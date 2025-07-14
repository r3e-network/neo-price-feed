using System;
using System.IO;
using System.Numerics;
using System.Threading.Tasks;
using Neo;
using Neo.IO;
using Neo.Network.P2P.Payloads;
using Neo.Network.RPC;
using Neo.SmartContract;
using Neo.SmartContract.Manifest;
using Neo.SmartContract.Native;
using Neo.VM;
using Neo.Wallets;
using Neo.Wallets.NEP6;

namespace PriceFeed.ContractDeployer
{
    class Program
    {
        static async Task Main(string[] args)
        {
            try
            {
                Console.WriteLine("🚀 Neo N3 Smart Contract Deployer");
                Console.WriteLine("==================================");

                // Configuration
                const string rpcEndpoint = "http://seed1t5.neo.org:20332";
                const string masterWif = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb";
                const string contractPath = "../../PriceFeed.Contracts/PriceFeed.Oracle.nef";
                const string manifestPath = "../../PriceFeed.Contracts/PriceFeed.Oracle.manifest.json";

                // Create account from WIF
                var privateKey = Neo.Wallets.Wallet.GetPrivateKeyFromWIF(masterWif);
                var keyPair = new Neo.Wallets.KeyPair(privateKey);
                var contract = Neo.SmartContract.Contract.CreateSignatureContract(keyPair.PublicKey);
                var address = contract.ScriptHash.ToAddress(Neo.ProtocolSettings.Default.AddressVersion);
                Console.WriteLine($"📍 Deploying with Master Account: {address}");

                // Check contract files
                if (!File.Exists(contractPath))
                {
                    throw new FileNotFoundException($"Contract file not found: {contractPath}");
                }
                if (!File.Exists(manifestPath))
                {
                    throw new FileNotFoundException($"Manifest file not found: {manifestPath}");
                }

                // Read contract files
                var nefFile = File.ReadAllBytes(contractPath);
                var nef = NefFile.Parse(nefFile, true);
                var manifestContent = File.ReadAllText(manifestPath);
                var manifest = ContractManifest.Parse(manifestContent);

                Console.WriteLine("📄 Contract files loaded successfully");
                Console.WriteLine($"   NEF Checksum: {nef.CheckSum}");
                Console.WriteLine($"   Compiler: {nef.Compiler}");
                Console.WriteLine($"   Contract Name: {manifest.Name}");

                // Create RPC client
                var rpcClient = new RpcClient(new Uri(rpcEndpoint));
                Console.WriteLine($"🌐 Connected to TestNet: {rpcEndpoint}");

                // Get account balance
                var nep17Balances = await rpcClient.GetNep17BalancesAsync(address);
                var neoBalance = BigInteger.Zero;
                var gasBalance = BigInteger.Zero;
                
                if (nep17Balances?.Balances != null)
                {
                    foreach (var balance in nep17Balances.Balances)
                    {
                        if (balance.AssetHash == NativeContract.NEO.Hash.ToString())
                            neoBalance = BigInteger.Parse(balance.Amount);
                        else if (balance.AssetHash == NativeContract.GAS.Hash.ToString())
                            gasBalance = BigInteger.Parse(balance.Amount);
                    }
                }
                
                Console.WriteLine($"💰 Account Balances:");
                Console.WriteLine($"   NEO: {neoBalance / BigInteger.Pow(10, 0)}");
                Console.WriteLine($"   GAS: {gasBalance / BigInteger.Pow(10, 8)}");

                if (gasBalance < new BigInteger(10_00000000)) // 10 GAS minimum
                {
                    throw new InvalidOperationException("Insufficient GAS balance. Need at least 10 GAS for deployment.");
                }

                // Deploy contract
                Console.WriteLine("\n📤 Deploying contract to TestNet...");

                // Get the contract hash (before deployment)
                var contractHash = Neo.SmartContract.Helper.GetContractHash(contract.ScriptHash, nef.Script, manifest.ToJson().ToString());
                Console.WriteLine($"🎯 Expected Contract Hash: 0x{contractHash}");

                // Create deployment script
                using var sb = new ScriptBuilder();
                sb.EmitPush(manifest.ToJson().ToString());
                // NefFile doesn't have ToArray() in newer versions, use Script property
                sb.EmitPush(nef.Script);
                sb.EmitPush(2); // CallFlags.All
                sb.EmitSysCall(Neo.SmartContract.ApplicationEngine.System_Contract_Create);

                var script = sb.ToArray();

                // Create and sign transaction
                var signers = new[] { new Signer { Scopes = WitnessScope.CalledByEntry, Account = contract.ScriptHash } };
                var tx = await rpcClient.CreateTransactionAsync(script, signers);
                
                // Create witness
                var witness = new Witness
                {
                    InvocationScript = new byte[0],
                    VerificationScript = contract.Script
                };
                
                // Sign the transaction
                var data = tx.GetHashData();
                var signature = Neo.Cryptography.Crypto.Sign(data, privateKey);
                witness.InvocationScript = new ScriptBuilder().EmitPush(signature).ToArray();
                
                tx.Witnesses = new[] { witness };

                // Send transaction
                var txHash = await rpcClient.SendRawTransactionAsync(tx);
                Console.WriteLine($"✅ Deployment transaction sent!");
                Console.WriteLine($"📋 Transaction Hash: 0x{txHash}");

                // Wait for confirmation
                Console.WriteLine("\n⏳ Waiting for transaction confirmation...");
                await Task.Delay(15000); // Wait 15 seconds

                // Verify deployment
                try
                {
                    var contractState = await rpcClient.GetContractStateAsync(contractHash.ToString());
                    if (contractState != null)
                    {
                        Console.WriteLine("✅ Contract deployed successfully!");
                        Console.WriteLine($"   Name: {contractState.Manifest.Name}");
                        Console.WriteLine($"   Hash: 0x{contractHash}");
                    }
                }
                catch
                {
                    Console.WriteLine("⚠️  Contract verification pending. Check TestNet explorer for confirmation.");
                }

                // Initialize contract
                Console.WriteLine("\n📝 Next Steps:");
                Console.WriteLine("1. Update appsettings.json with contract hash: 0x" + contractHash);
                Console.WriteLine("2. Initialize the contract with the following command:");
                Console.WriteLine($"   dotnet run --project src/PriceFeed.ContractDeployer init");

                // Save contract hash for later use
                File.WriteAllText("contract-hash.txt", "0x" + contractHash);
                Console.WriteLine($"\n💾 Contract hash saved to: contract-hash.txt");

            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Deployment failed: {ex.Message}");
                Console.WriteLine(ex.StackTrace);
                Environment.Exit(1);
            }
        }
    }
}