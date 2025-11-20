using System.Collections.Immutable;
using System.Linq;
using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Neo;
using Neo.Network.P2P.Payloads;
using Neo.Network.RPC;
using Neo.Network.RPC.Models;
using Neo.Wallets;
using PriceFeed.Core.Options;

namespace PriceFeed.Infrastructure.Services;

public interface INeoRpcClient : IDisposable
{
    ProtocolSettings ProtocolSettings { get; }

    Task<UInt256> SubmitScriptAsync(ReadOnlyMemory<byte> script, Signer[] signers, params KeyPair[] signingKeys);

    Task<RpcTransaction?> GetRawTransactionAsync(string hash);

    Task<RpcNep17Balances?> GetNep17BalancesAsync(UInt160 account);
}

/// <summary>
/// Thin wrapper over the Neo RpcClient that handles protocol discovery,
/// transaction construction, signing, and submission.
/// </summary>
public class NeoRpcClient : INeoRpcClient
{
    private readonly ILogger<NeoRpcClient> _logger;
    private readonly IHttpClientFactory _httpClientFactory;
    private readonly BatchProcessingOptions _options;
    private readonly SemaphoreSlim _initializationLock = new(1, 1);
    private RpcClient? _rpcClient;

    public NeoRpcClient(
        ILogger<NeoRpcClient> logger,
        IHttpClientFactory httpClientFactory,
        IOptions<BatchProcessingOptions> options)
    {
        _logger = logger;
        _httpClientFactory = httpClientFactory;
        _options = options.Value;
    }

    public ProtocolSettings ProtocolSettings { get; private set; } = ProtocolSettings.Default;

    public async Task<UInt256> SubmitScriptAsync(ReadOnlyMemory<byte> script, Signer[] signers, params KeyPair[] signingKeys)
    {
        await EnsureInitializedAsync();

        try
        {
            var factory = new TransactionManagerFactory(_rpcClient!);
            var txManager = await factory.MakeTransactionAsync(script, signers, Array.Empty<TransactionAttribute>());

            foreach (var key in signingKeys)
            {
                txManager.AddSignature(key);
            }

            var tx = await txManager.SignAsync();
            var hash = await _rpcClient!.SendRawTransactionAsync(tx);
            _logger.LogInformation("Submitted transaction {TransactionHash}", hash);
            return hash;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to submit transaction to Neo RPC endpoint");
            throw;
        }
    }

    public async Task<RpcTransaction?> GetRawTransactionAsync(string hash)
    {
        await EnsureInitializedAsync();
        return await _rpcClient!.GetRawTransactionAsync(hash);
    }

    public async Task<RpcNep17Balances?> GetNep17BalancesAsync(UInt160 account)
    {
        await EnsureInitializedAsync();
        var address = account.ToAddress(ProtocolSettings.AddressVersion);
        return await _rpcClient!.GetNep17BalancesAsync(address);
    }

    public void Dispose()
    {
        _rpcClient?.Dispose();
        _initializationLock.Dispose();
        GC.SuppressFinalize(this);
    }

    private async Task EnsureInitializedAsync()
    {
        if (_rpcClient != null)
        {
            return;
        }

        await _initializationLock.WaitAsync();
        try
        {
            if (_rpcClient != null)
            {
                return;
            }

            var httpClient = _httpClientFactory.CreateClient("Neo");
            var bootstrapClient = new RpcClient(httpClient, new Uri(_options.RpcEndpoint), ProtocolSettings.Default);
            var version = await bootstrapClient.GetVersionAsync();

            ProtocolSettings = BuildProtocolSettings(version);
            _rpcClient = new RpcClient(httpClient, new Uri(_options.RpcEndpoint), ProtocolSettings);

            _logger.LogInformation("Initialized Neo RPC client for {Endpoint} with network {Network}", _options.RpcEndpoint, ProtocolSettings.Network);
        }
        finally
        {
            _initializationLock.Release();
        }
    }

    private static ProtocolSettings BuildProtocolSettings(RpcVersion version)
    {
        var settings = new ProtocolSettings
        {
            Network = version.Protocol.Network,
            AddressVersion = version.Protocol.AddressVersion,
            MillisecondsPerBlock = version.Protocol.MillisecondsPerBlock,
            MaxValidUntilBlockIncrement = version.Protocol.MaxValidUntilBlockIncrement,
            MaxTraceableBlocks = version.Protocol.MaxTraceableBlocks,
            MaxTransactionsPerBlock = version.Protocol.MaxTransactionsPerBlock,
            MemoryPoolMaxTransactions = version.Protocol.MemoryPoolMaxTransactions,
            InitialGasDistribution = version.Protocol.InitialGasDistribution,
            ValidatorsCount = version.Protocol.ValidatorsCount,
            SeedList = version.Protocol.SeedList.ToArray(),
            StandbyCommittee = version.Protocol.StandbyCommittee.ToArray(),
            Hardforks = version.Protocol.Hardforks.ToImmutableDictionary()
        };

        ProtocolSettings.Custom = settings;
        return settings;
    }
}
