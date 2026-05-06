#!/bin/bash
set -e

echo "Deploying LLM Inference Platform..."

# Apply Kubernetes manifests
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml

echo "Deployment submitted. Waiting for pods to be ready..."
kubectl rollout status deployment/llm-inference-server

echo "Done!"
