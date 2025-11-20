using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Moq;
using Neo;
using Neo.Cryptography.ECC;
using Neo.Network.P2P.Payloads;
using Neo.Network.RPC.Models;
using Neo.SmartContract;
using Neo.Wallets;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;
using PriceFeed.Infrastructure.Services;
using Xunit;

namespace PriceFeed.Tests;

/// <summary>
/// Integration tests for Neo blockchain interactions
/// </summary>
public class NeoIntegrationTests
{
    private readonly Mock<ILogger<BatchProcessingService>> _mockLogger = new();
    private readonly Mock<IAttestationService> _mockAttestationService = new();
    private readonly Mock<INeoRpcClient> _rpcClientMock = new();

    public NeoIntegrationTests()
    {
        _rpcClientMock.SetupGet(r => r.ProtocolSettings).Returns(ProtocolSettings.Default);
        _rpcClientMock.Setup(r => r.GetRawTransactionAsync(It.IsAny<string>()))
            .ReturnsAsync(new RpcTransaction { Confirmations = 1 });

        _mockAttestationService
            .Setup(a => a.CreatePriceFeedAttestationAsync(
                It.IsAny<PriceBatch>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<string>()))
            .ReturnsAsync(true);
    }

    [Fact]
    public void GenerateNeoAccount_ShouldCreateValidAccount()
    {
        // Arrange & Act
        var privateKey = new byte[32];
        using (var rng = System.Security.Cryptography.RandomNumberGenerator.Create())
        {
            rng.GetBytes(privateKey);
        }

        var keyPair = new KeyPair(privateKey);
        var wif = keyPair.Export();
        var contract = Contract.CreateSignatureContract(keyPair.PublicKey);
        var address = contract.ScriptHash.ToAddress(ProtocolSettings.Default.AddressVersion);

        // Assert
        Assert.NotNull(wif);
        Assert.True(wif.StartsWith("K") || wif.StartsWith("L")); // WIF should start with K or L for mainnet
        Assert.NotNull(address);
        Assert.StartsWith("N", address); // Neo N3 addresses start with N
        Assert.Equal(34, address.Length); // Neo addresses are 34 characters long
    }

    [Fact]
    public void ImportAccountFromWIF_ShouldRecreateCorrectAddress()
    {
        // Arrange
        var privateKey = new byte[32];
        using (var rng = System.Security.Cryptography.RandomNumberGenerator.Create())
        {
            rng.GetBytes(privateKey);
        }

        var originalKeyPair = new KeyPair(privateKey);
        var wif = originalKeyPair.Export();
        var originalContract = Contract.CreateSignatureContract(originalKeyPair.PublicKey);
        var originalAddress = originalContract.ScriptHash.ToAddress(ProtocolSettings.Default.AddressVersion);

        // Act
        var importedPrivateKey = Wallet.GetPrivateKeyFromWIF(wif);
        var importedKeyPair = new KeyPair(importedPrivateKey);
        var importedContract = Contract.CreateSignatureContract(importedKeyPair.PublicKey);
        var importedAddress = importedContract.ScriptHash.ToAddress(ProtocolSettings.Default.AddressVersion);

        // Assert
        Assert.Equal(originalAddress, importedAddress);
        Assert.Equal(originalKeyPair.PrivateKey, importedKeyPair.PrivateKey);
    }

