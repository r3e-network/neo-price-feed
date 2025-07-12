#!/usr/bin/env node

const Neon = require("@cityofzion/neon-js");
const fs = require("fs");
const path = require("path");

// Configuration
const TESTNET_RPC = "http://seed1t5.neo.org:20332";
const MASTER_WIF = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb";
const CONTRACT_PATH = path.join(__dirname, "../src/PriceFeed.Contracts/PriceFeed.Oracle.nef");
const MANIFEST_PATH = path.join(__dirname, "../src/PriceFeed.Contracts/PriceFeed.Oracle.manifest.json");

async function deployContract() {
    try {
        console.log("🚀 Starting contract deployment to Neo N3 TestNet...");
        
        // Create account from WIF
        const account = Neon.create.account(MASTER_WIF);
        console.log(`📍 Deploying with account: ${account.address}`);
        
        // Read contract files
        if (!fs.existsSync(CONTRACT_PATH)) {
            throw new Error(`Contract file not found: ${CONTRACT_PATH}`);
        }
        if (!fs.existsSync(MANIFEST_PATH)) {
            throw new Error(`Manifest file not found: ${MANIFEST_PATH}`);
        }
        
        const nefFile = fs.readFileSync(CONTRACT_PATH);
        const manifest = fs.readFileSync(MANIFEST_PATH, 'utf8');
        
        console.log("📄 Contract files loaded successfully");
        
        // Create RPC client
        const rpcClient = new Neon.rpc.RPCClient(TESTNET_RPC);
        
        // Check account balance
        const balance = await rpcClient.getNep17Balances(account.address);
        console.log("💰 Account balances:", balance);
        
        // Deploy contract
        console.log("📤 Deploying contract to TestNet...");
        
        // Create deployment transaction
        const deployTx = Neon.create.deployContract({
            nef: nefFile.toString('hex'),
            manifest: manifest,
            account: account
        });
        
        // Send transaction
        const result = await rpcClient.sendRawTransaction(deployTx);
        console.log("✅ Deployment transaction sent!");
        console.log(`📋 Transaction Hash: ${result}`);
        
        // Calculate contract hash
        const contractHash = Neon.experimental.getContractHash(
            account.scriptHash,
            nefFile,
            manifest
        );
        
        console.log(`🎯 Contract Hash: ${contractHash}`);
        console.log("\n📝 Next steps:");
        console.log("1. Wait for transaction confirmation (check on TestNet explorer)");
        console.log("2. Update appsettings.json with the new contract hash");
        console.log("3. Initialize the contract with TEE and Master accounts");
        
        return contractHash;
        
    } catch (error) {
        console.error("❌ Deployment failed:", error.message);
        console.error(error);
        process.exit(1);
    }
}

// Run deployment
deployContract()
    .then(hash => {
        console.log("\n✅ Deployment script completed successfully!");
        process.exit(0);
    })
    .catch(err => {
        console.error("❌ Fatal error:", err);
        process.exit(1);
    });