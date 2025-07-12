# Neo N3 Price Oracle Deployment Instructions

## Contract Details
- **Name**: PriceFeed.Oracle
- **Expected Hash**: 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc
- **NEF Size**: 2946 bytes
- **Manifest Size**: 4457 chars
- **Deployment Cost**: ~10.002 GAS

## Account Information
- **Address**: NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX
- **Private Key (WIF)**: KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
- **Balance**: 50 GAS (sufficient)

## Deployment Methods

### Option 1: Neo-CLI (Recommended)

1. **Download Neo-CLI**:
   ```bash
   wget https://github.com/neo-project/neo-cli/releases/download/v3.6.2/neo-cli-linux-x64.zip
   unzip neo-cli-linux-x64.zip
   cd neo-cli
   ```

2. **Start Neo-CLI**:
   ```bash
   ./neo-cli
   ```

3. **In Neo-CLI Console**:
   ```
   neo> create wallet deploy.json
   Password: [enter any password]
   neo> open wallet deploy.json
   Password: [enter your password]
   neo> import key KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb
   neo> list asset
   ```

4. **Deploy Contract**:
   ```
   neo> deploy PriceFeed.Oracle.nef PriceFeed.Oracle.manifest.json
   ```

5. **Confirm when prompted**

### Option 2: NeoLine Browser Extension

1. Install NeoLine: https://neoline.io/
2. Click "Import Wallet"
3. Select "Import from WIF"
4. Paste: `KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb`
5. Switch to TestNet (top right)
6. Go to: https://neoline.io/deploy
7. Upload the NEF and manifest files
8. Confirm the transaction

### Option 3: Neo GUI

1. Download Neo GUI: https://github.com/neo-project/neo-gui/releases
2. Import wallet using WIF
3. Switch to TestNet
4. Deploy contract through GUI

## Post-Deployment

After deployment, the contract hash should be: `0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc`

### Initialize Contract

Using Neo-CLI:
```
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc addOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
neo> invoke 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc setMinOracles [1]
```

### Verify Deployment
```
neo> invokefunction 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getOwner
neo> invokefunction 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc isOracle ["NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"]
neo> invokefunction 0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc getMinOracles
```

### Test Oracle
```bash
cd /home/neo/git/neo-price-feed
export COINMARKETCAP_API_KEY="your-api-key"
dotnet run --project src/PriceFeed.Console
```

## Troubleshooting

- If deployment fails with "insufficient GAS", check balance
- If "invalid signature", ensure correct private key
- If "contract already exists", check the contract hash

## Support

- Neo Discord: https://discord.gg/neo
- TestNet Explorer: https://testnet.explorer.onegate.space/
