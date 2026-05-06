# Production Setup Guide: LLM Inference Platform

This guide provides step-by-step instructions for deploying the complete LLM inference infrastructure from scratch to a production-ready state on AWS.

---

## 1. Prerequisites

Before starting, ensure you have the following installed locally:
- `aws-cli`: Configured with administrator access to your AWS account.
- `eksctl`: For creating and managing the EKS cluster.
- `kubectl`: The Kubernetes command-line tool.
- `helm`: The Kubernetes package manager.
- `docker`: For building and pushing any custom container images (if necessary).

---

## 2. Infrastructure Setup (AWS EKS)

### 2.1 Create the EKS Cluster
We need an Amazon EKS cluster with a CPU node group for core services and a GPU node group specifically for inference workloads.

Create a cluster configuration file `eks-cluster.yaml`:
```yaml
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: llm-inference-cluster
  region: us-east-1
  version: "1.29"

managedNodeGroups:
  - name: core-nodes
    instanceType: m5.large
    minSize: 1
    maxSize: 3
  - name: gpu-nodes
    instanceType: g4dn.2xlarge  # NVIDIA T4 GPU
    minSize: 1
    maxSize: 5
    volumeSize: 100
    iam:
      withAddonPolicies:
        autoScaler: true
```

Deploy the cluster:
```bash
eksctl create cluster -f eks-cluster.yaml
```
*(Note: This process usually takes 15-20 minutes).*

### 2.2 Install NVIDIA Device Plugin
For Kubernetes to schedule workloads onto GPUs, the NVIDIA device plugin is required.
```bash
helm repo add nvdp https://nvidia.github.io/k8s-device-plugin
helm repo update
helm install nvidia-device-plugin nvdp/nvidia-device-plugin \
    --namespace kube-system
```

---

## 3. Storage Setup

Triton needs access to your model repository. While a local `ConfigMap` or `emptyDir` can be used for testing, production environments should use an AWS S3 bucket or Amazon EFS.

### 3.1 Upload Model to S3 (Recommended)
1. Create an S3 bucket: `aws s3 mb s3://my-llm-model-repo`
2. Sync the local model repository to S3:
```bash
aws s3 sync ./triton/model_repository s3://my-llm-model-repo/
```
3. Update `kubernetes/deployment.yaml` to pull from S3. Modify the Triton command args:
```yaml
args: ["--model-repository=s3://my-llm-model-repo"]
```
*(Ensure the node group's IAM role has `s3:GetObject` and `s3:ListBucket` permissions).*

---

## 4. Deploying the Inference Stack

Once the cluster is up and storage is accessible, deploy the Triton inference server.

### 4.1 Apply Kubernetes Manifests
Navigate to the root of the repository and execute the deployment script:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```
Or apply manually:
```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml
```

### 4.2 Verify the Deployment
Check if the pods are running and the GPU is correctly attached:
```bash
kubectl get pods
kubectl logs -l app=llm-inference-server -c triton-server
```
Wait until you see: `Started GRPCInferenceService` and `Started HTTPService`.

---

## 5. Observability (Prometheus & Grafana)

To achieve the live dashboard functionality, we deploy the Prometheus stack.

### 5.1 Install Kube-Prometheus-Stack
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring --create-namespace
```

### 5.2 Configure PodMonitor for Triton
Tell Prometheus to scrape Triton metrics on port 8002. Create `triton-monitor.yaml`:
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: triton-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: llm-inference-server
  podMetricsEndpoints:
  - port: metrics
    path: /metrics
```
```bash
kubectl apply -f triton-monitor.yaml
```

### 5.3 Apply Alerts & Dashboard
Apply the Prometheus alert rules:
```bash
kubectl apply -f monitoring/prometheus-rules.yaml
```

To access Grafana:
```bash
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```
- Open `http://localhost:3000` (Default login: `admin` / `prom-operator`)
- Navigate to **Dashboards > Import** and upload the `monitoring/grafana-dashboard.json` file.

---

## 6. Testing & Benchmarking

Retrieve the external IP of your LoadBalancer:
```bash
kubectl get svc llm-inference-service
```
*(Wait until the `EXTERNAL-IP` is populated).*

Run the benchmark script against the live cluster:
```bash
# Install dependencies
pip install aiohttp

# Run load test
python scripts/benchmark.py --host <EXTERNAL-IP> --port 80 --model vllm_model --concurrency 50 --requests 1000
```

---

## 7. Next Steps for Production Hardening

- **TLS/SSL**: Add an AWS Application Load Balancer (ALB) Ingress controller and attach an ACM certificate.
- **Authentication**: Place an API Gateway (like Kong or AWS API Gateway) in front of the Triton service to manage API keys and rate-limiting.
- **Model Caching**: Implement a PVC (Persistent Volume Claim) with Amazon EFS for faster pod startup times compared to S3 pulls.
