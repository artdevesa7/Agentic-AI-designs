# AI Agent Blueprint - Kubernetes Deployment Guide

## Overview

This guide covers the complete deployment of the AI Agent Blueprint system to Kubernetes, including all 4 agent patterns (ReAct, Plan-Execute, Self-Reflection, Multi-Agent).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Kubernetes Cluster                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐         ┌──────────────────────┐          │
│  │   Ingress   │────────▶│  LoadBalancer/NLB   │          │
│  │  Controller │         └──────────────────────┘          │
│  └─────────────┘                    │                       │
│         │                            │                       │
│         ▼                            ▼                       │
│  ┌─────────────────────────────────────────────┐            │
│  │        agent-blueprint-service              │            │
│  │         (ClusterIP / LoadBalancer)          │            │
│  └─────────────────────────────────────────────┘            │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           agent-blueprint Deployment                 │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐    │   │
│  │  │   Pod 1    │  │   Pod 2    │  │   Pod 3    │    │   │
│  │  │  ReAct     │  │  Plan-Exec │  │  Reflect   │    │   │
│  │  │  + All     │  │  + All     │  │  + All     │    │   │
│  │  │  Patterns  │  │  Patterns  │  │  Patterns  │    │   │
│  │  └────────────┘  └────────────┘  └────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                    │                    │          │
│         ▼                    ▼                    ▼          │
│  ┌─────────────┐      ┌──────────┐      ┌──────────┐       │
│  │  ConfigMap  │      │ Secrets  │      │   HPA    │       │
│  └─────────────┘      └──────────┘      └──────────┘       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │Anthropic │        │ Stock    │        │ Vector   │
   │   API    │        │  APIs    │        │   DB     │
   └──────────┘        └──────────┘        └──────────┘
```

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   - Managed: EKS, GKE, AKS
   - Self-hosted: kubeadm, k3s, kind
   
2. **kubectl** configured and connected to your cluster

3. **Container Registry**
   - Docker Hub, ECR, GCR, ACR, or private registry

4. **API Keys** (required)
   - Anthropic API key
   - Alpha Vantage API key
   - Financial Modeling Prep API key
   - Vector DB credentials (Pinecone/Weaviate/Qdrant)

5. **Optional Tools**
   - Helm (for easier management)
   - Prometheus + Grafana (for monitoring)
   - cert-manager (for TLS certificates)

## Step 1: Build and Push Docker Image

```bash
# Build the Docker image
docker build -t agent-blueprint:latest .

# Tag for your registry
docker tag agent-blueprint:latest your-registry/agent-blueprint:v1.0.0

# Push to registry
docker push your-registry/agent-blueprint:v1.0.0

# Update deployment.yaml with your image
# image: your-registry/agent-blueprint:v1.0.0
```

## Step 2: Create Namespace

```bash
# Create the namespace
kubectl apply -f k8s/namespace-netpol.yaml

# Verify
kubectl get namespace ai-agents
```

## Step 3: Configure Secrets

```bash
# Option 1: From command line (recommended for production)
kubectl create secret generic agent-secrets \
  --from-literal=ANTHROPIC_API_KEY='your-anthropic-key' \
  --from-literal=ALPHA_VANTAGE_API_KEY='your-alphavantage-key' \
  --from-literal=FMP_API_KEY='your-fmp-key' \
  --from-literal=PINECONE_API_KEY='your-pinecone-key' \
  --from-literal=PINECONE_ENVIRONMENT='your-pinecone-env' \
  --from-literal=LANGCHAIN_API_KEY='your-langsmith-key' \
  --namespace=ai-agents

# Option 2: From file (update secret.yaml first)
kubectl apply -f k8s/secret.yaml

# Verify (values should be hidden)
kubectl get secrets -n ai-agents
kubectl describe secret agent-secrets -n ai-agents
```

## Step 4: Apply ConfigMap

```bash
# Apply configuration
kubectl apply -f k8s/configmap.yaml

# Verify
kubectl get configmap -n ai-agents
kubectl describe configmap agent-config -n ai-agents
```

## Step 5: Setup RBAC

```bash
# Create ServiceAccount and permissions
kubectl apply -f k8s/rbac.yaml

