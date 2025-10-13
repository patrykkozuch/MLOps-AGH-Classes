# Use a minimal Python image as the base
FROM python:3.12.8-slim

# Set the working directory in the container
WORKDIR /app

# Install uv from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

# Copy only dependency files first (to leverage caching)
COPY pyproject.toml uv.lock ./

# Install project dependencies using uv
RUN uv sync --no-dev

# Copy the rest of the application code
COPY lab lab
COPY models models

# Expose the application port
EXPOSE 8000

# Run the application with uv
CMD ["uv", "run", "uvicorn", "lab.app:app", "--host", "0.0.0.0", "--port", "8000"]