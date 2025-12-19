# JupyterHub Multi-User GPU Environment

A production-ready JupyterHub setup with Docker, NVIDIA GPU support, and Nginx reverse proxy for secure multi-user access.

## 📁 Project Structure

```
jupyterhub-docker/
├── config/                     # Configuration files
│   ├── jupyterhub_config.py    # JupyterHub configuration
│   ├── nginx.conf              # Nginx reverse proxy config
│   └── users.txt               # Admin/user whitelist
├── data/                       # Persistent data (gitignored)
│   └── student-notebooks/      # Student work storage
├── docker/                     # Docker build files
│   └── Dockerfile              # JupyterHub container image
├── scripts/                    # Utility scripts
│   ├── setup.sh                # Initial setup script
│   ├── test-gpu.sh             # GPU availability test
│   └── manage-users.sh         # User management helper
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🏗️ Architecture

```
                    Internet / Local Network
                              │
                              ▼
                    ┌─────────────────┐
                    │  Nginx (:8000)  │  ◄── Reverse Proxy
                    │  WebSocket      │      (handles WS upgrade)
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   JupyterHub    │  ◄── Hub Container
                    │  (DockerSpawner)│
                    └────────┬────────┘
                             │ Spawns containers
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌────────────┐    ┌────────────┐    ┌────────────┐
    │  Student1  │    │  Student2  │    │  StudentN  │
    │  PyTorch   │    │  PyTorch   │    │  PyTorch   │
    │  + CUDA    │    │  + CUDA    │    │  + CUDA    │
    └────────────┘    └────────────┘    └────────────┘
           │                 │                 │
           └─────────────────┴─────────────────┘
                             │
                    ┌────────▼────────┐
                    │ data/student-   │  ◄── Persistent Storage
                    │ notebooks/      │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose**
2. **NVIDIA Container Toolkit** (for GPU support)
3. **NVIDIA GPU drivers**

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd jupyterhub-docker

# Copy environment template
cp .env.example .env

# Generate a secure key and add to .env
openssl rand -hex 32
# Edit .env and paste the key

# Create data directory
mkdir -p data/student-notebooks

# Build and start
docker compose up -d

# View logs
docker compose logs -f
```

### Access

- **Local**: `http://localhost:8000`
- **Network**: `http://<server-ip>:8000`
- **External**: Configure Cloudflare Tunnel to point to `http://<server-ip>:8000`

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
JUPYTERHUB_CRYPT_KEY=<generate-with-openssl-rand-hex-32>
DOCKER_NETWORK_NAME=jupyterhub-network
JUPYTERHUB_EXTERNAL_URL=https://your-domain.com
JUPYTERHUB_LOG_LEVEL=INFO
```

### Admin Users

Edit `config/users.txt` to manage admin users:

```
admin
instructor
```

### GPU Configuration

In `config/jupyterhub_config.py`:

```python
# All GPUs available to each user
'Count': -1

# Or limit to 1 GPU per user
'Count': 1

# Or specific GPU by ID
'DeviceIDs': ['0']
```

## 👥 User Management

### Admin Panel URLs

| URL | Purpose |
|-----|---------|
| `/hub/admin` | Admin dashboard |
| `/hub/authorize` | Approve pending signups |
| `/hub/signup` | Student registration |

### Using the Management Script

```bash
# List users
./scripts/manage-users.sh list

# Add a user
./scripts/manage-users.sh add student1

# View active servers
./scripts/manage-users.sh servers

# Stop a user's server
./scripts/manage-users.sh stop student1
```

## 🔧 Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# JupyterHub only
docker compose logs -f jupyterhub

# Nginx only
docker compose logs -f nginx
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart JupyterHub only
docker compose restart jupyterhub
```

### Update Images

```bash
docker compose pull
docker compose up -d --build
```

### Backup Student Data

```bash
tar -czf backup-$(date +%Y%m%d).tar.gz data/student-notebooks/
```

## 🧪 Testing GPU Access

```bash
./scripts/test-gpu.sh
```

Or inside a notebook:

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU: {torch.cuda.get_device_name(0)}")
```

## 🌐 External Access (Cloudflare Tunnel)

1. Create a tunnel in Cloudflare Zero Trust dashboard
2. Add public hostname pointing to `http://<server-ip>:8000`
3. Run cloudflared separately or add to your system services

## 📝 License

MIT License - Feel free to use and modify.
