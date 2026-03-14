# =============================================================================
# ERB (Effortlessly Invariant Rulesbooks) Docker Image
# =============================================================================
# Complete environment for running the ERB stack with all substrates.
# Includes: Python, PostgreSQL client, .NET (for ssotme), Go, Node.js
# =============================================================================

FROM python:3.11-slim-bookworm

LABEL maintainer="ERB Project"
LABEL description="Effortlessly Invariant Rulesbooks - Complete Stack"

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# =============================================================================
# Install system dependencies
# =============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client
    postgresql-client \
    # Build essentials
    build-essential \
    curl \
    wget \
    git \
    # Calculator (used by orchestration scripts)
    bc \
    # For https and package management
    apt-transport-https \
    ca-certificates \
    gnupg \
    # For .NET (ICU for globalization)
    libicu72 \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Install .NET 8 SDK (required by ssotme npm package)
# =============================================================================
RUN curl -sSL https://dot.net/v1/dotnet-install.sh -o dotnet-install.sh \
    && chmod +x dotnet-install.sh \
    && ./dotnet-install.sh --channel 8.0 --install-dir /usr/share/dotnet \
    && ln -s /usr/share/dotnet/dotnet /usr/bin/dotnet \
    && rm dotnet-install.sh

ENV DOTNET_ROOT=/usr/share/dotnet
ENV PATH="${PATH}:/usr/share/dotnet"

# =============================================================================
# Install Node.js 20 (for ssotme CLI and report generation)
# =============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Install ssotme CLI from npm
# =============================================================================
RUN npm install -g ssotme

# =============================================================================
# Install Go (for Go substrate) - detect architecture
# =============================================================================
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then \
        GO_ARCH="arm64"; \
    else \
        GO_ARCH="amd64"; \
    fi && \
    curl -fsSL "https://go.dev/dl/go1.21.13.linux-${GO_ARCH}.tar.gz" | tar -C /usr/local -xzf -

ENV PATH="${PATH}:/usr/local/go/bin"

# =============================================================================
# Install Python dependencies
# =============================================================================
RUN pip install --no-cache-dir \
    psycopg2-binary \
    pyyaml \
    rdflib \
    openpyxl

# =============================================================================
# Set up working directory
# =============================================================================
WORKDIR /app

# Copy the entire project
COPY . .

# Make scripts executable
RUN chmod +x orchestration/orchestrate.sh \
    && chmod +x postgres/init-db.sh \
    && chmod +x run-in-docker.sh 2>/dev/null || true

# =============================================================================
# Environment variables
# =============================================================================
# Default database URL (connects to docker-compose postgres service)
ENV DATABASE_URL=postgresql://postgres:postgres@postgres:5432/erb

# Disable interactive prompts in ssotme
ENV SSOTME_NONINTERACTIVE=1

# =============================================================================
# Entry point
# =============================================================================
CMD ["bash", "orchestration/orchestrate.sh"]
