# Neo Price Feed - Quick Start Deployment Guide

## 🚀 5-Minute Deployment

### Prerequisites
- .NET 9.0 SDK installed
- Git repository cloned
- Neo account with private keys

### Step 1: Set Environment Variables (30 seconds)
```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your values
nano .env
# Or set directly:
export TEE_ACCOUNT_ADDRESS="your-tee-address"
export TEE_ACCOUNT_PRIVATE_KEY="your-tee-key"
export MASTER_ACCOUNT_ADDRESS="your-master-address"
export MASTER_ACCOUNT_PRIVATE_KEY="your-master-key"
```

### Step 2: Build Project (1 minute)
```bash
dotnet build src/PriceFeed.Console/PriceFeed.Console.csproj --configuration Release
```

### Step 3: Run Price Feed (Immediate)
```bash
# For TestNet deployment
dotnet run --project src/PriceFeed.Console --configuration Release

# For Production MainNet (when ready)
ASPNETCORE_ENVIRONMENT=Production dotnet run --project src/PriceFeed.Console --configuration Release
```

## 🔍 Verify It's Working

### Check Logs
You should see output like:
```
{"@t":"2025-07-12T10:00:00.000Z","@mt":"Starting PriceFeed job","Application":"PriceFeed"}
{"@t":"2025-07-12T10:00:01.000Z","@mt":"Collecting price data from {Source}","Source":"CoinGecko"}
{"@t":"2025-07-12T10:00:02.000Z","@mt":"Successfully processed batch {BatchId}","BatchId":"..."}
```

### Check Contract Status
```bash
bash scripts/check-contract-status.sh
```

## 🔧 Common Issues

### "Missing environment variables"
- Ensure all required variables are set
- Check `.env` file is in correct location
- Use `source .env` to load variables

### "Contract not initialized"
- The contract needs one-time initialization
- Follow INITIALIZATION_GUIDE.md

### "No price data collected"
- Check internet connectivity
- Verify at least one data source is accessible
- CoinGecko and Kraken work without API keys

## 📊 GitHub Actions Deployment

### 1. Set Secrets (2 minutes)
Go to: Settings → Secrets and variables → Actions

Add these secrets:
- `TEE_ACCOUNT_ADDRESS`
- `TEE_ACCOUNT_PRIVATE_KEY`
- `MASTER_ACCOUNT_ADDRESS`
- `MASTER_ACCOUNT_PRIVATE_KEY`

### 2. Enable Workflow
- Go to Actions tab
- Enable workflows if disabled
- The price feed runs every 5 minutes automatically

### 3. Manual Trigger
- Go to Actions → Neo Price Feed Service
- Click "Run workflow"
- Select branch and run

## 🎯 Next Steps

1. **Monitor Price Updates**
   - Check blockchain explorer
   - Review GitHub Actions logs
   - Query contract for prices

2. **Add More Data Sources**
   - Get API keys for better coverage
   - Configure in environment variables

3. **Set Up Monitoring**
   - Configure OTLP endpoint
   - Set up alerts for failures

---

**Need Help?**
- Check PROJECT_STATUS_FINAL.md for detailed status
- Review DEPLOYMENT_CHECKLIST.md for full checklist
- See logs for specific errors

**Quick Commands:**
```bash
# Build and run in one command
dotnet run --project src/PriceFeed.Console --configuration Release

# Check if working
curl -s http://seed1t5.neo.org:20332 -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"getcontractstate","params":["0xc14ffc3f28363fe59645873b28ed3ed8ccb774cc"],"id":1}' \
  | jq .result.manifest.name
```

You should see: `"PriceFeed.Oracle"`