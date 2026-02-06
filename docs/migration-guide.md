# Migration Guide: Bare-Metal to Kubernetes

## Overview

This guide provides a step-by-step process for migrating from bare-metal RHEL deployments to containerized Kubernetes infrastructure.

## Prerequisites

- Access to existing bare-metal servers
- Kubernetes cluster (1.28+)
- Docker installed on build machine
- kubectl and Helm configured
- Backup of all production data

---

## Phase 1: Assessment (Week 1)

### 1.1 Document Current State

```bash
# Inventory all services
systemctl list-units --type=service --state=running

# Document dependencies
lsof -i -P -n | grep LISTEN

# Check disk usage
df -h
du -sh /var/lib/mysql /var/lib/mongo

# Review configurations
cat /etc/my.cnf.d/server.cnf
cat /etc/mongod.conf
```

### 1.2 Create Migration Checklist

- [ ] List all services and dependencies
- [ ] Document database schemas
- [ ] Identify configuration files
- [ ] Map network ports and firewall rules
- [ ] Document backup procedures
- [ ] Create rollback plan

---

## Phase 2: Containerization (Week 2-3)

### 2.1 Build Docker Images

#### Web Application

```bash
cd src/web-app
docker build -f ../../docker/web-app/Dockerfile -t enterprise-platform/web-app:1.0.0 .
```

#### API Service

```bash
cd src/api-service
docker build -f ../../docker/api-service/Dockerfile -t enterprise-platform/api-service:1.0.0 .
```

### 2.2 Test Locally with Docker Compose

```bash
cd docker
docker-compose up -d

# Verify services
docker-compose ps
docker-compose logs -f

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:3000/health

# Stop services
docker-compose down
```

### 2.3 Data Migration Preparation

#### Export MariaDB Data

```bash
# On bare-metal server
mysqldump -u root -p --all-databases > /backup/mariadb-full-$(date +%Y%m%d).sql

# Compress
gzip /backup/mariadb-full-$(date +%Y%m%d).sql
```

#### Export MongoDB Data

```bash
# On bare-metal server
mongodump --out=/backup/mongodb-$(date +%Y%m%d)

# Compress
tar -czf /backup/mongodb-$(date +%Y%m%d).tar.gz /backup/mongodb-$(date +%Y%m%d)
```

---

## Phase 3: Kubernetes Preparation (Week 3-4)

### 3.1 Create Namespaces

```bash
kubectl apply -f kubernetes/namespaces/tenant-a.yaml
kubectl get namespaces
```

### 3.2 Configure Secrets

```bash
# Create secrets from files (recommended)
kubectl create secret generic db-credentials \
  --from-literal=mariadb-root-password='YourSecurePassword' \
  --from-literal=mariadb-user='app_user' \
  --from-literal=mariadb-password='YourAppPassword' \
  --from-literal=mongodb-admin-user='admin' \
  --from-literal=mongodb-admin-password='YourAdminPassword' \
  --from-literal=mongodb-user='app_user' \
  --from-literal=mongodb-password='YourAppPassword' \
  -n tenant-a
```

### 3.3 Deploy ConfigMaps

```bash
kubectl apply -f kubernetes/configmaps/app-config.yaml
kubectl get configmaps -n tenant-a
```

### 3.4 Set Up Persistent Storage

```bash
# Verify storage class
kubectl get storageclass

# Create PVCs
kubectl apply -f kubernetes/deployments/mariadb-statefulset.yaml
kubectl apply -f kubernetes/deployments/mongodb-statefulset.yaml

# Check PVC status
kubectl get pvc -n tenant-a
```

---

## Phase 4: Database Migration (Week 4)

### 4.1 Deploy Databases to Kubernetes

```bash
# Deploy MariaDB
kubectl apply -f kubernetes/deployments/mariadb-statefulset.yaml
kubectl apply -f kubernetes/services/mariadb-service.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app=mariadb -n tenant-a --timeout=300s

# Deploy MongoDB
kubectl apply -f kubernetes/deployments/mongodb-statefulset.yaml
kubectl apply -f kubernetes/services/mongodb-service.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app=mongodb -n tenant-a --timeout=300s
```

### 4.2 Import Data

#### MariaDB

```bash
# Copy backup to pod
kubectl cp /backup/mariadb-full-20260206.sql.gz tenant-a/mariadb-0:/tmp/

# Import data
kubectl exec -it mariadb-0 -n tenant-a -- bash
gunzip /tmp/mariadb-full-20260206.sql.gz
mysql -u root -p < /tmp/mariadb-full-20260206.sql
exit
```

#### MongoDB

```bash
# Copy backup to pod
kubectl cp /backup/mongodb-20260206.tar.gz tenant-a/mongodb-0:/tmp/

# Import data
kubectl exec -it mongodb-0 -n tenant-a -- bash
cd /tmp
tar -xzf mongodb-20260206.tar.gz
mongorestore --username admin --password YourAdminPassword --authenticationDatabase admin /tmp/mongodb-20260206
exit
```

### 4.3 Verify Data Integrity

```bash
# MariaDB
kubectl exec -it mariadb-0 -n tenant-a -- mysql -u root -p -e "SHOW DATABASES;"
kubectl exec -it mariadb-0 -n tenant-a -- mysql -u root -p enterprise_db -e "SELECT COUNT(*) FROM your_table;"

# MongoDB
kubectl exec -it mongodb-0 -n tenant-a -- mongosh -u admin -p YourAdminPassword --authenticationDatabase admin
use enterprise_db
db.data.count()
exit
```

---

## Phase 5: Application Deployment (Week 5)

### 5.1 Deploy Applications

