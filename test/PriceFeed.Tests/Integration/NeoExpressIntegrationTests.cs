using System;
using System.Threading.Tasks;
using Neo.Network.RPC;
using PriceFeed.Tests.TestUtilities;
using Xunit;

namespace PriceFeed.Tests.Integration;

/// <summary>
/// Minimal integration test that exercises a running Neo Express instance via RPC.
/// Requires RUN_NEO_EXPRESS_TESTS=true and a running Neo Express node (default http://localhost:20332).
/// </summary>
public class NeoExpressIntegrationTests
{
    private static readonly string RpcUrl = Environment.GetEnvironmentVariable("NEO_EXPRESS_RPC_ENDPOINT") ?? "http://localhost:20332";

    [CITestHelper.NeoExpressFact]
    public async Task GetBlockCount_FromNeoExpress_ShouldSucceed()
    {
        var rpc = new RpcClient(new Uri(RpcUrl));
        var count = await rpc.GetBlockCountAsync();
        Assert.True(count > 0, $"Expected block count > 0 from Neo Express at {RpcUrl}");
    }
}
