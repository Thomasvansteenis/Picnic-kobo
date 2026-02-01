# ==============================================================================
# Stage 1: Build React Frontend
# ==============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source files
COPY frontend/ ./

# Build for production
RUN npm run build

# ==============================================================================
# Stage 2: Python Runtime
# ==============================================================================
FROM alpine:3.18

# Install requirements including PostgreSQL client libs
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq \
    bash \
    libpq \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev

# Upgrade pip
RUN pip3 install --no-cache-dir --upgrade pip

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del gcc python3-dev musl-dev postgresql-dev libffi-dev

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