```bash
# Deploy web app
kubectl apply -f kubernetes/deployments/web-app-deployment.yaml
kubectl apply -f kubernetes/services/web-app-service.yaml

# Deploy API service
kubectl apply -f kubernetes/deployments/api-deployment.yaml
kubectl apply -f kubernetes/services/api-service.yaml

# Check deployment status
kubectl get deployments -n tenant-a
kubectl get pods -n tenant-a
```

### 5.2 Configure Ingress

```bash
# Deploy Ingress
kubectl apply -f kubernetes/ingress/ingress.yaml

# Get Ingress IP
kubectl get ingress -n tenant-a
```

### 5.3 Configure DNS

Update your DNS records to point to the Ingress IP:

```
enterprise-platform.example.com  A  <INGRESS_IP>
```

---

## Phase 6: Testing & Validation (Week 5-6)

### 6.1 Functional Testing

```bash
# Test web app
curl https://enterprise-platform.example.com/health
curl https://enterprise-platform.example.com/ready

# Test API
curl https://enterprise-platform.example.com/api/health
curl https://enterprise-platform.example.com/api/items
```

### 6.2 Load Testing

```bash
# Install Apache Bench
sudo yum install httpd-tools

# Run load test
ab -n 1000 -c 10 https://enterprise-platform.example.com/
```

### 6.3 Failover Testing

```bash
# Delete a pod to test self-healing
kubectl delete pod web-app-<pod-id> -n tenant-a

# Watch pod recreation
kubectl get pods -n tenant-a -w

# Verify service availability
curl https://enterprise-platform.example.com/health
```

---

## Phase 7: Cutover (Week 6)

### 7.1 Pre-Cutover Checklist

- [ ] All data migrated and verified
- [ ] Application tests passing
- [ ] Monitoring configured
- [ ] Backup procedures tested
- [ ] Rollback plan documented
- [ ] Team trained on new system

### 7.2 Cutover Steps

1. **Announce maintenance window** (e.g., 2 AM - 6 AM)
2. **Stop writes to bare-metal databases**
   ```bash
   systemctl stop webapp
   systemctl stop mariadb
   systemctl stop mongod
   ```
3. **Final data sync** (incremental backup and restore)
4. **Update DNS** to point to Kubernetes Ingress
5. **Monitor logs and metrics**
6. **Verify application functionality**
7. **Announce completion**

### 7.3 Post-Cutover Monitoring

```bash
# Watch pod status
kubectl get pods -n tenant-a -w

# Monitor logs
kubectl logs -f deployment/web-app -n tenant-a
kubectl logs -f deployment/api-service -n tenant-a

# Check resource usage
kubectl top pods -n tenant-a
kubectl top nodes
```

---

## Phase 8: Optimization (Week 7+)

### 8.1 Enable Autoscaling

```bash
kubectl apply -f kubernetes/hpa/web-app-hpa.yaml
kubectl get hpa -n tenant-a
```

### 8.2 Configure RBAC

```bash
kubectl apply -f kubernetes/rbac/tenant-role.yaml
kubectl apply -f kubernetes/rbac/tenant-rolebinding.yaml
```

### 8.3 Set Resource Quotas

```bash
kubectl apply -f kubernetes/resource-quotas/tenant-quota.yaml
kubectl describe resourcequota tenant-quota -n tenant-a
```

---

## Rollback Plan

If issues arise during cutover:

### 1. Immediate Rollback

```bash
# Update DNS back to bare-metal servers
# Restart bare-metal services
systemctl start mariadb
systemctl start mongod
systemctl start webapp
```

### 2. Data Rollback

```bash
# Restore from pre-migration backup
mysql -u root -p < /backup/pre-migration-backup.sql
mongorestore /backup/pre-migration-mongodb
```

---

## Common Issues & Solutions

### Issue: Pods in CrashLoopBackOff

```bash
# Check logs
kubectl logs <pod-name> -n tenant-a

# Check events
kubectl describe pod <pod-name> -n tenant-a

# Common causes:
# - Missing secrets/configmaps
# - Database connection issues
# - Resource limits too low
```

### Issue: Database Connection Failures

```bash
# Verify service DNS
kubectl exec -it web-app-<pod-id> -n tenant-a -- nslookup mariadb-service

# Test database connectivity
kubectl exec -it web-app-<pod-id> -n tenant-a -- nc -zv mariadb-service 3306
```

### Issue: Persistent Volume Not Mounting

```bash
# Check PVC status
kubectl get pvc -n tenant-a

# Check PV status
kubectl get pv

# Describe PVC for events
kubectl describe pvc <pvc-name> -n tenant-a
```

---

## Best Practices

1. **Always test in staging first**
2. **Perform migrations during low-traffic periods**
3. **Keep bare-metal servers running for 30 days post-migration**
4. **Document all configuration changes**
5. **Train team on Kubernetes operations**
6. **Set up comprehensive monitoring before cutover**
7. **Have rollback plan tested and ready**

---

## Timeline Summary

| Phase | Duration | Key Activities |
|-------|----------|----------------|
| Assessment | Week 1 | Document current state, create plan |
| Containerization | Week 2-3 | Build images, test locally |
| K8s Preparation | Week 3-4 | Set up cluster, configure resources |
| Database Migration | Week 4 | Deploy DBs, import data |
| App Deployment | Week 5 | Deploy apps, configure ingress |
| Testing | Week 5-6 | Functional, load, failover tests |
| Cutover | Week 6 | Production migration |
| Optimization | Week 7+ | Autoscaling, monitoring, tuning |

**Total Duration:** 6-8 weeks

---

## Success Criteria

- ✅ Zero data loss during migration
- ✅ < 4 hours downtime during cutover
- ✅ All services operational in Kubernetes
- ✅ Monitoring and alerting configured
- ✅ Team trained on new platform
- ✅ Documentation complete
