# AI Agent Blueprint - Quick Reference Guide

## 🚀 Quick Start Commands

### Local Development
```bash
# Setup
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
export ALPHA_VANTAGE_API_KEY="your-key"
export FMP_API_KEY="your-key"

# Run locally
python agent_blueprint.py          # Demo all patterns
python server.py                   # Start API server

# Test
curl http://localhost:8000/health
```

### Docker
```bash
# Build
docker build -t agent-blueprint:latest .

# Run
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY="your-key" \
  agent-blueprint:latest

# Docker Compose
docker-compose up -d
```

### Kubernetes (Automated)
```bash
# One-command deploy
./quickstart.sh deploy

# Cleanup
./quickstart.sh cleanup
```

### Kubernetes (Manual)
```bash
# 1. Build and push image
docker build -t your-registry/agent-blueprint:v1.0.0 .
docker push your-registry/agent-blueprint:v1.0.0

# 2. Create namespace
kubectl apply -f k8s/namespace-netpol.yaml

# 3. Create secrets
kubectl create secret generic agent-secrets \
  --from-literal=ANTHROPIC_API_KEY='your-key' \
  --from-literal=ALPHA_VANTAGE_API_KEY='your-key' \
  --from-literal=FMP_API_KEY='your-key' \
  --from-literal=PINECONE_API_KEY='your-key' \
  --from-literal=PINECONE_ENVIRONMENT='your-env' \
  --namespace=ai-agents

# 4. Deploy
kubectl apply -f k8s/

# 5. Check status
kubectl get pods -n ai-agents
kubectl get svc -n ai-agents

# 6. Access
kubectl port-forward -n ai-agents svc/agent-blueprint-service 8000:80
```

## 📊 Agent Pattern Selection Guide

| Use Case | Best Pattern | Why |
|----------|--------------|-----|
| Quick stock check | ReAct | Fast, flexible iteration |
| Detailed analysis | Plan-Execute | Structured, comprehensive |
| Report writing | Reflection | High quality output |
| Multi-perspective analysis | Multi-Agent | Expert collaboration |
| Exploratory tasks | ReAct | Adaptive to unknowns |
| Compliance reports | Reflection | Quality-driven |
| Market research | Multi-Agent | Diverse viewpoints |

## 🔧 API Endpoints

### Health Checks
```bash
GET /health        # Liveness probe
GET /ready         # Readiness probe  
GET /metrics       # Prometheus metrics
GET /              # API info
```

### Agent Invocation
```bash
POST /agent/invoke
Content-Type: application/json

{
  "query": "Should I invest in AAPL?",
  "pattern": "react",              # react|plan_execute|reflection|multi_agent
  "max_iterations": 3,
  "thread_id": "optional-id"
}
```

### Streaming
```bash
POST /agent/stream
Content-Type: application/json

{
  "query": "Analyze GOOGL",
  "pattern": "react",
  "stream": true
}
```

## 📝 Pattern Details

### ReAct
```python
# State
{
  "messages": [HumanMessage(...)],
  "iteration": 0,
  "max_iterations": 3
}

# Use for: Dynamic exploration, quick queries
# Iterations: 1-5
# Latency: 2-5 seconds
```

### Plan-Execute
```python
# State
{
  "messages": [HumanMessage(...)],
  "plan": [],
  "current_step": 0,
  "results": {}
}

# Use for: Complex multi-step tasks
# Steps: 3-7 typical
# Latency: 5-15 seconds
```

### Reflection
```python
# State
{
  "messages": [HumanMessage(...)],
  "draft": "",
  "critique": "",
  "iteration": 0,
  "max_iterations": 2,
  "quality_score": 0.0
}

# Use for: High-quality content
# Iterations: 2-3
# Latency: 10-30 seconds
```

### Multi-Agent
```python
# State
{
  "messages": [HumanMessage(...)],
  "next_agent": "supervisor",
  "completed_agents": [],
  "findings": {},
  "confidence": 0.0
}

# Use for: Complex analysis
# Agents: 4-6 specialists
# Latency: 10-25 seconds
```

