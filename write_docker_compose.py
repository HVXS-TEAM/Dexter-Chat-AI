# Script to regenerate docker-compose.yml with proper UTF-8 encoding
import os
import yaml
from pathlib import Path

# Get the current directory (which is the Dexter project root)
base_dir = Path.cwd()

# Define the docker-compose content
docker_compose_content = """
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: dexter_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-dexter}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dexter_dev}
      POSTGRES_DB: ${DB_NAME:-dexter}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-dexter} -d ${DB_NAME:-dexter}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: dexter_backend
    restart: unless-stopped
    env_file:
      - .env.docker
    environment:
      DB_URL: postgresql+psycopg2://${DB_USER:-dexter}:${DB_PASSWORD:-dexter_dev}@postgres:5432/${DB_NAME:-dexter}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
    # Volume removed for Docker build compatibility
    # - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: dexter_frontend
    restart: unless-stopped
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      VITE_API_URL: http://localhost:8000
    command: npm run dev -- --host 0.0.0.0

volumes:
  postgres_data:
"""

# Write the file with UTF-8 encoding
docker_compose_path = base_dir / 'docker-compose.yml'
docker_compose_path.write_text(docker_compose_content.strip(), encoding='utf-8')

print(f"docker-compose.yml written successfully to {docker_compose_path}")
