
# LLM Inference Platform

> High-throughput, GPU-optimised LLM serving infrastructure using Triton Inference Server and vLLM — orchestrated with Kubernetes and monitored via Grafana.

![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=flat-square)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat-square&logo=kubernetes&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat-square&logo=amazonaws&logoColor=white)

---

## Overview

Most teams deploy LLMs behind a basic FastAPI wrapper and call it done. This platform goes further — building a proper inference infrastructure layer that handles GPU utilisation, request batching, concurrent load, and live observability, the same way production ML teams at scale do it.

**The problem it solves:** As LLM usage grows in production, naive serving approaches hit a wall fast — GPU underutilisation, high latency under load, zero visibility into what's happening. This platform addresses all three.

---

## Architecture

```
                        ┌─────────────────────────────────┐
                        │         API Gateway / LB         │
                        └────────────────┬────────────────┘
                                         │
                        ┌────────────────▼────────────────┐
                        │     Kubernetes Cluster (AWS)     │
                        │                                  │
                        │  ┌──────────┐  ┌─────────────┐  │
                        │  │  Triton   │  │    vLLM     │  │
                        │  │ Inference │  │   Server    │  │
                        │  │  Server  │  │             │  │
                        │  └──────────┘  └─────────────┘  │
                        │                                  │
                        │  ┌──────────────────────────┐   │
                        │  │     GPU Node Pool         │   │
                        │  │   (AWS EC2 G-instances)   │   │
                        │  └──────────────────────────┘   │
                        └────────────────┬────────────────┘
                                         │
                        ┌────────────────▼────────────────┐
                        │      Grafana Observability        │
                        │  Latency · Throughput · GPU Util  │
                        └─────────────────────────────────┘
```

---

## Key Features

- **Triton Inference Server** — dynamic batching, multi-model serving, GPU/CPU backend selection
- **vLLM** — PagedAttention for high-throughput LLM inference with continuous batching
- **Kubernetes orchestration** — horizontal pod autoscaling, GPU node pools, rolling updates
- **Live Grafana dashboard** — real-time metrics: request latency (p50/p95/p99), tokens/sec, GPU memory utilisation, queue depth
- **Multi-model support** — serve multiple LLMs simultaneously with isolated resource allocation
- **Health checks & auto-recovery** — liveness and readiness probes with automatic pod restart

---

## Tech Stack

| Layer | Technology |
|---|---|
| Inference Engine | NVIDIA Triton Inference Server |
| LLM Serving | vLLM (PagedAttention) |
| Orchestration | Kubernetes (AWS EKS) |
| GPU Compute | AWS EC2 G4dn / G5 instances |
| Observability | Grafana + Prometheus |
| Container Registry | AWS ECR |
| CI/CD | GitHub Actions |

---

## Performance Targets

| Metric | Target |
|---|---|
| p50 Latency (first token) | < 200ms |
| p95 Latency (first token) | < 500ms |
| Throughput | 500+ tokens/sec per GPU |
| GPU Utilisation | > 80% under load |

---

## Repository Structure

```
llm-inference-platform/
├── triton/
│   ├── model_repository/       # Triton model configs
│   └── config/                 # Server configuration
├── vllm/
│   └── serving_config.yaml     # vLLM serving setup
├── kubernetes/
│   ├── deployment.yaml         # Pod specs & GPU node selectors
│   ├── hpa.yaml                # Horizontal pod autoscaler
│   └── service.yaml            # Load balancer config
├── monitoring/
│   ├── grafana-dashboard.json  # Importable Grafana dashboard
│   └── prometheus-rules.yaml   # Alert rules
├── scripts/
│   ├── benchmark.py            # Load testing & benchmarking
│   └── deploy.sh               # Deployment helper
└── README.md
```

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Gershonbest/llm-inference
cd llm-inference-platform

# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Import Grafana dashboard
# Navigate to Grafana → Dashboards → Import → Upload monitoring/grafana-dashboard.json

# Run benchmark
python scripts/benchmark.py --model llama3 --concurrency 50 --requests 500
```

---

---

## Status

🟡 **In active development.** Core Triton and vLLM configurations are functional. Kubernetes manifests and Grafana dashboard in progress.
