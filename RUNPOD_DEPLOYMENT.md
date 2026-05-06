# RunPod Deployment Guide: LLM Inference Platform

This guide provides instructions for deploying the Triton + vLLM inference infrastructure on [RunPod](https://www.runpod.io/), a fast and cost-effective cloud GPU platform.

Deploying on RunPod is simpler than a full Kubernetes cluster and is ideal for early-stage production, testing, or endpoints that don't require complex orchestration.

---

## 1. Prerequisites

- A [RunPod account](https://www.runpod.io/) with billing set up.
- Your model repository uploaded to a cloud storage provider (like AWS S3, Google Cloud Storage, or Hugging Face) or prepared to be uploaded directly to the Pod via network volumes.
- For this guide, we assume you have your `model_repository` hosted in an S3 bucket or are ready to sync it.

---

## 2. Setting Up a RunPod GPU Pod

We will use a secure, single Pod instance to host the Triton Inference Server.

### 2.1 Select a GPU
1. Log in to your RunPod dashboard.
2. Go to **Pods** -> **Deploy**.
3. Select **Secure Cloud** (recommended for production) or **Community Cloud**.
4. Choose an appropriate GPU. For a 8B-parameter model like Llama-3, a single **RTX 3090 (24GB)**, **RTX 4090 (24GB)**, or **A10G (24GB)** is sufficient.

### 2.2 Configure the Pod Environment
In the deployment screen, customize your template:

- **Template**: Choose a base Docker image. You should provide the official Triton Server container with vLLM support:
  ```text
  nvcr.io/nvidia/tritonserver:24.03-vllm-python-py3
  ```
- **Container Disk**: Allocate at least **40 GB** to handle the Triton container size and intermediate downloads.
- **Volume Disk**: Allocate at least **50 GB** for the model weights.

### 2.3 Expose Ports
Triton Server requires several ports to be accessible. In the RunPod template settings, add the following to the **Exposed HTTP Ports**:
- `8000` (HTTP requests)
- `8001` (gRPC requests)
- `8002` (Metrics)

Make sure the ports are mapped as HTTP so you can query them externally.

### 2.4 Environment Variables
If your model requires pulling restricted weights from Hugging Face (e.g., Llama-3), you must provide your HF token.
Add an environment variable:
- `HF_TOKEN`: `your_hugging_face_access_token`

---

## 3. Launching and Configuring the Server

Once you click **Deploy**, wait for the Pod to initialize.

### 3.1 Connect to the Pod
1. Click **Connect** on your running Pod.
2. Open the **Web Terminal** or connect via SSH using the provided credentials.

### 3.2 Prepare the Model Repository
Once inside the terminal, create your directory structure and pull your model config.

```bash
# Move to the persistent volume workspace
cd /workspace

# Clone the inference repository
git clone https://github.com/Gershonbest/llm-inference.git
cd llm-inference/triton
```

If your actual model weights need to be downloaded, vLLM will handle this automatically upon startup based on the `meta-llama/Meta-Llama-3-8B` specified in `1/model.json`.

### 3.3 Start Triton Server
Run the Triton Server command exactly as we would in our Kubernetes deployment, but map the local directory:

```bash
tritonserver \
    --model-repository=/workspace/llm-inference/triton/model_repository \
    --log-verbose=1
```

*Note: Triton will take a few minutes to download the Llama-3 model weights from Hugging Face into its cache during the first startup.*

Wait until you see:
```text
I0506 14:23:45.123456 1 grpc_server.cc:2451] Started GRPCInferenceService at 0.0.0.0:8001
I0506 14:23:45.123567 1 http_server.cc:3558] Started HTTPService at 0.0.0.0:8000
I0506 14:23:45.167890 1 metrics.cc:864] Collecting metrics on port 8002
```

---

## 4. Querying Your Endpoint

To query your server from your local machine, you need the public URL provided by RunPod.

1. Go to your Pod's **Connect** screen.
2. Under **HTTP Service**, you will see URLs mapped to the ports you exposed (e.g., `https://<pod-id>-8000.proxy.runpod.net`).

Run the benchmark script locally against the RunPod URL:

```bash
# Important: Omit the http:// and ports, as RunPod proxies handle this via HTTPS
python scripts/benchmark.py \
    --host <pod-id>-8000.proxy.runpod.net \
    --port 443 \
    --model vllm_model \
    --concurrency 10 \
    --requests 100
```
*(You may need to modify the benchmark script slightly to use `https://` instead of `http://` for RunPod proxy endpoints).*

---

## 5. RunPod Serverless (Alternative to Pods)

If you only want to pay for exact compute time per request rather than maintaining an always-on Pod, you can wrap the Triton Server in a RunPod Serverless handler.

1. Create a custom Docker image that extends `nvcr.io/nvidia/tritonserver:24.03-vllm-python-py3`.
2. Add a simple Python script using `runpod.serverless.start()` that forwards incoming RunPod payload requests to the locally running Triton `localhost:8000` endpoint.
3. Push the image to Docker Hub or AWS ECR.
4. Deploy a new RunPod Serverless endpoint using your custom image.

*Note: Serverless environments suffer from "cold starts" (the time it takes to boot the container and load model weights into VRAM). Always-on Pods are highly recommended for low-latency LLM inference.*
