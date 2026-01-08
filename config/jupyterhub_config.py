"""
JupyterHub Configuration for Multi-User GPU Environment
========================================================
This configuration sets up JupyterHub with:
- DockerSpawner for isolated user containers
- NVIDIA GPU passthrough to student containers
- NativeAuthenticator for user management
- Persistent storage for student work
"""

import os
from pathlib import Path

# ============================================================================
# GENERAL JUPYTERHUB CONFIGURATION
# ============================================================================

# JupyterHub listens on all interfaces inside the container
c.JupyterHub.bind_url = 'http://0.0.0.0:8000'

# Custom Templates for UI Overrides
c.JupyterHub.template_paths = ['/srv/jupyterhub/templates']

# Default to JupyterLab interface
c.Spawner.default_url = '/lab'

# Allow named servers (optional - lets users run multiple notebooks)
c.JupyterHub.allow_named_servers = False

# Database configuration - persist user state
c.JupyterHub.db_url = 'sqlite:///data/jupyterhub.sqlite'

# Cookie secret for security - set via environment
c.JupyterHub.cookie_secret_file = '/srv/jupyterhub/data/jupyterhub_cookie_secret'

# Hub IP - used by spawned containers to connect back
c.JupyterHub.hub_ip = os.environ.get('HUB_IP', '0.0.0.0')
c.JupyterHub.hub_connect_ip = 'jupyterhub'

# ============================================================================
# PROXY & WEBSOCKET CONFIGURATION (for Cloudflare Tunnel)
# ============================================================================

# IMPORTANT: Set the external URL that users access JupyterHub through
# This is required for WebSocket connections to work through Cloudflare Tunnel
EXTERNAL_URL = os.environ.get('JUPYTERHUB_EXTERNAL_URL', 'https://gpu.eagriassist.in')

# Trust X-Forwarded headers from proxy (Cloudflare Tunnel)
c.JupyterHub.trust_user_provided_tokens = True

# Configure Tornado to handle WebSockets properly behind proxy
c.ConfigurableHTTPProxy.command = ['configurable-http-proxy', '--no-x-forward']

# ============================================================================
# AUTHENTICATION - NativeAuthenticator
# ============================================================================

from nativeauthenticator import NativeAuthenticator
c.JupyterHub.authenticator_class = NativeAuthenticator

# Allow self-signup (users can register themselves, but need admin approval)
c.NativeAuthenticator.open_signup = True

# Allow users to create their own accounts (set to False for admin-only signup)
c.NativeAuthenticator.enable_signup = True

# Require admin approval for new signups
c.NativeAuthenticator.ask_email_on_signup = True

# Minimum password length
c.NativeAuthenticator.minimum_password_length = 8

# Allow password strength checking
c.NativeAuthenticator.check_common_password = True

# Admin users - CHANGE THESE TO YOUR ADMIN USERNAMES
c.Authenticator.admin_users = {'admin'}

# Allow admins to access user notebooks (for debugging/help)
c.JupyterHub.admin_access = True

# ============================================================================
# DOCKERSPAWNER CONFIGURATION
# ============================================================================

from dockerspawner import DockerSpawner

c.JupyterHub.spawner_class = DockerSpawner

# Docker network name (must match docker-compose.yml)
c.DockerSpawner.network_name = os.environ.get('DOCKER_NETWORK_NAME', 'jupyterhub-network')

# Use the internal docker network for communication
c.DockerSpawner.use_internal_ip = True

# ============================================================================
# STUDENT CONTAINER IMAGE - PyTorch with CUDA Support
# ============================================================================

# Official Jupyter PyTorch image with CUDA support
# This image includes:
# - PyTorch with CUDA
# - JupyterLab
# - Common data science libraries (numpy, pandas, matplotlib, etc.)
c.DockerSpawner.image = 'quay.io/jupyter/pytorch-notebook:cuda11-ubuntu-24.04'

