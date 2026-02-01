# ==============================================================================
# Stage 1: Build React Frontend
# ==============================================================================
FROM node:20-alpine AS frontend-builder

# Cache-busting argument - change this value to force rebuild
ARG CACHEBUST=1

WORKDIR /frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Invalidate cache for source files copy
ARG CACHEBUST
RUN echo "Cache bust: $CACHEBUST"

# Copy source files
COPY frontend/ ./

# Build for production
RUN npm run build

# ==============================================================================
# Stage 2: Python Runtime
# ==============================================================================
FROM alpine:3.18

# Install requirements (PyMySQL is pure Python, no native deps needed)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    bash

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates ./templates
COPY api ./api
COPY services ./services
COPY migrations ./migrations

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose port
EXPOSE 5000

# Run the application
CMD ["/run.sh"]
