#!/usr/bin/env python3
"""
Test script for the K8s AI Troubleshooter API.
Run the server first: uvicorn app.main:app --reload
Then run this script: python test_api.py
"""

import httpx
import json

BASE_URL = "http://localhost:8000"

# Sample test data simulating a CrashLoopBackOff scenario
TEST_REQUEST = {
    "describe_output": """Name:         nginx-deployment-5d4c4b8c9-x7z2k
Namespace:    default
Priority:     0
Node:         worker-node-1/10.0.0.5
Start Time:   Mon, 25 Feb 2026 10:00:00 -0800
Labels:       app=nginx
              pod-template-hash=5d4c4b8c9
Status:       Running
IP:           10.244.1.15
Containers:
  nginx:
    Container ID:   containerd://abc123
    Image:          nginx:latests
    Image ID:       
    Port:           80/TCP
    State:          Waiting
      Reason:       ImagePullBackOff
    Last State:     Terminated
      Reason:       Error
      Exit Code:    1
    Ready:          False
    Restart Count:  5
Events:
  Type     Reason     Age                From               Message
  ----     ------     ----               ----               -------
  Normal   Scheduled  5m                 default-scheduler  Successfully assigned default/nginx-deployment-5d4c4b8c9-x7z2k to worker-node-1
  Normal   Pulling    4m (x4 over 5m)    kubelet            Pulling image "nginx:latests"
  Warning  Failed     4m (x4 over 5m)    kubelet            Failed to pull image "nginx:latests": rpc error: code = NotFound desc = failed to pull and unpack image "docker.io/library/nginx:latests": failed to resolve reference "docker.io/library/nginx:latests": docker.io/library/nginx:latests: not found
  Warning  Failed     4m (x4 over 5m)    kubelet            Error: ErrImagePull
  Warning  Failed     3m (x6 over 5m)    kubelet            Error: ImagePullBackOff
  Normal   BackOff    30s (x20 over 5m)  kubelet            Back-off pulling image "nginx:latests"
""",
    "pod_logs": """Error from server (BadRequest): container "nginx" in pod "nginx-deployment-5d4c4b8c9-x7z2k" is waiting to start: image can't be pulled
""",
    "deployment_yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latests
        ports:
        - containerPort: 80
"""
}


def test_health():
    """Test the health endpoint."""
    print("=" * 60)
    print("Testing Health Endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/api/v1/health", timeout=10.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except httpx.ConnectError:
        print("ERROR: Cannot connect to server. Is it running?")
        print("Start the server with: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_analyze():
    """Test the analyze endpoint."""
    print("\n" + "=" * 60)
    print("Testing Analyze Endpoint")
    print("=" * 60)
    
    try:
        print("Sending analysis request (this may take 10-30 seconds)...")
        response = httpx.post(
            f"{BASE_URL}/api/v1/analyze",
            json=TEST_REQUEST,
            timeout=120.0  # LLM calls can take time
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n--- Analysis Results ---")
            print(f"Error Category: {result['error_category']}")
            print(f"Root Cause: {result['root_cause']}")
            print(f"Confidence: {result['confidence']:.2%}")
            print(f"\nExplanation:\n{result['explanation']}")
            print(f"\nFix Steps:")
            for i, step in enumerate(result['fix_steps'], 1):
                print(f"  {i}. {step}")
            print(f"\nSuggested kubectl commands:")
            for cmd in result['kubectl_commands']:
                print(f"  $ {cmd}")
            print(f"\nLog Analysis Confidence: {result['log_analysis']['confidence']:.2%}")
            print(f"YAML Validation Issues: {len(result['yaml_validation']['misconfigurations'])}")
            
            if result['yaml_validation']['misconfigurations']:
                print("\nYAML Issues Found:")
                for issue in result['yaml_validation']['misconfigurations']:
                    print(f"  - [{issue['severity']}] {issue['issue']}")
            
            return True
        else:
            print(f"Error Response: {json.dumps(response.json(), indent=2)}")
            return False
            
    except httpx.ConnectError:
        print("ERROR: Cannot connect to server. Is it running?")
        return False
    except httpx.ReadTimeout:
        print("ERROR: Request timed out. The LLM may be taking too long.")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_root_endpoint():
    """Test the root endpoint."""
    print("\n" + "=" * 60)
    print("Testing Root Endpoint")
    print("=" * 60)
    
    try:
        response = httpx.get(f"{BASE_URL}/", timeout=10.0)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    print("\n🔧 K8s AI Troubleshooter - API Test Suite\n")
    
    # Test health first
    if not test_health():
        print("\n❌ Health check failed. Ensure the server is running.")
        print("\nTo start the server:")
        print("  1. cd k8s-ai-troubleshooter")
        print("  2. cp .env.example .env")
        print("  3. Edit .env and add your OPENAI_API_KEY")
        print("  4. pip install -r requirements.txt")
        print("  5. uvicorn app.main:app --reload")
        exit(1)
    
    # Test root
    test_root_endpoint()
    
    # Test analyze
    print("\n⏳ Running analysis test (requires OpenAI API)...")
    if test_analyze():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Analysis test failed. Check your OPENAI_API_KEY.")
