# Stage 1: Build - This stage installs dependencies into a virtual environment
FROM python:3.11-slim AS build

# Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final - This stage creates the final, lean image
FROM python:3.11-slim AS final

# Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set pipeline version from build argument
ARG PIPELINE_VERSION=unknown
ENV PIPELINE_VERSION=$PIPELINE_VERSION

# Create a non-root user
RUN addgroup --system app && adduser --system --group app

# Copy the virtual environment from the build stage
COPY --from=build /opt/venv /opt/venv

# Copy the application code
WORKDIR /app
COPY . .

# Set ownership of the app directory to the new user
RUN chown -R app:app /app

# Activate the virtual environment by adding it to the PATH
ENV PATH="/opt/venv/bin:$PATH"

# Switch to the non-root user
USER app

# Futtatás
CMD ["python", "-m", "src.main"]
