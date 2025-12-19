# JupyterHub with DockerSpawner and NativeAuthenticator
# This image runs the JupyterHub hub itself (not the student containers)

FROM jupyterhub/jupyterhub

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install DockerSpawner and NativeAuthenticator
RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator \
    jupyterhub-idle-culler

# Create necessary directories
RUN mkdir -p /srv/jupyterhub/data && \
    chmod 755 /srv/jupyterhub/data

# Set working directory
WORKDIR /srv/jupyterhub

# Expose JupyterHub port
EXPOSE 8000

# Default command (can be overridden in docker-compose.yml)
CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
