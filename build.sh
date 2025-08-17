#!/bin/bash

# Build script for MLOps Text Embedding Pipeline
# Automatically sets the pipeline version from git commit hash

set -e

echo "Building MLOps Text Embedding Pipeline Docker image..."

# Get the current git commit hash
if command -v git &> /dev/null; then
    PIPELINE_VERSION=$(git rev-parse HEAD)
    echo "Using Git commit hash as pipeline version: ${PIPELINE_VERSION:0:8}..."
else
    PIPELINE_VERSION="unknown"
    echo "Git not available, using 'unknown' as pipeline version"
fi

# Build the Docker image with the pipeline version
docker build \
    --build-arg PIPELINE_VERSION="$PIPELINE_VERSION" \
    -t mlops-text-embedding-pipeline:latest \
    .

echo "Build completed successfully!"
echo "Image tagged as: mlops-text-embedding-pipeline:latest"
echo "Pipeline version: $PIPELINE_VERSION"
