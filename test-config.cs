using Microsoft.Extensions.Configuration;

var config = new ConfigurationBuilder()
    .AddJsonFile("src/PriceFeed.Console/appsettings.json")
    .Build();

var rpc = config.GetSection("BatchProcessing:RpcEndpoint").Value;
var hash = config.GetSection("BatchProcessing:ContractScriptHash").Value;
var tee = config.GetSection("BatchProcessing:TeeAccountAddress").Value;
var master = config.GetSection("BatchProcessing:MasterAccountAddress").Value;

Console.WriteLine($"RPC: {rpc}");
Console.WriteLine($"Hash: {hash}");
Console.WriteLine($"TEE: {tee}");
Console.WriteLine($"Master: {master}");