# Verify
kubectl get serviceaccount -n ai-agents
kubectl get role -n ai-agents
kubectl get rolebinding -n ai-agents
```

## Step 6: Deploy Application

```bash
# Deploy the application
kubectl apply -f k8s/deployment.yaml

# Watch deployment progress
kubectl rollout status deployment/agent-blueprint -n ai-agents

# Check pods
kubectl get pods -n ai-agents -w

# View logs
kubectl logs -f deployment/agent-blueprint -n ai-agents
```

## Step 7: Create Service

```bash
# Create services
kubectl apply -f k8s/service.yaml

# Verify
kubectl get svc -n ai-agents

# For LoadBalancer, get external IP (may take a few minutes)
kubectl get svc agent-blueprint-service -n ai-agents -w
```

## Step 8: Configure Autoscaling

```bash
# Deploy HPA
kubectl apply -f k8s/hpa.yaml

# Verify
kubectl get hpa -n ai-agents

# Watch autoscaling in action
kubectl get hpa agent-blueprint-hpa -n ai-agents -w
```

## Step 9: Setup Ingress (Optional)

```bash
# If using NGINX Ingress Controller
# First install NGINX if not present:
# kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml

# Apply ingress
kubectl apply -f k8s/ingress.yaml

# Verify
kubectl get ingress -n ai-agents

# Get ingress IP/hostname
kubectl get ingress agent-blueprint-ingress -n ai-agents
```

## Step 10: Apply Pod Disruption Budget

```bash
# Ensure high availability during updates
kubectl apply -f k8s/pdb.yaml

# Verify
kubectl get pdb -n ai-agents
```

## Testing the Deployment

### 1. Port Forward (for local testing)

```bash
# Forward port to local machine
kubectl port-forward -n ai-agents service/agent-blueprint-service 8000:80

# Test in another terminal
curl http://localhost:8000/health
```

### 2. Test Health Endpoints

```bash
# Get service external IP
export SERVICE_IP=$(kubectl get svc agent-blueprint-service -n ai-agents -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Or for hostname
export SERVICE_HOST=$(kubectl get svc agent-blueprint-service -n ai-agents -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Health check
curl http://$SERVICE_IP/health

# Readiness check
curl http://$SERVICE_IP/ready

# API info
curl http://$SERVICE_IP/
```

### 3. Test Agent Endpoints

```bash
# ReAct pattern
curl -X POST http://$SERVICE_IP/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I invest in AAPL?",
    "pattern": "react",
    "max_iterations": 3
  }'

# Plan-Execute pattern
curl -X POST http://$SERVICE_IP/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze GOOGL stock performance",
    "pattern": "plan_execute"
  }'

# Self-Reflection pattern
curl -X POST http://$SERVICE_IP/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare MSFT and AAPL",
    "pattern": "reflection",
    "max_iterations": 2
  }'

# Multi-Agent pattern
curl -X POST http://$SERVICE_IP/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Risk assessment for tech stocks",
    "pattern": "multi_agent"
  }'
```

### 4. Test Streaming

```bash
curl -X POST http://$SERVICE_IP/agent/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the trends in AI stocks?",
    "pattern": "react",
    "stream": true
  }'
```

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -f deployment/agent-blueprint -n ai-agents

# Specific pod
kubectl logs -f <pod-name> -n ai-agents

# Previous instance (if crashed)
kubectl logs <pod-name> -n ai-agents --previous

# Tail last 100 lines
kubectl logs --tail=100 -f deployment/agent-blueprint -n ai-agents
```

### Metrics

```bash
# Prometheus metrics
curl http://$SERVICE_IP/metrics

# Pod metrics (requires metrics-server)
kubectl top pods -n ai-agents

# Node metrics
kubectl top nodes
```

### Describe Resources

```bash
# Deployment
kubectl describe deployment agent-blueprint -n ai-agents

# Pods
kubectl describe pods -n ai-agents

# Service
kubectl describe svc agent-blueprint-service -n ai-agents

# HPA
kubectl describe hpa agent-blueprint-hpa -n ai-agents
```

## Scaling

### Manual Scaling