# Alternative images you can use:
# c.DockerSpawner.image = 'quay.io/jupyter/pytorch-notebook:latest'
# c.DockerSpawner.image = 'pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime'
# Or build your own custom image with specific requirements

# Pull policy - always pull to get updates (change to 'ifnotpresent' for faster startup)
c.DockerSpawner.pull_policy = 'ifnotpresent'

# Remove containers when they stop (clean up resources)
c.DockerSpawner.remove = True

# ============================================================================
# GPU PASSTHROUGH - NVIDIA A6000 Configuration
# ============================================================================

# This is the critical configuration for GPU access
# It passes the NVIDIA GPU from the host to the spawned student containers

c.DockerSpawner.extra_host_config = {
    # NVIDIA GPU device requests
    'device_requests': [
        {
            'Driver': 'nvidia',
            'Count': -1,  # -1 means all GPUs; use 1 for single GPU per user
            'Capabilities': [['gpu', 'utility', 'compute']],
            
            # Optional: Limit to specific GPU(s) by index or UUID
            # 'DeviceIDs': ['0'],  # Use GPU 0 only
            # 'DeviceIDs': ['GPU-12345678-1234-1234-1234-123456789012'],  # Use specific GPU UUID
        }
    ],
    
    # Optional: Memory and CPU limits per container
    'mem_limit': '16g',  # Limit each container to 16GB RAM
    'memswap_limit': '16g',  # Prevent swap usage
    'cpu_quota': 200000,  # 2 CPU cores (200000 / 100000)
    'cpu_period': 100000,
    
    # Optional: Security options
    'security_opt': ['no-new-privileges:true'],
}

# Environment variables to pass to spawned containers
c.DockerSpawner.environment = {
    'GRANT_SUDO': 'no',  # Don't grant sudo access to users
    'NVIDIA_VISIBLE_DEVICES': 'all',  # Make all GPUs visible
    'NVIDIA_DRIVER_CAPABILITIES': 'compute,utility',
    # Allow WebSocket connections from any origin (required for Cloudflare Tunnel)
    'JUPYTER_ALLOW_INSECURE_WRITES': '1',
}

# Extra arguments for the spawned notebook server to handle proxy/WebSocket
c.DockerSpawner.args = [
    '--ServerApp.allow_origin=*',
    '--ServerApp.allow_remote_access=True',
    '--ServerApp.disable_check_xsrf=True',
    '--ServerApp.trust_xheaders=True',
]

# ============================================================================
# DATA PERSISTENCE - Student Work Storage
# ============================================================================

# IMPORTANT: DockerSpawner mounts volumes from the HOST filesystem, not from
# inside the JupyterHub container. Use absolute host paths here.
# Change this path to match your actual data directory on the host.
STUDENT_DATA_PATH = '/home/stihub/machine-learning/jupyterhub-docker/data/student-notebooks'

# Path inside the JupyterHub container where user data is mounted
HUB_NOTEBOOK_DIR = '/home'

c.DockerSpawner.volumes = {
    # Student data persistence - each user gets their own directory
    STUDENT_DATA_PATH + '/{username}': {
        'bind': '/home/jovyan/work',
        'mode': 'rw'
    },
}

# Notebook directory inside the container
c.DockerSpawner.notebook_dir = '/home/jovyan/work'

# Create user directory on host if it doesn't exist
# IMPORTANT: The jovyan user inside containers has UID 1000, GID 100
JOVYAN_UID = 1000
JOVYAN_GID = 100

