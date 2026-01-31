FROM node:20-alpine

# Install build dependencies
RUN apk add --no-cache bash jq

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Copy run script
COPY run.sh /
RUN chmod +x /run.sh

# Set the entrypoint
ENTRYPOINT ["/run.sh"]
