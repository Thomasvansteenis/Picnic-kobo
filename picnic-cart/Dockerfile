FROM alpine:3.18

# Install requirements
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

# Copy application
COPY app.py .
COPY templates ./templates

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

# Expose port
EXPOSE 5000

# Run the application
CMD ["/run.sh"]