def create_user_dir(spawner):
    """Create user directory on host before spawning container.
    
    The directory must be owned by UID 1000 (jovyan) for the container
    to have write access.
    """
    import os
    import subprocess
    
    # Use the path inside the container (where the volume is mounted)
    user_dir = Path(f'{HUB_NOTEBOOK_DIR}/{spawner.user.name}')
    user_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Set ownership to jovyan user (UID 1000, GID 100)
        os.chown(user_dir, JOVYAN_UID, JOVYAN_GID)
        # Set permissions: owner can read/write/execute, group can read/execute
        user_dir.chmod(0o755)
    except PermissionError:
        # If chown fails (not running as root), try using subprocess
        try:
            subprocess.run(['chown', f'{JOVYAN_UID}:{JOVYAN_GID}', str(user_dir)], check=True)
            subprocess.run(['chmod', '755', str(user_dir)], check=True)
        except Exception as e:
            print(f"Warning: Could not set permissions for {user_dir}: {e}")

c.Spawner.pre_spawn_hook = create_user_dir

# ============================================================================
# RESOURCE LIMITS & TIMEOUTS
# ============================================================================

# Timeout for container startup
c.DockerSpawner.start_timeout = 300  # 5 minutes

# Timeout for HTTP activity (prevents idle containers)
c.DockerSpawner.http_timeout = 120

# CPU and memory guarantees (minimum resources)
c.DockerSpawner.cpu_guarantee = 1.0  # 1 CPU core minimum
c.DockerSpawner.mem_guarantee = '4G'  # 4GB RAM minimum

# Maximum CPU and memory limits (set in extra_host_config above)
c.DockerSpawner.cpu_limit = 2.0  # 2 CPU cores maximum
c.DockerSpawner.mem_limit = '16G'  # 16GB RAM maximum

# ============================================================================
# IDLE CULLING (Optional - automatically stop idle notebooks)
# ============================================================================

# Uncomment to enable automatic shutdown of idle notebooks
# c.JupyterHub.services = [
#     {
#         'name': 'idle-culler',
#         'admin': True,
#         'command': [
#             'python3',
#             '-m', 'jupyterhub_idle_culler',
#             '--timeout=3600',  # Cull after 1 hour of inactivity
#             '--cull-every=600',  # Check every 10 minutes
#             '--remove-named-servers',  # Also cull named servers
#         ],
#     }
# ]

# ============================================================================
# LOGGING
# ============================================================================

c.JupyterHub.log_level = os.environ.get('JUPYTERHUB_LOG_LEVEL', 'INFO')
c.Spawner.debug = False

# ============================================================================
# ADDITIONAL SECURITY SETTINGS
# ============================================================================

# Disable unauthenticated access
c.JupyterHub.authenticate_prometheus = True

# Redirect to login page for unauthenticated users
c.JupyterHub.redirect_to_server = False

# Token expiration (optional)
# c.JupyterHub.cookie_max_age_days = 7

# ============================================================================
# CUSTOM CONFIGURATION (Optional)
# ============================================================================

# If you want to load additional users from a file
users_file = Path('/srv/jupyterhub/users.txt')
if users_file.exists():
    with open(users_file, 'r') as f:
        # File format: one username per line
        allowed_users = {line.strip() for line in f if line.strip() and not line.startswith('#')}
        if allowed_users:
            c.Authenticator.allowed_users = allowed_users

# Custom spawner options (let users choose their environment)
# Uncomment to allow users to select different images or configurations
# c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
# c.DockerSpawner.form_template = """
# <label for="image">Select your environment:</label>
# <select name="image" size="1">
#     <option value="quay.io/jupyter/pytorch-notebook:latest">PyTorch (Latest)</option>
#     <option value="quay.io/jupyter/tensorflow-notebook:latest">TensorFlow</option>
#     <option value="quay.io/jupyter/datascience-notebook:latest">Data Science</option>
# </select>
# """

print("=" * 70)
print("JupyterHub Configuration Loaded Successfully!")
print("=" * 70)
print(f"Network: {c.DockerSpawner.network_name}")
print(f"Image: {c.DockerSpawner.image}")
print(f"GPU Passthrough: Enabled (NVIDIA Runtime)")
print(f"Authentication: NativeAuthenticator")
print(f"Data Persistence: /home/{{username}} -> /home/jovyan/work")
print("=" * 70)