## 🐛 Troubleshooting

### Pods Not Starting
```bash
# Check status
kubectl get pods -n ai-agents
kubectl describe pod <pod-name> -n ai-agents

# Common fixes:
# 1. Image pull error → verify registry credentials
# 2. Secret not found → kubectl get secrets -n ai-agents
# 3. Resource limits → check node capacity
```

### Service Not Accessible
```bash
# Debug
kubectl get svc -n ai-agents
kubectl get endpoints -n ai-agents

# Test internally
kubectl run debug --rm -it --image=curlimages/curl -n ai-agents -- \
  curl http://agent-blueprint-service:80/health
```

### High Latency
```bash
# Check metrics
kubectl top pods -n ai-agents
curl http://localhost:8000/metrics

# Solutions:
# 1. Scale up: kubectl scale deployment agent-blueprint --replicas=5 -n ai-agents
# 2. Reduce max_iterations
# 3. Check external API response times
```

### Out of Memory
```bash
# Check usage
kubectl top pods -n ai-agents

# Fix:
# 1. Increase limits in deployment.yaml
# 2. Reduce concurrent requests
# 3. Enable autoscaling
```

## 📊 Monitoring

### View Logs
```bash
# Real-time
kubectl logs -f deployment/agent-blueprint -n ai-agents

# Last 100 lines
kubectl logs --tail=100 deployment/agent-blueprint -n ai-agents

# All pods
kubectl logs -l app=agent-blueprint -n ai-agents
```

### Metrics
```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics:
# - agent_requests_total
# - agent_request_duration_seconds
# - agent_errors_total
```

### Health Status
```bash
# Quick health check
kubectl get pods -n ai-agents
kubectl get hpa -n ai-agents

# Detailed
kubectl describe deployment agent-blueprint -n ai-agents
```

## 🔄 Updates and Rollbacks

### Deploy New Version
```bash
# Update image
kubectl set image deployment/agent-blueprint \
  agent-api=your-registry/agent-blueprint:v1.1.0 \
  -n ai-agents

# Watch progress
kubectl rollout status deployment/agent-blueprint -n ai-agents
```

### Rollback
```bash
# To previous version
kubectl rollout undo deployment/agent-blueprint -n ai-agents

# To specific version
kubectl rollout history deployment/agent-blueprint -n ai-agents
kubectl rollout undo deployment/agent-blueprint --to-revision=2 -n ai-agents
```

## 📈 Scaling

### Manual
```bash
# Scale to 5 replicas
kubectl scale deployment agent-blueprint --replicas=5 -n ai-agents
```

### Auto
```bash
# HPA handles automatically based on:
# - CPU > 70%
# - Memory > 80%  
# - Custom metrics

# View HPA status
kubectl get hpa -n ai-agents -w
```

## 🔒 Security

### Secrets Management
```bash
# View secrets (values hidden)
kubectl get secrets -n ai-agents
kubectl describe secret agent-secrets -n ai-agents

# Update secret
kubectl delete secret agent-secrets -n ai-agents
kubectl create secret generic agent-secrets \
  --from-literal=ANTHROPIC_API_KEY='new-key' \
  --namespace=ai-agents
  
# Restart pods to pick up new secrets
kubectl rollout restart deployment/agent-blueprint -n ai-agents
```

### Network Policies
```bash
# View policies
kubectl get networkpolicies -n ai-agents
kubectl describe networkpolicy agent-blueprint-netpol -n ai-agents
```

## 💾 Configuration

### Update ConfigMap
```bash
# Edit
kubectl edit configmap agent-config -n ai-agents

# Or apply new file
kubectl apply -f k8s/configmap.yaml

# Restart to apply
kubectl rollout restart deployment/agent-blueprint -n ai-agents
```

