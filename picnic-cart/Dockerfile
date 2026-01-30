# Use Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    && pip3 install --no-cache-dir --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates ./templates
COPY run.sh /

# Make run script executable
RUN chmod a+x /run.sh

# Expose port
EXPOSE 5000

# Run the add-on
CMD ["/run.sh"]
