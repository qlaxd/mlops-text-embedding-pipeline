# Stage 1: Base
FROM python:3.11-slim AS base

# Ne fussunk root-ként
RUN addgroup --system app && adduser --system --group app
USER app
WORKDIR /app

# Python környezet beállításai
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Stage 2: Build
FROM base AS build

# Copy with correct ownership and install
# This ensures the user can write to the directory
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final
FROM base AS final

# Másoljuk a függőségeket
COPY --from=build /home/app/.local /home/app/.local
ENV PATH=/home/app/.local/bin:$PATH

# Másoljuk a forráskódot
COPY --chown=app:app . .

# Futtatás
CMD ["python", "src/main.py"]