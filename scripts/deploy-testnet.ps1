# Neo N3 TestNet Deployment Script
# This script compiles and deploys the PriceOracle contract to Neo N3 TestNet

param(
    [string]$RpcEndpoint = "http://seed1t5.neo.org:20332",
    [string]$OwnerAddress = "NTmHjwiadq4g3VHpJ5FQigQcD4fF5m8TyX",
    [string]$OwnerPrivateKey = "KzjaqMvqzF1uup6KrTKRxTgjcXE7PbKLRH84e6ckyXDt3fu7afUb",
    [string]$TeeAccountAddress = "NiNmXL8FjEUEs1nfX9uHFBNaenxDHJtmuB"
)

Write-Host "=== Neo N3 TestNet Deployment Script ===" -ForegroundColor Green
Write-Host "RPC Endpoint: $RpcEndpoint"
Write-Host "Owner Address: $OwnerAddress" 
Write-Host "TEE Account: $TeeAccountAddress"
Write-Host ""

# Step 1: Compile the smart contract
Write-Host "Step 1: Compiling PriceOracle contract..." -ForegroundColor Yellow
$contractPath = "src/PriceFeed.Contracts"

try {
    Push-Location $contractPath
    
    # Build the contract
    dotnet build --configuration Release
    if ($LASTEXITCODE -ne 0) {
        throw "Contract compilation failed"
    }
    
    # Find the compiled NEF and manifest files
    $nefFile = Get-ChildItem -Path "bin/Release/net8.0" -Name "*.nef" | Select-Object -First 1
    $manifestFile = Get-ChildItem -Path "bin/Release/net8.0" -Name "*.manifest.json" | Select-Object -First 1
    
    if (-not $nefFile -or -not $manifestFile) {
        throw "Compiled contract files not found"
    }
    
    $nefPath = "bin/Release/net8.0/$nefFile"
    $manifestPath = "bin/Release/net8.0/$manifestFile"
    
    Write-Host "✓ Contract compiled successfully" -ForegroundColor Green
    Write-Host "  NEF file: $nefPath"
    Write-Host "  Manifest: $manifestPath"
} catch {
    Write-Host "✗ Contract compilation failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# Step 2: Deploy using neo-express (if available) or prepare for manual deployment
Write-Host ""
Write-Host "Step 2: Preparing deployment to TestNet..." -ForegroundColor Yellow

# Check if neo-express is available for local testing first
$neoExpressAvailable = $false
try {
    $null = neoxp --version 2>$null
    $neoExpressAvailable = $true
    Write-Host "✓ Neo Express is available for local testing" -ForegroundColor Green
} catch {
    Write-Host "⚠ Neo Express not available, will prepare for manual deployment" -ForegroundColor Yellow
}

# Read the compiled contract files
try {
    $nefBytes = [System.IO.File]::ReadAllBytes("$contractPath/$nefPath")
    $manifestContent = Get-Content "$contractPath/$manifestPath" -Raw
    
    Write-Host "✓ Contract files read successfully" -ForegroundColor Green
    Write-Host "  NEF size: $($nefBytes.Length) bytes"
    Write-Host "  Manifest size: $($manifestContent.Length) characters"
} catch {
    Write-Host "✗ Failed to read contract files: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Generate deployment transaction
Write-Host ""
Write-Host "Step 3: Generating deployment information..." -ForegroundColor Yellow

# Calculate contract hash (this is approximate - actual hash will be determined on deployment)
$contractName = "PriceOracle"
Write-Host "Contract Name: $contractName"

# Create deployment script template
$deploymentScript = @"
// Neo N3 TestNet Deployment Script
// Deploy this using Neo-CLI or Neo-GUI

// 1. Import owner wallet
// neo> import key $OwnerPrivateKey

// 2. Deploy contract
// neo> deploy $nefPath $manifestPath

// 3. Initialize contract (replace CONTRACT_HASH with actual deployed hash)
// neo> invoke CONTRACT_HASH initialize ["$OwnerAddress", "$TeeAccountAddress"]

// 4. Add TEE account as oracle
// neo> invoke CONTRACT_HASH addOracle ["$TeeAccountAddress"]

// 5. Set minimum oracles to 1
// neo> invoke CONTRACT_HASH setMinOracles [1]
"@

$deploymentScript | Out-File -FilePath "deployment-commands.txt" -Encoding UTF8
Write-Host "✓ Deployment commands saved to deployment-commands.txt" -ForegroundColor Green

# Step 4: Create PowerShell deployment function
Write-Host ""
Write-Host "Step 4: Creating deployment helper..." -ForegroundColor Yellow

$deployFunction = @'
# Neo N3 Contract Deployment Helper
function Deploy-PriceOracleContract {
    param(
        [string]$NeoCliPath = "neo-cli",
        [string]$RpcUrl = "http://seed1t5.neo.org:20332"
    )
    
    Write-Host "Deploying PriceOracle contract to Neo N3 TestNet..."
    Write-Host "Make sure you have Neo-CLI installed and configured"
    Write-Host ""
    Write-Host "Manual steps:"
    Write-Host "1. Start neo-cli with: neo-cli.exe --rpc"
    Write-Host "2. Import the owner wallet key"
    Write-Host "3. Use the deployment commands from deployment-commands.txt"
    Write-Host ""
    Write-Host "Or use neo-express for local testing first"
}
'@

$deployFunction | Out-File -FilePath "deploy-helper.ps1" -Encoding UTF8

Write-Host "=== Deployment Preparation Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Use neo-express for local testing: neoxp contract deploy $contractPath/$nefPath"
Write-Host "2. Or deploy to TestNet using neo-cli with the commands in deployment-commands.txt"
Write-Host "3. Update the CONTRACT_SCRIPT_HASH in appsettings.json with the deployed contract hash"
Write-Host ""
Write-Host "Files created:"
Write-Host "- deployment-commands.txt (neo-cli commands)"
Write-Host "- deploy-helper.ps1 (PowerShell helper functions)"