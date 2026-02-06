FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install system dependencies for SUMO (if needed here, or in a separate container? The architecture shows Traffic Simulation SUMO. Often SUMO needs to be installed. The prompt says "Install and configure SUMO" in Phase 1. 
# Installing SUMO in the backend container allows TraCI to interact with it directly if they are in the same environment, or we use a separate SUMO container.
# Given the prompt "TraCI - SUMO Python interface for control", it's easiest if SUMO is in the same container.
# So I will install SUMO here.

RUN apt-get update && apt-get install -y \
    sumo \
    sumo-tools \
    sumo-doc \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
