# Use a minimal Python image as the base
FROM python:3.13-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Install uv from the official Astral image
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

# Copy only dependency files first (to leverage caching)
COPY pyproject.toml uv.lock .python-version ./

# Install project dependencies using uv
RUN uv sync --no-dev

# Copy the rest of the application code
COPY sa sa
COPY models models

# Expose the application port
EXPOSE 8000

# Run the application with uv
CMD ["uv", "run", "--no-dev", "uvicorn", "sa.app:app", "--host", "0.0.0.0", "--port", "8000"]