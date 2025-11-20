using System.Numerics;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Neo;
using Neo.Extensions;
using Neo.Network.P2P.Payloads;
using Neo.SmartContract;
using Neo.SmartContract.Native;
using Neo.VM;
using Neo.Wallets;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;

namespace PriceFeed.Infrastructure.Services;

/// <summary>
/// Service for processing and sending batches of price data to the smart contract.
/// Uses dual signatures (TEE + Master) and the Neo RPC client to build and broadcast real transactions.
/// </summary>
public class BatchProcessingService : IBatchProcessingService, IDisposable
{
    private readonly ILogger<BatchProcessingService> _logger;
    private readonly BatchProcessingOptions _options;
    private readonly IAttestationService _attestationService;
    private readonly INeoRpcClient _rpcClient;
    private readonly Dictionary<Guid, BatchStatus> _batchStatuses = new();
    private readonly Dictionary<Guid, string> _transactionHashes = new();
    private readonly KeyPair _teeKeyPair;
    private readonly KeyPair _masterKeyPair;
    private readonly UInt160 _teeAccount;
    private readonly UInt160 _masterAccount;
    private readonly UInt160 _contractHash;

    public BatchProcessingService(
        ILogger<BatchProcessingService> logger,
        IOptions<BatchProcessingOptions> options,
        IAttestationService attestationService,
        INeoRpcClient rpcClient)
    {
        _logger = logger;
        _attestationService = attestationService;
        _rpcClient = rpcClient;

        _options = options.Value;

        if (string.IsNullOrWhiteSpace(_options.RpcEndpoint))
        {
            throw new OptionsValidationException(nameof(BatchProcessingOptions), typeof(BatchProcessingOptions), new[] { "RpcEndpoint must be configured" });
        }

        if (string.IsNullOrWhiteSpace(_options.ContractScriptHash))
        {
            throw new OptionsValidationException(nameof(BatchProcessingOptions), typeof(BatchProcessingOptions), new[] { "ContractScriptHash must be configured" });
        }

        try
        {
            _contractHash = UInt160.Parse(_options.ContractScriptHash);
        }
        catch (FormatException)
        {
            throw new OptionsValidationException(nameof(BatchProcessingOptions), typeof(BatchProcessingOptions), new[] { $"ContractScriptHash is invalid: {_options.ContractScriptHash}" });
        }

        _teeKeyPair = CreateKeyPair(nameof(_options.TeeAccountPrivateKey), _options.TeeAccountPrivateKey);
        _masterKeyPair = CreateKeyPair(nameof(_options.MasterAccountPrivateKey), _options.MasterAccountPrivateKey);
        _teeAccount = Contract.CreateSignatureContract(_teeKeyPair.PublicKey).ScriptHash;
        _masterAccount = Contract.CreateSignatureContract(_masterKeyPair.PublicKey).ScriptHash;
    }

    private static KeyPair CreateKeyPair(string optionName, string wif)
    {
        try
        {
            return new KeyPair(Wallet.GetPrivateKeyFromWIF(wif));
        }
        catch (Exception)
        {
            throw new OptionsValidationException(nameof(BatchProcessingOptions), typeof(BatchProcessingOptions), new[] { $"{optionName} is invalid or missing" });
        }
    }

