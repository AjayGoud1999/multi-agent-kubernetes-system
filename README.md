# K8s AI Troubleshooter 🚀

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-grade **Multi-Agent Kubernetes Troubleshooting System** powered by AI. Upload your failing pod's logs, describe output, or deployment YAML and get instant root cause analysis with actionable fix steps.

![K8s AI Troubleshooter UI](docs/screenshot.png)

## ✨ Features

- **🤖 Multi-Agent Architecture** - Specialized AI agents work together:
  - **Log Analysis Agent** - Parses pod logs and kubectl describe output
  - **YAML Validation Agent** - Validates deployment configurations against best practices
  - **Root Cause Agent** - Synthesizes findings to determine the actual root cause
  
- **📚 RAG-Powered Knowledge** - Retrieves relevant Kubernetes documentation using FAISS vector store for context-aware analysis

- **🎯 Structured Output** - Returns:
  - Error category classification
  - Root cause explanation
  - Step-by-step fix instructions
  - Ready-to-run kubectl commands

- **🖥️ Modern Web UI** - React frontend with:
  - File upload support (drag & drop YAML, logs, etc.)
  - Real-time analysis with loading states
  - Copy-to-clipboard for kubectl commands
  - Expandable detailed analysis sections

- **🐳 Production Ready** - Async FastAPI, Docker support, proper error handling

## 🎬 Demo
https://github.com/AjayGoud1999/multi-agent-kubernetes-system/blob/master/demo-video.mp4

1. **Paste or upload** your `kubectl describe pod` output, pod logs, and deployment YAML
2. **Click Analyze** - AI agents process your inputs in parallel
3. **Get results** - Root cause, fix steps, and kubectl commands ready to run

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│                    POST /api/v1/analyze                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│              (Sequential Agent Coordination)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  Log Analysis │   │     YAML      │   │      RAG      │
│     Agent     │   │   Validation  │   │   Retriever   │
│               │   │     Agent     │   │               │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Root Cause Agent                             │
│            (Synthesizes all findings + RAG context)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Structured Response                           │
│   { error_category, root_cause, fix_steps, kubectl_commands }   │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, Pydantic |
| **Frontend** | React 18, Vite, TailwindCSS, Lucide Icons |
| **AI/ML** | OpenAI GPT-4, text-embedding-3-small |
| **Vector Store** | FAISS |
| **Deployment** | Docker, Docker Compose |

## 📁 Project Structure

