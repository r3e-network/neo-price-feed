using System;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Moq;
using Neo;
using Neo.Network.P2P.Payloads;
using Neo.Network.RPC.Models;
using Neo.SmartContract;
using Neo.SmartContract.Native;
using Neo.Wallets;
using PriceFeed.Core.Interfaces;
using PriceFeed.Core.Models;
using PriceFeed.Core.Options;
using PriceFeed.Infrastructure.Services;
using Xunit;

namespace PriceFeed.Tests;

    public class BatchProcessingServiceTests
    {
        private readonly Mock<ILogger<BatchProcessingService>> _loggerMock = new();
        private readonly Mock<IOptions<BatchProcessingOptions>> _optionsMock = new();
        private readonly Mock<IAttestationService> _attestationServiceMock = new();
        private readonly Mock<INeoRpcClient> _rpcClientMock = new();
    private readonly string _teeWif;
    private readonly string _masterWif;
    private readonly string _teeAddress;
    private readonly string _masterAddress;

    public BatchProcessingServiceTests()
    {
        var teeKey = CreateKeyPair();
        var masterKey = CreateKeyPair();

        _teeWif = teeKey.Export();
        _masterWif = masterKey.Export();
        _teeAddress = Contract.CreateSignatureContract(teeKey.PublicKey).ScriptHash.ToAddress(ProtocolSettings.Default.AddressVersion);
        _masterAddress = Contract.CreateSignatureContract(masterKey.PublicKey).ScriptHash.ToAddress(ProtocolSettings.Default.AddressVersion);

        _optionsMock.Setup(o => o.Value).Returns(new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
            TeeAccountAddress = _teeAddress,
            TeeAccountPrivateKey = _teeWif,
            MasterAccountAddress = _masterAddress,
            MasterAccountPrivateKey = _masterWif,
            MaxBatchSize = 50,
            CheckAndTransferTeeAssets = false
        });

        _rpcClientMock.SetupGet(r => r.ProtocolSettings).Returns(ProtocolSettings.Default);
        _rpcClientMock.Setup(r => r.GetRawTransactionAsync(It.IsAny<string>()))
            .ReturnsAsync(new RpcTransaction { Confirmations = 1 });

        _attestationServiceMock
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
    public async Task ProcessBatchAsync_WithValidBatch_ShouldReturnTrue()
    {
        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ReturnsAsync(UInt256.Zero);

        var service = CreateService();
        var batch = CreateBatch(1);

        var result = await service.ProcessBatchAsync(batch);

        Assert.True(result);
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(It.IsAny<ReadOnlyMemory<byte>>(), It.IsAny<Signer[]>(), It.IsAny<KeyPair[]>()), Times.Once);
        _attestationServiceMock.Verify(a => a.CreatePriceFeedAttestationAsync(
            It.IsAny<PriceBatch>(),
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<string>(),
            It.IsAny<string>()), Times.Once);
    }

    [Fact]
    public async Task ProcessBatchAsync_WithLargeBatch_ShouldSplitIntoSubBatches()
    {
        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ReturnsAsync(UInt256.Zero);

        var service = CreateService();
        var batch = CreateBatch(100);

        var result = await service.ProcessBatchAsync(batch);

        Assert.True(result);
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(
            It.IsAny<ReadOnlyMemory<byte>>(),
            It.IsAny<Signer[]>(),
            It.IsAny<KeyPair[]>()), Times.Exactly(2));
    }

    [Fact]
    public async Task ProcessBatchAsync_WhenSubmissionFails_ShouldReturnFalse()
    {
        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ThrowsAsync(new InvalidOperationException("rpc failure"));

        var service = CreateService();
        var batch = CreateBatch(1);

        var result = await service.ProcessBatchAsync(batch);

        Assert.False(result);
    }

    [Fact]
    public async Task ProcessBatchAsync_WithEmptyBatch_ShouldThrowException()
    {
        var service = CreateService();
        var batch = new PriceBatch { Prices = new List<AggregatedPriceData>() };

        await Assert.ThrowsAsync<ArgumentException>(() => service.ProcessBatchAsync(batch));
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(
            It.IsAny<ReadOnlyMemory<byte>>(),
            It.IsAny<Signer[]>(),
            It.IsAny<KeyPair[]>()), Times.Never);
    }

    [Fact]
    public async Task ProcessBatchAsync_WithAssetSweep_ShouldTransferFirst()
    {
        _optionsMock.Setup(o => o.Value).Returns(new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
            TeeAccountAddress = _teeAddress,
            TeeAccountPrivateKey = _teeWif,
            MasterAccountAddress = _masterAddress,
            MasterAccountPrivateKey = _masterWif,
            MaxBatchSize = 50,
            CheckAndTransferTeeAssets = true
        });

        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ReturnsAsync(UInt256.Zero);

        _rpcClientMock.Setup(r => r.GetNep17BalancesAsync(It.IsAny<UInt160>()))
            .ReturnsAsync(new RpcNep17Balances
            {
                UserScriptHash = UInt160.Zero,
                Balances = new List<RpcNep17Balance>
                {
                    new RpcNep17Balance
                    {
                        AssetHash = NativeContract.GAS.Hash,
                        Amount = new System.Numerics.BigInteger(2_00000000),
                        LastUpdatedBlock = 0
                    }
                }
            });

        var service = CreateService();
        var batch = CreateBatch(1);

        var result = await service.ProcessBatchAsync(batch);

        Assert.True(result);
        _rpcClientMock.Verify(r => r.GetNep17BalancesAsync(It.IsAny<UInt160>()), Times.Once);
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(
            It.IsAny<ReadOnlyMemory<byte>>(),
            It.IsAny<Signer[]>(),
            It.IsAny<KeyPair[]>()), Times.AtLeast(2));
    }

    [Fact]
    public void Constructor_WithInvalidContractHash_ShouldThrow()
    {
        _optionsMock.Setup(o => o.Value).Returns(new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "notahash",
            TeeAccountAddress = _teeAddress,
            TeeAccountPrivateKey = _teeWif,
            MasterAccountAddress = _masterAddress,
            MasterAccountPrivateKey = _masterWif
        });

        Assert.Throws<OptionsValidationException>(() => CreateService());
    }

    [Fact]
    public void Constructor_WithInvalidKey_ShouldThrow()
    {
        _optionsMock.Setup(o => o.Value).Returns(new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
            TeeAccountAddress = _teeAddress,
            TeeAccountPrivateKey = "invalid",
            MasterAccountAddress = _masterAddress,
            MasterAccountPrivateKey = _masterWif
        });

        Assert.Throws<OptionsValidationException>(() => CreateService());
    }

    [Fact]
    public async Task ProcessBatchAsync_WithSmallGasBalance_ShouldSkipSweep()
    {
        _optionsMock.Setup(o => o.Value).Returns(new BatchProcessingOptions
        {
            RpcEndpoint = "http://localhost:10332",
            ContractScriptHash = "0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc",
            TeeAccountAddress = _teeAddress,
            TeeAccountPrivateKey = _teeWif,
            MasterAccountAddress = _masterAddress,
            MasterAccountPrivateKey = _masterWif,
            MaxBatchSize = 50,
            CheckAndTransferTeeAssets = true
        });

        _rpcClientMock.Setup(r => r.SubmitScriptAsync(
                It.IsAny<ReadOnlyMemory<byte>>(),
                It.IsAny<Signer[]>(),
                It.IsAny<KeyPair[]>()))
            .ReturnsAsync(UInt256.Zero);

        _rpcClientMock.Setup(r => r.GetNep17BalancesAsync(It.IsAny<UInt160>()))
            .ReturnsAsync(new RpcNep17Balances
            {
                UserScriptHash = UInt160.Zero,
                Balances = new List<RpcNep17Balance>
                {
                    new RpcNep17Balance
                    {
                        AssetHash = NativeContract.GAS.Hash,
                        Amount = new System.Numerics.BigInteger(50000000), // 0.5 GAS
                        LastUpdatedBlock = 0
                    }
                }
            });

        var service = CreateService();
        var batch = CreateBatch(1);

        var result = await service.ProcessBatchAsync(batch);

        Assert.True(result);
        // Only the batch submission should happen; sweep skipped for small GAS
        _rpcClientMock.Verify(r => r.SubmitScriptAsync(
            It.IsAny<ReadOnlyMemory<byte>>(),
            It.IsAny<Signer[]>(),
            It.IsAny<KeyPair[]>()), Times.Once);
    }

    private BatchProcessingService CreateService() =>
        new(_loggerMock.Object, _optionsMock.Object, _attestationServiceMock.Object, _rpcClientMock.Object);

    private static KeyPair CreateKeyPair()
    {
        var privateKey = new byte[32];
        RandomNumberGenerator.Fill(privateKey);
        return new KeyPair(privateKey);
    }

    private static PriceBatch CreateBatch(int itemCount)
    {
        var prices = new List<AggregatedPriceData>();
        for (int i = 0; i < itemCount; i++)
        {
            prices.Add(new AggregatedPrice
            {
                Symbol = $"SYMBOL{i}",
                Price = 1000 + i,
                Timestamp = DateTime.UtcNow,
                ConfidenceScore = 90
            });
        }

        return new PriceBatch
        {
            BatchId = Guid.NewGuid(),
            Prices = prices
        };
    }
}