    public async Task<bool> ProcessBatchAsync(PriceBatch batch)
    {
        try
        {
            _logger.LogInformation("Processing batch {BatchId} with {Count} prices", batch.BatchId, batch.Prices.Count);

            if (batch.Prices.Count == 0)
            {
                _logger.LogError("Cannot process empty batch");
                throw new ArgumentException("Batch must contain at least one price entry", nameof(batch));
            }

            _batchStatuses[batch.BatchId] = BatchStatus.Processing;

            if (_options.CheckAndTransferTeeAssets)
            {
                await CheckAndTransferTeeAssetsAsync();
            }

            foreach (var subBatch in SplitBatch(batch))
            {
                var symbols = subBatch.Prices.Select(p => p.Symbol).ToArray();

                const decimal satoshiMultiplier = 100000000m;
                const long maxSafeValue = long.MaxValue / 100000000;

                var priceValues = subBatch.Prices.Select(p =>
                {
                    if (p.Price > maxSafeValue)
                    {
                        _logger.LogWarning("Price {Price} for {Symbol} exceeds safe scaling limit, capping at {MaxPrice}",
                            p.Price, p.Symbol, maxSafeValue);
                        return (long)(maxSafeValue * satoshiMultiplier);
                    }

                    try
                    {
                        checked
                        {
                            return (long)(p.Price * satoshiMultiplier);
                        }
                    }
                    catch (OverflowException)
                    {
                        _logger.LogError("Overflow when scaling price {Price} for {Symbol}, using safe maximum", p.Price, p.Symbol);
                        return (long)(maxSafeValue * satoshiMultiplier);
                    }
                }).ToArray();

                var timestamps = subBatch.Prices.Select(p => new BigInteger(((DateTimeOffset)p.Timestamp).ToUnixTimeSeconds())).ToArray();
                var confidenceScores = subBatch.Prices.Select(p => new BigInteger((long)p.ConfidenceScore)).ToArray();
                var prices = priceValues.Select(p => new BigInteger(p)).ToArray();

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

                var symbolParams = symbols.Select(s => new ContractParameter(ContractParameterType.String) { Value = s }).ToList();
                var priceParams = prices.Select(p => new ContractParameter(ContractParameterType.Integer) { Value = p }).ToList();
                var timestampParams = timestamps.Select(t => new ContractParameter(ContractParameterType.Integer) { Value = t }).ToList();
                var confidenceParams = confidenceScores.Select(c => new ContractParameter(ContractParameterType.Integer) { Value = c }).ToList();

                var arguments = new[]
                {
                    new ContractParameter(ContractParameterType.Array) { Value = symbolParams },
                    new ContractParameter(ContractParameterType.Array) { Value = priceParams },
                    new ContractParameter(ContractParameterType.Array) { Value = timestampParams },
                    new ContractParameter(ContractParameterType.Array) { Value = confidenceParams }
                };

                using var scriptBuilder = new ScriptBuilder();
                scriptBuilder.EmitDynamicCall(_contractHash, "updatePriceBatch", CallFlags.All, arguments);
                var script = scriptBuilder.ToArray();

                UInt256 txHash;
                try
                {
                    txHash = await _rpcClient.SubmitScriptAsync(script, signers, _teeKeyPair, _masterKeyPair);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Failed to submit batch {BatchId}", subBatch.BatchId);
                    _batchStatuses[batch.BatchId] = BatchStatus.Failed;
                    return false;
                }

                var txHashString = txHash.ToString();
                _transactionHashes[subBatch.BatchId] = txHashString;
                _logger.LogInformation("Transaction sent for batch {BatchId}: {TransactionHash}", subBatch.BatchId, txHashString);

                try
                {
                    var runId = Environment.GetEnvironmentVariable("GITHUB_RUN_ID") ?? "unknown";
                    var runNumber = Environment.GetEnvironmentVariable("GITHUB_RUN_NUMBER") ?? "unknown";
                    var repository = Environment.GetEnvironmentVariable("GITHUB_REPOSITORY") ?? "unknown";
                    var workflow = Environment.GetEnvironmentVariable("GITHUB_WORKFLOW") ?? "unknown";
                    var repoSplit = repository.Split('/');
                    var repoOwner = repoSplit.Length > 0 ? repoSplit[0] : "unknown";
                    var repoName = repoSplit.Length > 1 ? repoSplit[1] : "unknown";

                    await _attestationService.CreatePriceFeedAttestationAsync(
                        subBatch,
                        txHashString,
                        runId,
                        runNumber,
                        repoOwner,
                        repoName,
                        workflow);

                    _logger.LogInformation("Created attestation for batch {BatchId}", subBatch.BatchId);
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Failed to create attestation for batch {BatchId}", subBatch.BatchId);
                    throw new InvalidOperationException($"Failed to create attestation for batch {subBatch.BatchId}. Cannot proceed without attestation.", ex);
                }
            }

            _batchStatuses[batch.BatchId] = BatchStatus.Sent;
            _ = Task.Run(() => MonitorBatchConfirmationAsync(batch.BatchId));

            return true;
        }
        catch (ArgumentException)
        {
            throw;
        }
        catch (InvalidOperationException)
        {
            throw;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing batch {BatchId}", batch.BatchId);
            _batchStatuses[batch.BatchId] = BatchStatus.Failed;
            return false;
        }
    }

    public Task<BatchStatusInfo> GetBatchStatusAsync(Guid batchId)
    {
        var status = _batchStatuses.TryGetValue(batchId, out var batchStatus) ? batchStatus : BatchStatus.Unknown;
        var transactionHash = _transactionHashes.TryGetValue(batchId, out var hash) ? hash : null;

        var statusInfo = new BatchStatusInfo
        {
            BatchId = batchId,
            Status = status,
            TransactionHash = transactionHash,
            Timestamp = DateTime.UtcNow,
            ProcessedCount = status == BatchStatus.Confirmed ? 1 : 0,
            TotalCount = 1
        };

        return Task.FromResult(statusInfo);
    }