```bash
# Scale to 5 replicas
kubectl scale deployment agent-blueprint --replicas=5 -n ai-agents

# Verify
kubectl get deployment agent-blueprint -n ai-agents
```

### Auto-scaling

```bash
# HPA automatically scales based on:
# - CPU utilization (70%)
# - Memory utilization (80%)
# - Custom metrics (requests per second)

# Watch HPA in action
kubectl get hpa -n ai-agents -w
```

## Updates and Rollbacks

### Rolling Update

```bash
# Update image
kubectl set image deployment/agent-blueprint \
  agent-api=your-registry/agent-blueprint:v1.1.0 \
  -n ai-agents

# Watch rollout
kubectl rollout status deployment/agent-blueprint -n ai-agents

# Check rollout history
kubectl rollout history deployment/agent-blueprint -n ai-agents
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/agent-blueprint -n ai-agents

# Rollback to specific revision
kubectl rollout undo deployment/agent-blueprint --to-revision=2 -n ai-agents
```

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods -n ai-agents

# Describe pod for events
kubectl describe pod <pod-name> -n ai-agents

# Check logs
kubectl logs <pod-name> -n ai-agents

# Common issues:
# 1. Image pull errors - check registry credentials
# 2. Secret not found - verify secret exists
# 3. Resource limits - check node capacity
```

### Service not accessible

```bash
# Check service
kubectl get svc -n ai-agents
kubectl describe svc agent-blueprint-service -n ai-agents

# Check endpoints
kubectl get endpoints -n ai-agents

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n ai-agents -- \
  curl http://agent-blueprint-service/health
```

### HPA not scaling

```bash
# Check metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Check HPA status
kubectl describe hpa agent-blueprint-hpa -n ai-agents

# Check pod metrics
kubectl top pods -n ai-agents
```

## Cleanup

```bash
# Delete all resources in namespace
kubectl delete namespace ai-agents

# Or delete individually
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/hpa.yaml
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/pdb.yaml
kubectl delete -f k8s/rbac.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secret.yaml
kubectl delete -f k8s/namespace-netpol.yaml
```

## Production Recommendations

1. **Use a proper secrets management solution**
   - AWS Secrets Manager + External Secrets Operator
   - HashiCorp Vault
   - Google Secret Manager

2. **Enable monitoring**
   - Prometheus + Grafana
   - DataDog / New Relic
   - Cloud-native monitoring (CloudWatch, Stackdriver)

3. **Set up log aggregation**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - Loki + Grafana
   - Cloud logging solutions

4. **Implement CI/CD**
   - GitHub Actions
   - GitLab CI
   - Jenkins
   - ArgoCD for GitOps

5. **Use resource quotas**
   ```bash
   kubectl create quota agent-quota \
     --hard=requests.cpu=10,requests.memory=20Gi,pods=20 \
     -n ai-agents
   ```

6. **Enable Network Policies**
   - Already included in namespace-netpol.yaml
   - Verify with a CNI that supports them (Calico, Cilium)

7. **Regular backups**
   - Backup ConfigMaps and Secrets
   - Use Velero for cluster backups

8. **Security scanning**
   - Scan container images (Trivy, Snyk)
   - Use Pod Security Standards
   - Implement OPA/Gatekeeper policies

## Cost Optimization

1. **Right-size resources**
   ```bash
   # Monitor actual usage
   kubectl top pods -n ai-agents
   
   # Adjust requests/limits in deployment.yaml
   ```

2. **Use spot/preemptible instances** for non-critical workloads

3. **Configure autoscaling properly**
   - Set appropriate min/max replicas
   - Use cluster autoscaler

4. **Use pod priority classes**
   ```yaml
   apiVersion: scheduling.k8s.io/v1
   kind: PriorityClass
   metadata:
     name: agent-high-priority
   value: 1000
   ```

## Support and Next Steps

- **Documentation**: Review LangGraph docs at https://langchain-ai.github.io/langgraph/
- **Monitoring**: Set up Prometheus + Grafana dashboards
- **CI/CD**: Automate deployments with GitHub Actions or ArgoCD
- **Scaling**: Implement cluster autoscaler for node-level scaling
- **Security**: Enable Pod Security Admission and network policies
