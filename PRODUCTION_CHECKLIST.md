# Production Deployment Checklist

## Pre-Deployment

### Environment Setup
- [ ] Set up production Neo N3 node or use reliable RPC endpoint
- [ ] Configure all required environment variables:
  - [ ] `NEO_RPC_ENDPOINT` - Production Neo RPC endpoint
  - [ ] `CONTRACT_SCRIPT_HASH` - Deployed contract hash
  - [ ] `TEE_ACCOUNT_ADDRESS` - TEE account address
  - [ ] `TEE_ACCOUNT_PRIVATE_KEY` - TEE account WIF (secure storage)
  - [ ] `MASTER_ACCOUNT_ADDRESS` - Master account address  
  - [ ] `MASTER_ACCOUNT_PRIVATE_KEY` - Master account WIF (secure storage)
  - [ ] API keys for data sources (optional but recommended)

### Security Review
- [ ] Remove all test credentials from configuration files
- [ ] Ensure private keys are stored in secure vault (e.g., Azure Key Vault, AWS Secrets Manager)
- [ ] Review and test dual-signature implementation
- [ ] Verify TEE environment isolation
- [ ] Run security audit on smart contract

### Smart Contract Deployment
1. [ ] Build the smart contract: `./build-contract.sh`
2. [ ] Deploy to testnet first and verify functionality
3. [ ] Initialize contract with production owner and TEE addresses
4. [ ] Add authorized oracles
5. [ ] Test price updates with small batch
6. [ ] Deploy to mainnet
7. [ ] Update `CONTRACT_SCRIPT_HASH` in configuration

### Testing
- [ ] Run all unit tests: `dotnet test`
- [ ] Run Neo integration tests
- [ ] Test with production-like data volumes
- [ ] Verify error handling and recovery
- [ ] Test circuit breaker functionality
- [ ] Load test the system

## Deployment

### Application Deployment
1. [ ] Build release version: `dotnet build -c Release`
2. [ ] Deploy to production environment
3. [ ] Configure monitoring and alerting
4. [ ] Set up log aggregation
5. [ ] Configure auto-scaling if needed

### Post-Deployment Verification
- [ ] Verify TEE account generation works correctly
- [ ] Confirm dual-signature transactions are being created
- [ ] Check price updates are reaching the blockchain
- [ ] Monitor error rates and system health
- [ ] Verify attestation creation

## Monitoring

### Key Metrics to Monitor
- [ ] Transaction success rate
- [ ] Price update latency
- [ ] Data source availability
- [ ] Error rates by operation
- [ ] TEE account balance (NEO/GAS)
- [ ] Master account balance (GAS for fees)

### Alerts to Configure
- [ ] Transaction failures above threshold
- [ ] Data source unavailability
- [ ] Low GAS balance on master account
- [ ] Circuit breaker triggered
- [ ] Excessive price deviation detected

## Maintenance

### Regular Tasks
- [ ] Monitor and transfer assets from TEE to Master account
- [ ] Review and update oracle list
- [ ] Update data source API keys before expiration
- [ ] Review error logs and optimize
- [ ] Update symbol mappings as needed

### Emergency Procedures
- [ ] Document rollback procedure
- [ ] Set up circuit breaker trigger process
- [ ] Create runbook for common issues
- [ ] Establish on-call rotation

## Compliance

- [ ] Ensure compliance with data provider terms of service
- [ ] Document data retention policies
- [ ] Set up audit logging
- [ ] Review regulatory requirements

## Notes

- The system now uses proper Neo N3 account generation and transaction signing
- All test compatibility bypasses have been removed
- Error handling has been improved with proper thresholds
- The smart contract includes comprehensive security features
- Always test thoroughly on testnet before mainnet deployment