### Environment Variables
```bash
# Add via deployment patch
kubectl set env deployment/agent-blueprint \
  NEW_VAR=value \
  -n ai-agents
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# With coverage
pytest --cov=agent_blueprint tests/

# Specific test
pytest tests/test_agents.py::test_react_agent_creation
```

### Integration Testing
```bash
# Port forward
kubectl port-forward -n ai-agents svc/agent-blueprint-service 8000:80

# Test ReAct
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"query":"Test AAPL","pattern":"react"}'

# Test Plan-Execute
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"query":"Analyze GOOGL","pattern":"plan_execute"}'

# Test Reflection
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"query":"Report on MSFT","pattern":"reflection"}'

# Test Multi-Agent
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"query":"Comprehensive TSLA analysis","pattern":"multi_agent"}'
```

## 📦 File Structure

```
agent-blueprint/
├── agent_blueprint.py          # Core agent implementations
├── server.py                   # FastAPI server
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Local multi-container setup
├── quickstart.sh              # Automated deployment script
├── README.md                  # Main documentation
├── ARCHITECTURE.md            # Architecture details
├── .env.example              # Environment variables template
├── k8s/                      # Kubernetes manifests
│   ├── DEPLOYMENT_GUIDE.md   # Detailed K8s guide
│   ├── namespace-netpol.yaml # Namespace and network policy
│   ├── secret.yaml           # Secret template
│   ├── configmap.yaml        # Configuration
│   ├── rbac.yaml             # Service account and RBAC
│   ├── deployment.yaml       # Main deployment
│   ├── service.yaml          # Service definitions
│   ├── ingress.yaml          # Ingress rules
│   ├── hpa.yaml             # Horizontal pod autoscaler
│   └── pdb.yaml             # Pod disruption budget
├── helm/                     # Helm chart (alternative)
│   └── values.yaml          # Helm values
└── tests/                   # Test suite
    └── test_agents.py       # Agent tests
```

## 🎯 Common Use Cases

### Financial Analysis
```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Compare AAPL and GOOGL for investment",
    "pattern": "multi_agent",
    "max_iterations": 5
  }'
```

### Risk Assessment
```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Risk analysis for TSLA stock",
    "pattern": "reflection",
    "max_iterations": 3
  }'
```

### Market Research
```bash
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest trends in AI sector stocks",
    "pattern": "plan_execute"
  }'
```

## 🔑 Environment Variables

### Required
```bash
ANTHROPIC_API_KEY          # Claude API key
ALPHA_VANTAGE_API_KEY      # Stock price API
FMP_API_KEY                # Financial data API
PINECONE_API_KEY           # Vector DB (or alternative)
PINECONE_ENVIRONMENT       # Vector DB environment
```

### Optional
```bash
LANGCHAIN_TRACING_V2       # Enable LangSmith tracing
LANGCHAIN_API_KEY          # LangSmith API key
MAX_ITERATIONS             # Default: 3
LOG_LEVEL                  # Default: INFO
```

## 📞 Getting Help

1. **Check logs**: `kubectl logs -f deployment/agent-blueprint -n ai-agents`
2. **Review documentation**: `README.md`, `ARCHITECTURE.md`, `k8s/DEPLOYMENT_GUIDE.md`
3. **Test locally**: Run `python server.py` for debugging
4. **Verify configuration**: Check secrets and configmaps
5. **Monitor metrics**: Access `/metrics` endpoint

## ⚡ Performance Tips

1. **Right-size resources**: Monitor actual usage and adjust
2. **Use caching**: Implement Redis for frequently accessed data
3. **Batch requests**: Group multiple queries when possible
4. **Optimize iterations**: Lower max_iterations for faster responses
5. **Scale horizontally**: Add more replicas during peak times
6. **Monitor latency**: Track p50, p95, p99 latencies

## 🎓 Learning Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Anthropic API](https://docs.anthropic.com)
- [Kubernetes Docs](https://kubernetes.io/docs/)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Agent Patterns](./ARCHITECTURE.md)

---
**Happy Agent Building! 🤖**