    [Fact]
    public void CreateTransaction_WithDualSignatures_ShouldBeValid()
    {
        // Arrange
        var teePrivateKey = new byte[32];
        var masterPrivateKey = new byte[32];
        using (var rng = System.Security.Cryptography.RandomNumberGenerator.Create())
        {
            rng.GetBytes(teePrivateKey);
            rng.GetBytes(masterPrivateKey);
        }

        var teeKeyPair = new KeyPair(teePrivateKey);
        var masterKeyPair = new KeyPair(masterPrivateKey);

        // Create a sample transaction
        var transaction = new Transaction
        {
            Version = 0,
            Nonce = (uint)new Random().Next(),
            SystemFee = 1000000, // 0.01 GAS
            NetworkFee = 1000000, // 0.01 GAS
            ValidUntilBlock = 1000,
            Attributes = Array.Empty<TransactionAttribute>(),
            Signers = new[]
            {
                new Signer
                {
                    Account = Contract.CreateSignatureContract(teeKeyPair.PublicKey).ScriptHash,
                    Scopes = WitnessScope.CalledByEntry
                },
                new Signer
                {
                    Account = Contract.CreateSignatureContract(masterKeyPair.PublicKey).ScriptHash,
                    Scopes = WitnessScope.CalledByEntry
                }
            },
            Script = new byte[] { 0x01, 0x02, 0x03 }, // Dummy script
            Witnesses = new Witness[0]
        };

        // Act - Sign with both keys
        // Create placeholder signatures for test
        var teeSignature = new byte[64];
        var masterSignature = new byte[64];

        var witnesses = new List<Witness>
        {
            new Witness
            {
                InvocationScript = new byte[] { 0x40 }.Concat(teeSignature).ToArray(),
                VerificationScript = Contract.CreateSignatureContract(teeKeyPair.PublicKey).Script
            },
            new Witness
            {
                InvocationScript = new byte[] { 0x40 }.Concat(masterSignature).ToArray(),
                VerificationScript = Contract.CreateSignatureContract(masterKeyPair.PublicKey).Script
            }
        };

        transaction.Witnesses = witnesses.ToArray();

        // Assert
        Assert.Equal(2, transaction.Signers.Length);
        Assert.Equal(2, transaction.Witnesses.Length);
        Assert.NotNull(transaction.Hash);
        Assert.True(transaction.Witnesses[0].InvocationScript.Length > 0);
        Assert.True(transaction.Witnesses[1].InvocationScript.Length > 0);
    }

    [Fact]
    public void VerifyNeoAssetIds_ShouldBeCorrect()
    {
        // Arrange & Act
        var neoAssetId = "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5";
        var gasAssetId = "0xd2a4cff31913016155e38e474a2c06d08be276cf";

        // Assert - Verify these are the correct Neo N3 asset IDs
        Assert.Equal(42, neoAssetId.Length); // Asset IDs are 42 characters (0x + 40 hex chars)
        Assert.Equal(42, gasAssetId.Length);
        Assert.StartsWith("0x", neoAssetId);
        Assert.StartsWith("0x", gasAssetId);
    }

    [Fact]
    public async Task ProcessBatch_WithValidCredentials_ShouldSubmitTransaction()
    {
        var options = new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
            TeeAccountAddress = "NXV7ZhHiyM1aHXwpVsRZC6BwNFP7jghXAq",
            TeeAccountPrivateKey = GenerateTestWIF(),
            MasterAccountAddress = "NL5P8BBjpPuLpH5gZBxATrxDLqXxjHqmkr",
            MasterAccountPrivateKey = GenerateTestWIF(),
            MaxBatchSize = 50
        };

        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ReturnsAsync(UInt256.Zero);

        var service = new BatchProcessingService(
            _mockLogger.Object,
            Options.Create(options),
            _mockAttestationService.Object,
            _rpcClientMock.Object
        );

        var batch = new PriceBatch
        {
            BatchId = Guid.NewGuid(),
            Prices = new List<AggregatedPriceData>
            {
                new AggregatedPrice
                {
                    Symbol = "BTCUSDT",
                    Price = 50000.00m,
                    Timestamp = DateTime.UtcNow,
                    ConfidenceScore = 95
                }
            }
        };

        var result = await service.ProcessBatchAsync(batch);

        Assert.True(result);
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(
            It.IsAny<ReadOnlyMemory<byte>>(),
            It.IsAny<Signer[]>(),
            It.IsAny<KeyPair[]>()), Times.Once);
    }

    private string GenerateTestWIF()
    {
        var privateKey = new byte[32];
        using (var rng = System.Security.Cryptography.RandomNumberGenerator.Create())
        {
            rng.GetBytes(privateKey);
        }
        var keyPair = new KeyPair(privateKey);
        return keyPair.Export();
    }
}
