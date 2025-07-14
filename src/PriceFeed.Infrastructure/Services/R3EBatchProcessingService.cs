using System;
using System.Collections.Generic;
using System.Linq;
using System.Numerics;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Neo;
using Neo.Network.P2P.Payloads;
using Neo.Network.RPC;
using Neo.SmartContract;
using Neo.SmartContract.Native;
using Neo.Wallets;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;

namespace PriceFeed.Infrastructure.Services
{
    /// <summary>
    /// Batch processing service for R3E-optimized smart contract
    /// Implements dual-signature transaction system for TEE authentication
    /// </summary>
    public class R3EBatchProcessingService : IBatchProcessingService
    {
        private readonly ILogger<R3EBatchProcessingService> _logger;
        private readonly BatchProcessingOptions _options;
        private readonly IAttestationService _attestationService;
        private readonly RpcClient _rpcClient;
        private readonly KeyPair _teeKeyPair;
        private readonly KeyPair _masterKeyPair;
        private readonly UInt160 _contractHash;
        private readonly UInt160 _teeAccount;
        private readonly UInt160 _masterAccount;

        public R3EBatchProcessingService(
            ILogger<R3EBatchProcessingService> logger,
            IOptions<BatchProcessingOptions> options,
            IAttestationService attestationService)
        {
            _logger = logger;
            _options = options.Value;
            _attestationService = attestationService;

            // Initialize RPC client
            _rpcClient = new RpcClient(new Uri(_options.RpcEndpoint));

            // Parse contract hash
            _contractHash = UInt160.Parse(_options.ContractScriptHash);

            // Initialize TEE account
            if (!string.IsNullOrEmpty(_options.TeeAccountPrivateKey))
            {
                var teePrivateKey = Wallet.GetPrivateKeyFromWIF(_options.TeeAccountPrivateKey);
                _teeKeyPair = new KeyPair(teePrivateKey);
                var teeContract = Contract.CreateSignatureContract(_teeKeyPair.PublicKey);
                _teeAccount = teeContract.ScriptHash;
            }
            else
            {
                throw new InvalidOperationException("TEE account private key is required");
            }

            // Initialize Master account
            if (!string.IsNullOrEmpty(_options.MasterAccountPrivateKey))
            {
                var masterPrivateKey = Wallet.GetPrivateKeyFromWIF(_options.MasterAccountPrivateKey);
                _masterKeyPair = new KeyPair(masterPrivateKey);
                var masterContract = Contract.CreateSignatureContract(_masterKeyPair.PublicKey);
                _masterAccount = masterContract.ScriptHash;
            }
            else
            {
                throw new InvalidOperationException("Master account private key is required");
            }

            _logger.LogInformation("R3E Batch Processing Service initialized");
            _logger.LogInformation("Contract: {ContractHash}", _contractHash);
            _logger.LogInformation("TEE Account: {TeeAccount}", _teeAccount.ToAddress(ProtocolSettings.Default.AddressVersion));
            _logger.LogInformation("Master Account: {MasterAccount}", _masterAccount.ToAddress(ProtocolSettings.Default.AddressVersion));
        }

        public async Task<bool> ProcessBatchAsync(PriceBatch batch)
        {
            try
            {
                _logger.LogInformation("Processing batch {BatchId} with {Count} prices using R3E contract",
                    batch.BatchId, batch.Prices.Count);

                // Validate batch
                if (batch.Prices.Count == 0 || batch.Prices.Count > _options.MaxBatchSize)
                {
                    _logger.LogWarning("Invalid batch size: {Count}. Must be between 1 and {MaxSize}",
                        batch.Prices.Count, _options.MaxBatchSize);
                    return false;
                }

                // Check and transfer any assets from TEE to Master account if enabled
                if (_options.CheckAndTransferTeeAssets)
                {
                    await CheckAndTransferTeeAssetsAsync();
                }

                // Convert prices to R3E contract format
                var priceUpdates = batch.Prices.Select(p => new ContractParameterBuilder()
                    .Push(p.Symbol)                    // string Symbol
                    .Push(ConvertToContractPrice(p.Price)) // BigInteger Price
                    .Push(p.Timestamp)                 // BigInteger Timestamp  
                    .Push((int)(p.ConfidenceScore * 100)) // BigInteger Confidence (0-100)
                    .ToArray())
                    .ToArray();

                // Build the script for batch update
                using var scriptBuilder = new ScriptBuilder();
                
                // Push the array of price updates
                scriptBuilder.EmitPush(priceUpdates.Length);
                for (int i = priceUpdates.Length - 1; i >= 0; i--)
                {
                    foreach (var param in priceUpdates[i].Reverse())
                    {
                        scriptBuilder.EmitPush(param);
                    }
                }
                scriptBuilder.Emit(OpCode.PACK);
                
                // Push contract hash and method
                scriptBuilder.EmitDynamicCall(_contractHash, "updatePriceBatch", CallFlags.All);

                var script = scriptBuilder.ToArray();

                // Create signers with dual-signature requirement
                var signers = new[]
                {
                    new Signer
                    {
                        Account = _teeAccount,
                        Scopes = WitnessScope.CalledByEntry,
                        AllowedContracts = new[] { _contractHash }
                    },
                    new Signer
                    {
                        Account = _masterAccount,
                        Scopes = WitnessScope.CalledByEntry,
                        AllowedContracts = new[] { _contractHash }
                    }
                };

                // Create transaction
                var tx = await _rpcClient.CreateTransactionAsync(script, signers);

                // Sign with both accounts
                var witnesses = new List<Witness>();

                // TEE account witness
                var teeContract = Contract.CreateSignatureContract(_teeKeyPair.PublicKey);
                var teeSignature = tx.Sign(_teeKeyPair, ProtocolSettings.Default.Network);
                witnesses.Add(new Witness
                {
                    InvocationScript = new ScriptBuilder().EmitPush(teeSignature).ToArray(),
                    VerificationScript = teeContract.Script
                });

                // Master account witness
                var masterContract = Contract.CreateSignatureContract(_masterKeyPair.PublicKey);
                var masterSignature = tx.Sign(_masterKeyPair, ProtocolSettings.Default.Network);
                witnesses.Add(new Witness
                {
                    InvocationScript = new ScriptBuilder().EmitPush(masterSignature).ToArray(),
                    VerificationScript = masterContract.Script
                });

                tx.Witnesses = witnesses.ToArray();

                // Send transaction
                _logger.LogInformation("Sending transaction with dual signatures...");
                var txHash = await _rpcClient.SendRawTransactionAsync(tx);
                _logger.LogInformation("Transaction sent: {TxHash}", txHash);

                // Create attestation
                await _attestationService.CreateAttestationAsync(batch, txHash.ToString());

                // Wait for confirmation
                await WaitForTransactionConfirmationAsync(txHash.ToString());

                _logger.LogInformation("Batch {BatchId} processed successfully with R3E contract", batch.BatchId);
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing batch {BatchId} with R3E contract", batch.BatchId);
                return false;
            }
        }

