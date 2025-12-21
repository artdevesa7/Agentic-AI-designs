#!/bin/bash
# AI Agent Blueprint - Quick Start Script

set -e

NAMESPACE="ai-agents"
DEPLOYMENT_NAME="agent-blueprint"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "docker is not installed. Please install Docker first."
        exit 1
    fi
    
    print_info "Prerequisites check passed ✓"
}

# Check API keys
check_api_keys() {
    print_info "Checking API keys..."
    
    missing_keys=()
    
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        missing_keys+=("ANTHROPIC_API_KEY")
    fi
    
    if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
        missing_keys+=("ALPHA_VANTAGE_API_KEY")
    fi
    
    if [ -z "$FMP_API_KEY" ]; then
        missing_keys+=("FMP_API_KEY")
    fi
    
    if [ -z "$PINECONE_API_KEY" ]; then
        missing_keys+=("PINECONE_API_KEY")
    fi
    
    if [ ${#missing_keys[@]} -gt 0 ]; then
        print_error "Missing required API keys: ${missing_keys[*]}"
        print_info "Please set the following environment variables:"
        for key in "${missing_keys[@]}"; do
            echo "  export $key='your-key-here'"
        done
        exit 1
    fi
    
    print_info "API keys check passed ✓"
}

# Build Docker image
build_image() {
    print_info "Building Docker image..."
    
    IMAGE_TAG="${1:-latest}"
    
    docker build -t agent-blueprint:$IMAGE_TAG .
    
    print_info "Docker image built successfully ✓"
}

# Create namespace
create_namespace() {
    print_info "Creating namespace $NAMESPACE..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        print_warning "Namespace $NAMESPACE already exists"
    else
        kubectl apply -f k8s/namespace-netpol.yaml
        print_info "Namespace created ✓"
    fi
}

# Create secrets
create_secrets() {
    print_info "Creating secrets..."
    
    if kubectl get secret agent-secrets -n $NAMESPACE &> /dev/null; then
        print_warning "Secrets already exist. Deleting and recreating..."
        kubectl delete secret agent-secrets -n $NAMESPACE
    fi
    
    kubectl create secret generic agent-secrets \
        --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        --from-literal=ALPHA_VANTAGE_API_KEY="$ALPHA_VANTAGE_API_KEY" \
        --from-literal=FMP_API_KEY="$FMP_API_KEY" \
        --from-literal=PINECONE_API_KEY="$PINECONE_API_KEY" \
        --from-literal=PINECONE_ENVIRONMENT="${PINECONE_ENVIRONMENT:-us-east-1-aws}" \
        --from-literal=LANGCHAIN_API_KEY="${LANGCHAIN_API_KEY:-}" \
        --namespace=$NAMESPACE
    
    print_info "Secrets created ✓"
}

# Deploy application
deploy_app() {
    print_info "Deploying application..."
    
    kubectl apply -f k8s/configmap.yaml
    kubectl apply -f k8s/rbac.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/hpa.yaml
    kubectl apply -f k8s/pdb.yaml
    
    print_info "Application deployed ✓"
}

# Wait for deployment
wait_for_deployment() {
    print_info "Waiting for deployment to be ready..."
    
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=5m
    
    print_info "Deployment is ready ✓"
}

# Get service info
get_service_info() {
    print_info "Getting service information..."
    
    echo ""
    print_info "Service Status:"
    kubectl get svc -n $NAMESPACE
    
    echo ""
    print_info "Pod Status:"
    kubectl get pods -n $NAMESPACE
    
    echo ""
    SERVICE_TYPE=$(kubectl get svc agent-blueprint-service -n $NAMESPACE -o jsonpath='{.spec.type}')
    
    if [ "$SERVICE_TYPE" = "LoadBalancer" ]; then
        print_info "Waiting for LoadBalancer IP..."
        kubectl get svc agent-blueprint-service -n $NAMESPACE -w &
        WATCH_PID=$!
        sleep 10
        kill $WATCH_PID 2>/dev/null || true
    fi
    
    echo ""
    print_info "To access the service locally:"
    echo "  kubectl port-forward -n $NAMESPACE service/agent-blueprint-service 8000:80"
    echo ""
    print_info "To view logs:"
    echo "  kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
    echo ""
}

# Test deployment
test_deployment() {
    print_info "Testing deployment..."
    
    # Port forward in background
    kubectl port-forward -n $NAMESPACE service/agent-blueprint-service 8000:80 &
    PORT_FORWARD_PID=$!
    
    sleep 5
    
    # Test health endpoint
    if curl -s http://localhost:8000/health > /dev/null; then
        print_info "Health check passed ✓"
    else
        print_warning "Health check failed"
    fi
    
    # Kill port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
}

# Main deployment flow
main() {
    echo "================================================"
    echo "  AI Agent Blueprint - Kubernetes Quick Start"
    echo "================================================"
    echo ""
    
    check_prerequisites
    check_api_keys
    
    # Ask user for confirmation
    read -p "Do you want to build and deploy? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    build_image "latest"
    create_namespace
    create_secrets
    deploy_app
    wait_for_deployment
    get_service_info
    
    echo ""
    print_info "Deployment completed successfully! 🎉"
    echo ""
    print_info "Next steps:"
    echo "  1. Port forward: kubectl port-forward -n $NAMESPACE svc/agent-blueprint-service 8000:80"
    echo "  2. Test: curl http://localhost:8000/health"
    echo "  3. View logs: kubectl logs -f deployment/$DEPLOYMENT_NAME -n $NAMESPACE"
    echo ""
}

# Cleanup function
cleanup() {
    print_info "Cleaning up deployment..."
    
    kubectl delete namespace $NAMESPACE
    
    print_info "Cleanup completed ✓"
}

# Parse arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    cleanup)
        cleanup
        ;;
    test)
        test_deployment
        ;;
    *)
        echo "Usage: $0 {deploy|cleanup|test}"
        exit 1
        ;;
esac
