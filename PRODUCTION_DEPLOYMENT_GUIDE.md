# 🏭 Neo N3 Price Feed - Production Deployment Guide

## 🚀 **Production-Ready Deployment**

This guide covers deploying your Neo N3 Price Feed to production with enterprise-grade security, monitoring, and reliability.

## 📋 **Pre-Deployment Checklist**

### ✅ **Security Requirements**
- [ ] Remove all hardcoded API keys from code
- [ ] Set up secure secrets management
- [ ] Configure firewall rules
- [ ] Enable HTTPS/TLS encryption
- [ ] Set up monitoring and alerting

### ✅ **Infrastructure Requirements**
- [ ] Docker and Docker Compose installed
- [ ] Sufficient server resources (2 CPU cores, 4GB RAM minimum)
- [ ] Network access to Neo N3 network
- [ ] Backup storage for attestations
- [ ] Log aggregation system

## 🔐 **Security Configuration**

### **1. Environment Variables Setup**
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your production values
nano .env
```

### **2. Secrets Management**
For production, use a proper secrets management system:

#### **Azure Key Vault**
```bash
# Install Azure CLI
az login
az keyvault secret set --vault-name "your-keyvault" --name "coinmarketcap-api-key" --value "your-key"
```

#### **AWS Secrets Manager**
```bash
# Install AWS CLI
aws secretsmanager create-secret --name "neo-price-feed/coinmarketcap" --secret-string "your-key"
```

#### **HashiCorp Vault**
```bash
vault kv put secret/neo-price-feed coinmarketcap_api_key="your-key"
```

### **3. Network Security**
```bash
# Configure firewall (Ubuntu/Debian)
ufw allow 22/tcp    # SSH
ufw allow 8080/tcp  # Price Feed API
ufw allow 9090/tcp  # Prometheus (optional)
ufw allow 3000/tcp  # Grafana (optional)
ufw enable
```

## 🐳 **Docker Deployment**

### **1. Production Deployment**
```bash
# Build and start the application
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f price-feed
```

### **2. With Monitoring**
```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access monitoring
# Prometheus: http://your-server:9090
# Grafana: http://your-server:3000 (admin/admin)
```

### **3. Resource Management**
```yaml
# Production resource limits
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## 📊 **Monitoring Setup**

### **1. Health Checks**
```bash
# Check application health
curl http://localhost:8080/health

# Expected response
{
  "status": "Healthy",
  "totalDuration": "00:00:00.0123456",
  "entries": {
    "data_sources": {
      "status": "Healthy"
    },
    "neo_rpc": {
      "status": "Healthy"
    }
  }
}
```

### **2. Metrics Monitoring**
Key metrics to monitor:
- `price_data_collected_total` - Total price data points collected
- `neo_transaction_success_rate` - Success rate of Neo transactions
- `coinmarketcap_api_requests_total` - API request count
- `price_feed_errors_total` - Error count
- `memory_usage_bytes` - Memory consumption
- `cpu_usage_percent` - CPU utilization

### **3. Log Analysis**
```bash
# View structured logs
docker-compose logs price-feed | jq '.'

# Filter for errors
docker-compose logs price-feed | grep -i error

# Monitor in real-time
docker-compose logs -f price-feed
```

## 🚨 **Alerting Configuration**

### **1. Critical Alerts**
- Application down for > 1 minute
- No price data collected for > 10 minutes
- Neo RPC endpoint unreachable
- All data sources down

### **2. Warning Alerts**
- High error rate (> 10%)
- High price deviation (> 10%)
- High resource usage (> 80%)
- Single data source down

### **3. Notification Channels**
Configure alerts to send to:
- Email
- Slack
- PagerDuty
- Discord/Teams

## 🔧 **Maintenance Procedures**

### **1. Updates and Deployments**
```bash
# Zero-downtime deployment
docker-compose pull
docker-compose up -d --no-deps price-feed

# Rollback if needed
docker-compose down
docker-compose up -d --scale price-feed=0
# Deploy previous version
docker-compose up -d
```

### **2. Backup Procedures**
```bash
# Backup attestations
tar -czf attestations-backup-$(date +%Y%m%d).tar.gz ./attestations

# Backup configuration
cp .env .env.backup-$(date +%Y%m%d)

# Database backup (if using external DB)
# mysqldump -u user -p price_feed > backup.sql
```

### **3. Log Rotation**
```bash
# Configure logrotate
cat > /etc/logrotate.d/neo-price-feed << EOF
/var/lib/docker/containers/*/*-json.log {
  daily
  rotate 30
  compress
  delaycompress
  missingok
  notifempty
  copytruncate
}
EOF
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Contract Not Found Error**
```bash
# Check contract hash configuration
grep "ContractScriptHash" src/PriceFeed.Console/appsettings.json

# Verify contract exists on blockchain
curl -X POST http://seed1t5.neo.org:20332 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"getcontractstate","params":["0xYOUR_CONTRACT_HASH"],"id":1}'
```

#### **2. API Rate Limiting**
```bash
# Check API key status
curl -H "X-CMC_PRO_API_KEY: your-key" \
  "https://pro-api.coinmarketcap.com/v1/key/info"

# Monitor rate limits in logs
docker-compose logs price-feed | grep -i "rate limit"
```

#### **3. Memory Issues**
```bash
# Check memory usage
docker stats neo-price-feed

# Increase memory limit
# Edit docker-compose.yml and restart
```

### **Performance Tuning**

#### **1. Optimize Data Collection**
```json
{
  "PriceFeed": {
    "BatchSize": 20,
    "CollectionInterval": "00:05:00"
  }
}
```

#### **2. Optimize Neo RPC**
```json
{
  "BatchProcessing": {
    "MaxRetries": 3,
    "TimeoutSeconds": 30
  }
}
```

## 📈 **Scaling Considerations**

### **1. Horizontal Scaling**
- Deploy multiple instances behind a load balancer
- Use external data source for coordination
- Implement leader election for single writer

### **2. Vertical Scaling**
```yaml
# Increase resources
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
```

### **3. Data Source Optimization**
- Implement caching layer
- Use multiple API keys for higher rate limits
- Add more data sources for redundancy

## 🔒 **Security Best Practices**

### **1. Regular Security Updates**
```bash
# Update base images monthly
docker-compose pull
docker-compose up -d

# Update application dependencies
dotnet list package --outdated
dotnet add package [PackageName] --version [NewVersion]
```

### **2. Access Control**
- Use non-root user in containers
- Implement API authentication
- Restrict network access
- Regular security audits

### **3. Data Protection**
- Encrypt sensitive data at rest
- Use TLS for all communications
- Regular backup testing
- Secure key rotation

## 📞 **Support and Maintenance**

### **Emergency Contacts**
- System Administrator: [Contact Info]
- Neo Network Status: https://status.neo.org/
- CoinMarketCap Status: https://status.coinmarketcap.com/

### **Regular Maintenance Schedule**
- **Daily**: Check logs and metrics
- **Weekly**: Review performance and errors
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Full system backup and disaster recovery test

---

**🎯 Production Deployment Complete!** Your Neo N3 Price Feed is now running with enterprise-grade reliability, monitoring, and security. 🚀