        private async Task CheckAndTransferTeeAssetsAsync()
        {
            try
            {
                // Get NEP-17 balances for TEE account
                var balances = await _rpcClient.GetNep17BalancesAsync(_teeAccount.ToAddress(ProtocolSettings.Default.AddressVersion));
                
                if (balances?.Balances == null || !balances.Balances.Any())
                {
                    return;
                }

                foreach (var balance in balances.Balances)
                {
                    var amount = BigInteger.Parse(balance.Amount);
                    if (amount <= 0) continue;

                    var assetHash = UInt160.Parse(balance.AssetHash);
                    
                    // Skip GAS transfers if balance is minimal (keep some for fees)
                    if (assetHash == NativeContract.GAS.Hash && amount < 1_00000000) // Keep at least 1 GAS
                    {
                        continue;
                    }

                    _logger.LogInformation("Transferring {Amount} of {Asset} from TEE to Master account",
                        amount, balance.Symbol ?? balance.AssetHash);

                    try
                    {
                        // Create transfer script
                        using var scriptBuilder = new ScriptBuilder();
                        scriptBuilder.EmitDynamicCall(assetHash, "transfer", 
                            _teeAccount, 
                            _masterAccount, 
                            amount, 
                            "TEE to Master transfer");

                        var script = scriptBuilder.ToArray();

                        // Create transaction with TEE account as signer
                        var signer = new Signer
                        {
                            Account = _teeAccount,
                            Scopes = WitnessScope.CalledByEntry
                        };

                        var tx = await _rpcClient.CreateTransactionAsync(script, signer);

                        // Sign with TEE account
                        var teeContract = Contract.CreateSignatureContract(_teeKeyPair.PublicKey);
                        var signature = tx.Sign(_teeKeyPair, ProtocolSettings.Default.Network);
                        
                        tx.Witnesses = new[]
                        {
                            new Witness
                            {
                                InvocationScript = new ScriptBuilder().EmitPush(signature).ToArray(),
                                VerificationScript = teeContract.Script
                            }
                        };

                        // Send transaction
                        var txHash = await _rpcClient.SendRawTransactionAsync(tx);
                        _logger.LogInformation("Asset transfer transaction sent: {TxHash}", txHash);
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "Failed to transfer {Asset} from TEE to Master account", 
                            balance.Symbol ?? balance.AssetHash);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error checking TEE account assets");
            }
        }

        private async Task WaitForTransactionConfirmationAsync(string txHash)
        {
            const int maxAttempts = 10;
            const int delayMs = 3000;

            for (int i = 0; i < maxAttempts; i++)
            {
                try
                {
                    var tx = await _rpcClient.GetRawTransactionAsync(txHash);
                    if (tx?.Confirmations > 0)
                    {
                        _logger.LogInformation("Transaction {TxHash} confirmed with {Confirmations} confirmations",
                            txHash, tx.Confirmations);
                        return;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogDebug(ex, "Transaction not yet confirmed, attempt {Attempt}/{MaxAttempts}",
                        i + 1, maxAttempts);
                }

                await Task.Delay(delayMs);
            }

            _logger.LogWarning("Transaction {TxHash} confirmation timeout after {MaxAttempts} attempts",
                txHash, maxAttempts);
        }

        private BigInteger ConvertToContractPrice(decimal price)
        {
            // Convert decimal price to BigInteger with 8 decimal places
            return new BigInteger(price * 100_000_000);
        }
    }
}