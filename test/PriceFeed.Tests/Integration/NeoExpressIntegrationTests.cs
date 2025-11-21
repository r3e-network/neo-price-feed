using System;
using System.Net.Http;
using System.Numerics;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using Neo.Network.RPC;
using PriceFeed.Tests.TestUtilities;
using Xunit;

namespace PriceFeed.Tests.Integration;

/// <summary>
/// Minimal integration test that exercises a running Neo Express instance via RPC.
/// Requires RUN_NEO_EXPRESS_TESTS=true and a running Neo Express node
/// (default http://localhost:50012 when using `neoxp create`).
/// </summary>
public class NeoExpressIntegrationTests
{
    private static readonly string RpcUrl = Environment.GetEnvironmentVariable("NEO_EXPRESS_RPC_ENDPOINT") ?? "http://localhost:50012";
    private static readonly string ContractHash = Environment.GetEnvironmentVariable("NEO_EXPRESS_CONTRACT_HASH") ?? string.Empty;
    private static readonly string TestSymbol = Environment.GetEnvironmentVariable("NEO_EXPRESS_TEST_SYMBOL") ?? "BTCUSDT";
    private static readonly BigInteger SeedPrice = BigInteger.Parse(Environment.GetEnvironmentVariable("NEO_EXPRESS_TEST_PRICE") ?? "0");
    private static readonly bool PriceSeeded = bool.TryParse(Environment.GetEnvironmentVariable("NEO_EXPRESS_PRICE_SEEDED"), out var seeded) && seeded;

    [CITestHelper.NeoExpressFact]
    public async Task GetBlockCount_FromNeoExpress_ShouldSucceed()
    {
        var rpc = new RpcClient(new Uri(RpcUrl));
        var count = await rpc.GetBlockCountAsync();
        Assert.True(count > 0, $"Expected block count > 0 from Neo Express at {RpcUrl}");
    }

    [CITestHelper.NeoExpressFact]
    public async Task GetPrice_FromDeployedContract_ShouldMatchSeed()
    {
        if (string.IsNullOrWhiteSpace(ContractHash) || SeedPrice <= 0 || !PriceSeeded)
            return;

        using var client = new HttpClient();
        var payload = new
        {
            jsonrpc = "2.0",
            method = "invokefunction",
            @params = new object[]
            {
                ContractHash,
                "getPrice",
                new object[]
                {
                    new { type = "String", value = TestSymbol }
                }
            },
            id = 1
        };

        var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var response = await client.PostAsync(RpcUrl, content);
        response.EnsureSuccessStatusCode();

        using var doc = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var result = doc.RootElement.GetProperty("result");
        var state = result.GetProperty("state").GetString();
        Assert.Equal("HALT", state);

        var stack = result.GetProperty("stack");
        Assert.True(stack.GetArrayLength() > 0, "Expected stack output from getPrice");

        var priceValue = stack[0].GetProperty("value").GetString();
        Assert.False(string.IsNullOrWhiteSpace(priceValue), "Price value missing");

        var onChainPrice = BigInteger.Parse(priceValue);
        Assert.Equal(SeedPrice, onChainPrice);
    }
}