```
k8s-ai-troubleshooter/
├── app/                          # Backend (FastAPI)
│   ├── main.py                   # Application entry point
│   ├── config.py                 # Configuration management
│   ├── api/
│   │   └── routes.py             # API endpoints
│   ├── agents/
│   │   ├── base_agent.py         # Abstract base agent
│   │   ├── log_agent.py          # Log analysis agent
│   │   ├── yaml_agent.py         # YAML validation agent
│   │   └── root_cause_agent.py   # Root cause synthesis
│   ├── rag/
│   │   ├── embeddings.py         # OpenAI embeddings
│   │   ├── vector_store.py       # FAISS vector store
│   │   └── retriever.py          # Document retrieval
│   ├── services/
│   │   └── orchestrator.py       # Agent orchestration
│   └── schemas/
│       └── models.py             # Pydantic models
├── frontend/                     # Frontend (React + Vite)
│   ├── src/
│   │   ├── App.jsx               # Main application
│   │   └── index.css             # TailwindCSS styles
│   ├── package.json
│   └── vite.config.js
├── data/
│   └── k8s_docs/                 # K8s docs for RAG
├── sample_data/                  # Sample test files
│   ├── describe_output.txt
│   ├── pod_logs.txt
│   └── deployment.yaml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend)
- OpenAI API key
- Docker (optional)

### Option 1: Full Stack (Backend + Frontend)

```bash
# 1. Clone and setup backend
cd k8s-ai-troubleshooter
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start backend (Terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Start frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

**Access the app:**
- 🖥️ **Web UI**: http://localhost:5173
- 📚 **API Docs**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/api/v1/health

### Option 2: Backend Only (API + Swagger UI)

```bash
# Setup
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your OPENAI_API_KEY

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access Swagger UI at http://localhost:8000/docs

### Option 3: Docker Deployment

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-api-key-here

# Build and start
docker-compose up --build
```

Or build manually:
```bash
docker build -t k8s-ai-troubleshooter .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key k8s-ai-troubleshooter
```

## 🧪 Testing with Sample Data

Sample test files are provided in `sample_data/`:

```bash
# Use the sample files in the Web UI or via curl:
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "describe_output": "'"$(cat sample_data/describe_output.txt)"'",
    "pod_logs": "'"$(cat sample_data/pod_logs.txt)"'",
    "deployment_yaml": "'"$(cat sample_data/deployment.yaml)"'"
  }'
```

The sample data contains an **ImagePullBackOff** error caused by a typo: `nginx:latests` instead of `nginx:latest`.

## 📡 API Usage

### Analyze Endpoint

**POST** `/api/v1/analyze`

#### Request Body

```json
{
  "describe_output": "Name: my-pod\nNamespace: default\nStatus: CrashLoopBackOff\n...",
  "pod_logs": "Error: connection refused to database at 10.0.0.5:5432\n...",
  "deployment_yaml": "apiVersion: apps/v1\nkind: Deployment\n..."
}
```

#### Response

```json
{
  "error_category": "CrashLoopBackOff",
  "root_cause": "Application cannot connect to database service",
  "explanation": "The pod is crashing because it cannot establish a connection to the database. The logs show connection refused errors to 10.0.0.5:5432, which indicates either the database service is not running or network policies are blocking the connection.",
  "fix_steps": [
    "Verify the database service is running: kubectl get svc -n default",
    "Check if the database pod is healthy: kubectl get pods -l app=database",
    "Verify network policies allow traffic: kubectl get networkpolicies",
    "Check the database connection string in the ConfigMap"
  ],
  "kubectl_commands": [
    "kubectl get svc -n default",
    "kubectl get pods -l app=database",
    "kubectl logs <database-pod-name>",
    "kubectl describe svc database"
  ],
  "log_analysis": {
    "error_category": "CrashLoopBackOff",
    "probable_cause": "Database connection failure",
    "supporting_log_lines": [
      "Error: connection refused to database at 10.0.0.5:5432"
    ],
    "confidence": 0.92
  },
  "yaml_validation": {
    "is_valid": true,
    "misconfigurations": [
      {
        "issue": "No resource limits defined",
        "severity": "medium",
        "recommendation": "Add resources.limits for CPU and memory",
        "field_path": "spec.containers[0].resources"
      }
    ],
    "confidence": 0.88
  },
  "confidence": 0.85,
  "rag_context_used": [
    "Kubernetes troubleshooting guide for CrashLoopBackOff..."
  ]
}
```

### Health Endpoint

**GET** `/api/v1/health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "openai_configured": true,
  "vector_store_ready": true
}
```

## Example Usage with curl

```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "describe_output": "Name: nginx-pod\nNamespace: default\nStatus: ImagePullBackOff\nEvents:\n  Warning  Failed  pull image \"nginx:latests\": not found",
    "pod_logs": "Error from server: container nginx is waiting to start: image can not be pulled",
    "deployment_yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: nginx\nspec:\n  replicas: 1\n  selector:\n    matchLabels:\n      app: nginx\n  template:\n    metadata:\n      labels:\n        app: nginx\n    spec:\n      containers:\n      - name: nginx\n        image: nginx:latests"
  }'
```

## ⚙️ Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | Model for analysis |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Model for embeddings |
| `OPENAI_MAX_TOKENS` | `4096` | Max tokens per request |
| `OPENAI_TEMPERATURE` | `0.1` | LLM temperature |
| `VECTOR_STORE_PATH` | `data/vector_store` | Path to FAISS index |
| `K8S_DOCS_PATH` | `data/k8s_docs` | Path to K8s docs |
| `CHUNK_SIZE` | `512` | Document chunk size |
| `TOP_K_RESULTS` | `3` | Number of RAG results |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DEBUG` | `false` | Enable debug mode |

## 📚 Adding Kubernetes Documentation for RAG

The RAG system enhances analysis by retrieving relevant Kubernetes documentation. To add your own:

1. Place `.txt` or `.md` files in `data/k8s_docs/`
2. Restart the backend server
3. Documents are automatically chunked, embedded, and indexed

**Recommended documentation to add:**
- Official Kubernetes troubleshooting guides
- Your organization's runbooks
- Common error patterns and solutions
- Best practices documentation

**Pre-included docs:**
- `troubleshooting_pods.txt` - CrashLoopBackOff, ImagePullBackOff guides
- `deployment_best_practices.txt` - Resource limits, probes, security
- `common_errors.txt` - Error patterns and solutions

## 🏷️ Error Categories

The system classifies errors into these categories:

| Category | Description |
|----------|-------------|
| `ImagePullError` | Image pull failures (wrong tag, private registry) |
| `CrashLoopBackOff` | Container crash loops |
| `OOMKilled` | Out of memory kills |
| `ResourceQuotaExceeded` | Resource quota issues |
| `ConfigurationError` | ConfigMap/Secret problems |
| `NetworkError` | Network connectivity issues |
| `VolumeError` | Volume mount failures |
| `PermissionError` | RBAC/permission issues |
| `ProbeFailure` | Liveness/readiness probe failures |
| `SchedulingError` | Pod scheduling issues |
| `Unknown` | Unclassified errors |

## 🔧 Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy app/

# Code formatting
black app/
isort app/

# Frontend development
cd frontend
npm run dev
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the Kubernetes community**
