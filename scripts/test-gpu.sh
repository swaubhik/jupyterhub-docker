#!/bin/bash

# ============================================================================
# GPU Test Script
# ============================================================================
# This script tests if GPU passthrough is working in spawned containers

echo "Testing GPU availability in JupyterHub spawned containers..."
echo ""

# Run a test container with the same image and GPU config
docker run --rm --gpus all \
    --network jupyterhub-network \
    quay.io/jupyter/pytorch-notebook:cuda12-pytorch-2.5.1 \
    python -c "
import torch
print('=' * 70)
print('GPU Test Results')
print('=' * 70)
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'Number of GPUs: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'GPU {i}: {torch.cuda.get_device_name(i)}')
        props = torch.cuda.get_device_properties(i)
        print(f'  Memory: {props.total_memory / 1024**3:.2f} GB')
        print(f'  Compute Capability: {props.major}.{props.minor}')
    
    # Run a simple test
    device = torch.device('cuda')
    x = torch.rand(1000, 1000, device=device)
    y = torch.rand(1000, 1000, device=device)
    z = torch.matmul(x, y)
    print(f'\\nTest matrix multiplication: SUCCESS')
    print(f'Result shape: {z.shape}')
else:
    print('\\nERROR: CUDA is not available!')
    print('Check your NVIDIA Container Toolkit installation.')
print('=' * 70)
"

echo ""
echo "If you see GPU information above, GPU passthrough is working!"
echo "If not, check:"
echo "  1. NVIDIA drivers are installed: nvidia-smi"
echo "  2. NVIDIA Container Toolkit is installed"
echo "  3. Docker is configured for NVIDIA runtime"
