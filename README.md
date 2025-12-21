# AI Agent Blueprint with LangGraph

A production-ready blueprint for building autonomous AI agents using LangGraph, featuring 4 distinct design patterns with planning, adaptation, autonomy, and self-reflection capabilities.

## 🎯 Features

### Four Agent Design Patterns

1. **ReAct Pattern** - Reasoning + Action
   - Iterative think-act-observe loop
   - Tool-based decision making
   - Ideal for: Dynamic problem-solving, exploration tasks

2. **Plan-Execute Pattern** - Strategic Planning
   - Upfront strategic planning
   - Sequential execution with oversight
   - Ideal for: Multi-step tasks, complex workflows

3. **Self-Reflection Pattern** - Iterative Refinement
   - Generate → Critique → Refine cycle
   - Quality-driven iteration
   - Ideal for: Content creation, analysis reports

4. **Adaptive Multi-Agent Pattern** - Collaborative Specialists
   - Dynamic agent coordination
   - Specialized expert agents
   - Ideal for: Complex analysis requiring multiple perspectives

### Core Capabilities

- ✅ **Planning**: Strategic goal decomposition and task orchestration
- ✅ **Adaptation**: Dynamic strategy adjustment based on context
- ✅ **Autonomy**: Independent decision-making with minimal human intervention
- ✅ **Self-Reflection**: Iterative quality assessment and improvement
- ✅ **Tool Integration**: Stock price APIs and vector database search
- ✅ **Production Ready**: Kubernetes deployment with monitoring and autoscaling

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Agent Patterns                         │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   ReAct     │  │ Plan-Execute │  │  Reflection    │  │
│  │             │  │              │  │                │  │
│  │ Think→Act→  │  │ Plan→Execute │  │ Generate→      │  │
│  │ Observe     │  │ →Synthesize  │  │ Critique→      │  │
│  │             │  │              │  │ Refine         │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Multi-Agent System                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │    │
│  │  │Supervisor│→ │Data      │→ │Technical │→...  │    │
│  │  │          │  │Collector │  │Analyst   │      │    │
│  │  └──────────┘  └──────────┘  └──────────┘      │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                      Tool Layer                           │
├──────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │Stock Price  │  │Stock History │  │Vector DB       │  │
│  │API (Alpha   │  │API (FMP)     │  │Search          │  │
│  │Vantage)     │  │              │  │                │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key
- Stock API keys (Alpha Vantage, FMP)
- Vector DB credentials (Pinecone/Weaviate)

### Local Development

```bash
# Clone repository
git clone <your-repo>
cd agent-blueprint

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export ALPHA_VANTAGE_API_KEY="your-key"
export FMP_API_KEY="your-key"
export PINECONE_API_KEY="your-key"
export PINECONE_ENVIRONMENT="your-env"

# Run demo
python agent_blueprint.py

# Or start the API server
python server.py
```

### Using the API

```bash
# Health check
curl http://localhost:8000/health

# Invoke ReAct agent
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Should I invest in AAPL?",
    "pattern": "react",
    "max_iterations": 3
  }'

# Invoke Plan-Execute agent
curl -X POST http://localhost:8000/agent/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze GOOGL stock comprehensively",
    "pattern": "plan_execute"
  }'

# Stream responses
curl -X POST http://localhost:8000/agent/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are AI stock trends?",
    "pattern": "react",
    "stream": true
  }'
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t agent-blueprint:latest .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY="your-key" \
  -e ALPHA_VANTAGE_API_KEY="your-key" \
  -e FMP_API_KEY="your-key" \
  -e PINECONE_API_KEY="your-key" \
  -e PINECONE_ENVIRONMENT="your-env" \
  agent-blueprint:latest
```

## ☸️ Kubernetes Deployment

See [k8s/DEPLOYMENT_GUIDE.md](k8s/DEPLOYMENT_GUIDE.md) for complete instructions.

### Quick Deploy

```bash
# Create namespace
kubectl apply -f k8s/namespace-netpol.yaml

# Configure secrets
kubectl create secret generic agent-secrets \
  --from-literal=ANTHROPIC_API_KEY='your-key' \
  --from-literal=ALPHA_VANTAGE_API_KEY='your-key' \
  --from-literal=FMP_API_KEY='your-key' \
  --from-literal=PINECONE_API_KEY='your-key' \
  --from-literal=PINECONE_ENVIRONMENT='your-env' \
  --namespace=ai-agents

# Deploy all resources
kubectl apply -f k8s/

# Check status
kubectl get pods -n ai-agents
kubectl get svc -n ai-agents
```