    private IEnumerable<PriceBatch> SplitBatch(PriceBatch batch)
    {
        if (batch.Prices.Count <= _options.MaxBatchSize)
        {
            return new[] { batch };
        }

        var result = new List<PriceBatch>();

        for (int i = 0; i < batch.Prices.Count; i += _options.MaxBatchSize)
        {
            var subBatch = new PriceBatch
            {
                BatchId = batch.BatchId,
                Timestamp = batch.Timestamp,
                Prices = batch.Prices.Skip(i).Take(_options.MaxBatchSize).ToList()
            };

            result.Add(subBatch);
        }

        return result;
    }

    private async Task MonitorBatchConfirmationAsync(Guid batchId)
    {
        try
        {
            if (!_transactionHashes.TryGetValue(batchId, out var txHashString))
            {
                _logger.LogWarning("No transaction hash found for batch {BatchId}", batchId);
                _batchStatuses[batchId] = BatchStatus.Failed;
                return;
            }

            const int maxAttempts = 30;
            const int delayMs = 2000;

            for (int attempt = 0; attempt < maxAttempts; attempt++)
            {
                try
                {
                    var transaction = await _rpcClient.GetRawTransactionAsync(txHashString);
                    if (transaction?.Confirmations > 0)
                    {
                        _batchStatuses[batchId] = BatchStatus.Confirmed;
                        _logger.LogInformation("Batch {BatchId} confirmed with {Confirmations} confirmations", batchId, transaction.Confirmations);
                        return;
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Error checking transaction status for batch {BatchId} (Attempt {Attempt}/{MaxAttempts})", batchId, attempt + 1, maxAttempts);
                }

                await Task.Delay(delayMs);
            }

            _logger.LogWarning("Transaction for batch {BatchId} not confirmed after {MaxAttempts} attempts", batchId, maxAttempts);
            _batchStatuses[batchId] = BatchStatus.Pending;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error monitoring batch {BatchId}", batchId);
            _batchStatuses[batchId] = BatchStatus.Failed;
        }
    }

    private async Task<bool> CheckAndTransferTeeAssetsAsync()
    {
        try
        {
            var balances = await _rpcClient.GetNep17BalancesAsync(_teeAccount);
            if (balances?.Balances == null || balances.Balances.Count == 0)
            {
                _logger.LogInformation("TEE account has no assets to transfer");
                return false;
            }

            var teeAddress = _teeAccount.ToAddress(_rpcClient.ProtocolSettings.AddressVersion);
            _logger.LogInformation("Checking for assets in TEE account {TeeAccountAddress}", teeAddress);

            bool transferred = false;

            foreach (var balance in balances.Balances)
            {
                var amount = balance.Amount;
                if (amount <= 0)
                {
                    continue;
                }

                var assetHash = balance.AssetHash;

                if (assetHash == NativeContract.GAS.Hash && amount < 1_00000000)
                {
                    _logger.LogInformation("Skipping GAS transfer to leave fees in TEE account (balance: {Balance})", balance.Amount);
                    continue;
                }

                using var scriptBuilder = new ScriptBuilder();
                scriptBuilder.EmitDynamicCall(assetHash, "transfer", CallFlags.All, _teeAccount, _masterAccount, amount, "TEE to Master transfer");
                var script = scriptBuilder.ToArray();

                var signers = new[]
                {
                    new Signer
                    {
                        Account = _teeAccount,
                        Scopes = WitnessScope.CalledByEntry,
                        AllowedContracts = new[] { assetHash }
                    }
                };

                try
                {
                    var txHash = await _rpcClient.SubmitScriptAsync(script, signers, _teeKeyPair);
                    var assetLabel = assetHash == NativeContract.GAS.Hash ? "GAS" : assetHash == NativeContract.NEO.Hash ? "NEO" : assetHash.ToString();
                    _logger.LogInformation("Transferred {Amount} of {Asset} from TEE to Master account: {TxHash}", balance.Amount, assetLabel, txHash);
                    transferred = true;
                }
                catch (Exception ex)
                {
                    var assetLabel = assetHash == NativeContract.GAS.Hash ? "GAS" : assetHash == NativeContract.NEO.Hash ? "NEO" : assetHash.ToString();
                    _logger.LogWarning(ex, "Failed to transfer {Asset} from TEE to Master account", assetLabel);
                }
            }

            return transferred;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking and transferring assets from TEE account");
            return false;
        }
    }

    public void Dispose()
    {
        _rpcClient.Dispose();
        GC.SuppressFinalize(this);
    }
}
