# Picnic Kobo MCP Architecture

This project now uses a **Model Context Protocol (MCP) server** architecture for better separation of concerns, improved security, and enhanced maintainability.

## Architecture Overview

```
┌─────────────────────┐
│   Kobo E-Reader     │
│   (Web Browser)     │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────────────┐
│  Picnic Shopping Cart       │
│  (Flask Web App)            │
│  Port: 5000                 │
└──────────┬──────────────────┘
           │ HTTP/JSON
           ▼
┌─────────────────────────────┐
│  Picnic MCP Server          │
│  (Node.js/TypeScript)       │
│  Port: 3000                 │
└──────────┬──────────────────┘
           │ Official API
           ▼
┌─────────────────────────────┐
│  Picnic API                 │
│  (api.picnic.app)           │
└─────────────────────────────┘
```

## Components

### 1. Picnic MCP Server (Port 3000)
- **Technology**: Node.js, TypeScript, Model Context Protocol SDK
- **Purpose**: Centralized authentication and API communication with Picnic
- **Features**:
  - Handles authentication with Picnic API
  - Provides standardized MCP tools for cart operations
  - Session management
  - RESTful HTTP endpoints for tool invocation
  - Support for AI assistants and applications

### 2. Picnic Shopping Cart Web UI (Port 5000)
- **Technology**: Python, Flask
- **Purpose**: User-friendly web interface optimized for Kobo e-readers
- **Features**:
  - Product search interface
  - Shopping cart management
  - Responsive design for e-ink displays
  - Session-based user authentication
  - Communicates with MCP server via HTTP

## Benefits of MCP Architecture

### 1. **Separation of Concerns**
- Web UI focuses on presentation and user experience
- MCP server handles all Picnic API communication
- Clear boundaries between components

### 2. **Enhanced Security**
- Centralized credential management
- API credentials stored only in MCP server
- No direct credential handling in web interface

### 3. **Better Session Management**
- MCP server maintains persistent sessions with Picnic
- Reduces authentication overhead
- Prevents rate limiting issues

### 4. **Extensibility**
- MCP server can serve multiple clients:
  - Web interface
  - AI assistants (Claude, ChatGPT)
  - Automation scripts
  - Home Assistant integrations
  - Custom applications

### 5. **Improved Error Handling**
- Centralized error handling in MCP server
- Consistent error messages across clients
- Better debugging and logging

## Installation

### Prerequisites
- Home Assistant OS
- Access to Home Assistant Add-on Store

### Step 1: Install Picnic MCP Server

1. Add this repository to Home Assistant Add-ons
2. Install **Picnic MCP Server**
3. Configure in the add-on settings:
   ```yaml
   picnic_username: your.email@example.com
   picnic_password: your_password
   picnic_country: NL
   http_port: 3000
   http_host: 0.0.0.0
   ```
4. Start the MCP Server add-on
5. Verify it's running: http://homeassistant.local:3000/health

### Step 2: Install Picnic Shopping Cart

1. In the same add-on repository
2. Install **Picnic Shopping Cart**
3. Configure in the add-on settings:
   ```yaml
   flask_secret_key: your-random-secret-key-here
   mcp_server_url: http://localhost:3000
   ```
4. Start the Shopping Cart add-on
5. Access at: http://homeassistant.local:5000

### Step 3: Access from Kobo

1. Connect your Kobo to the same Wi-Fi network
2. Open the Kobo web browser
3. Navigate to: `http://YOUR_HA_IP:5000`
4. Login (credentials are only for session, authentication happens via MCP)

## Configuration

### MCP Server Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `picnic_username` | email | required | Your Picnic account email |
| `picnic_password` | password | required | Your Picnic password |
| `picnic_country` | list | NL | Country code (NL, DE, BE) |
| `http_port` | port | 3000 | HTTP server port |
| `http_host` | string | 0.0.0.0 | HTTP server host binding |

### Web UI Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `flask_secret_key` | string | required | Flask session secret (change from default!) |
| `mcp_server_url` | url | http://localhost:3000 | MCP server endpoint |

## MCP Server API

The MCP server exposes these HTTP endpoints:

### Health Check
```bash
curl http://localhost:3000/health
```

### List Available Tools
```bash
curl http://localhost:3000/tools
```

### Call a Tool
```bash
curl -X POST http://localhost:3000/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "search_products",
    "arguments": {
      "query": "milk"
    }
  }'
```

## Available MCP Tools

1. **search_products** - Search product catalog
2. **get_cart** - Get shopping cart contents
3. **add_to_cart** - Add product to cart
4. **remove_from_cart** - Remove product from cart
5. **clear_cart** - Clear entire cart
6. **get_user** - Get user account info
7. **get_deliveries** - Get delivery schedules
8. **get_lists** - Get shopping lists
9. **get_categories** - Get product categories

## Development

### Local Development

#### MCP Server
```bash
cd picnic-mcp-server
npm install
npm run build

# Set environment variables
export PICNIC_USERNAME=your@email.com
export PICNIC_PASSWORD=yourpassword
export PICNIC_COUNTRY_CODE=NL
export ENABLE_HTTP_SERVER=true
export HTTP_PORT=3000

npm start
```

#### Web UI
```bash
cd picnic-cart

# Create .env file
cat > .env << EOF
FLASK_SECRET_KEY=dev-secret-key
MCP_SERVER_URL=http://localhost:3000
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF

pip install -r requirements.txt
python app.py
```

## Troubleshooting

### Web UI can't connect to MCP server

**Symptoms**: "Cannot connect to Picnic service" error

**Solutions**:
1. Check MCP server is running:
   ```bash
   curl http://localhost:3000/health
   ```
2. Verify `mcp_server_url` in web UI configuration
3. Check Home Assistant logs for MCP server errors:
   ```bash
   docker logs addon_picnic-mcp-server
   ```

### Authentication errors

**Symptoms**: Login fails or cart operations fail

**Solutions**:
1. Verify credentials in MCP server configuration
2. Check MCP server logs for authentication errors
3. Test Picnic credentials in official app
4. Ensure country code matches your account

### Port conflicts

**Symptoms**: Add-ons won't start

**Solutions**:
1. Check if ports 3000 or 5000 are already in use
2. Change ports in add-on configuration if needed
3. Update `mcp_server_url` in web UI if MCP port changes

## Migration from v2.x

If you're upgrading from version 2.x (direct Picnic API):

1. **Install MCP Server** first (see Step 1 above)
2. **Configure MCP Server** with your Picnic credentials
3. **Update Web UI** addon to v3.0.0
4. **Configure Web UI** to point to MCP server
5. **Restart both addons**

Your existing web UI configuration will be preserved, but you'll need to add the `mcp_server_url` option.

## Credits

- Based on [mcp-picnic](https://github.com/ivo-toby/mcp-picnic) by ivo-toby
- Model Context Protocol by [Anthropic](https://www.anthropic.com)
- Picnic API integration via [picnic-api](https://www.npmjs.com/package/picnic-api)

## License

MIT License - See LICENSE file for details