## 📊 Pattern Comparison

| Feature | ReAct | Plan-Execute | Reflection | Multi-Agent |
|---------|-------|--------------|------------|-------------|
| Planning | Iterative | Upfront | Minimal | Distributed |
| Execution | Sequential | Phased | Iterative | Parallel |
| Best For | Exploration | Structured tasks | Quality content | Complex analysis |
| Iterations | 3-5 | 1 (with steps) | 2-3 | Dynamic |
| Tool Calls | Multiple | Multiple | Few | Many |
| Output Quality | Good | Very Good | Excellent | Excellent |
| Latency | Medium | Medium-High | High | Medium |

## 🛠️ Customization

### Adding New Tools

```python
from langchain_core.tools import tool

@tool
def your_custom_tool(param: str) -> dict:
    """
    Tool description for the LLM
    
    Args:
        param: Parameter description
    
    Returns:
        Result dictionary
    """
    # Your implementation
    return {"result": "data"}

# Add to tools list
tools.append(your_custom_tool)
```

### Creating Custom Patterns

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class CustomState(TypedDict):
    # Your state fields
    messages: list
    custom_field: str

def create_custom_agent():
    workflow = StateGraph(CustomState)
    
    # Define nodes
    def custom_node(state: CustomState):
        # Your logic
        return state
    
    # Build graph
    workflow.add_node("custom", custom_node)
    workflow.add_edge("custom", END)
    
    return workflow.compile()
```

## 📈 Monitoring

### Prometheus Metrics

The API exposes metrics at `/metrics`:

- `agent_requests_total` - Total requests by pattern and status
- `agent_request_duration_seconds` - Request duration histogram
- `agent_errors_total` - Error counts by pattern and type

### Health Endpoints

- `/health` - Liveness probe
- `/ready` - Readiness probe
- `/metrics` - Prometheus metrics

## 🔒 Security

- Non-root container user
- Read-only root filesystem option
- Network policies for pod isolation
- Secret management for API keys
- RBAC with minimal permissions
- Pod Security Standards compliant

## 📝 API Reference

### POST /agent/invoke

Invoke an agent with specified pattern.

**Request:**
```json
{
  "query": "string",
  "pattern": "react|plan_execute|reflection|multi_agent",
  "max_iterations": 3,
  "thread_id": "optional-thread-id"
}
```

**Response:**
```json
{
  "pattern": "react",
  "query": "Should I invest in AAPL?",
  "result": "Based on analysis...",
  "metadata": {
    "iterations": 3,
    "processing_time": 2.5,
    "quality_score": 8.5
  },
  "timestamp": "2025-12-21T10:30:00",
  "thread_id": "react-12345"
}
```

### POST /agent/stream

Stream agent responses in real-time.

**Request:** Same as `/agent/invoke` with `"stream": true`

**Response:** Server-Sent Events (SSE)

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=agent_blueprint tests/

# Specific pattern
pytest tests/test_react_pattern.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent framework
- [LangChain](https://github.com/langchain-ai/langchain) - LLM orchestration
- [Anthropic Claude](https://anthropic.com) - Language model
- [FastAPI](https://fastapi.tiangolo.com) - Web framework

## 📚 Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Anthropic Documentation](https://docs.anthropic.com)
- [Agent Design Patterns](https://www.anthropic.com/research)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)

## 🐛 Troubleshooting

### Common Issues

**Agent not initializing:**
- Check API keys are set correctly
- Verify network access to APIs
- Review pod logs: `kubectl logs <pod-name>`

**High latency:**
- Adjust `max_iterations` parameter
- Scale up replicas
- Check external API response times

**Out of memory:**
- Increase resource limits in deployment.yaml
- Reduce concurrent requests
- Enable autoscaling

## 📞 Support

- Open an issue on GitHub
- Check the [Deployment Guide](k8s/DEPLOYMENT_GUIDE.md)
- Review pattern examples in `agent_blueprint.py`

---

**Built with ❤️ using LangGraph and Claude**
