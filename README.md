# Picnic Shopping Cart - Home Assistant Add-on Repository

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FThomasvansteenis%2FPicnic-kobo)

Home Assistant add-on repository for the Picnic Shopping Cart application.

## About

This repository contains Home Assistant add-ons for managing your Picnic grocery shopping cart from your Kobo e-reader or any web browser. The project uses a **Model Context Protocol (MCP)** architecture for better security, maintainability, and extensibility.

### Available Add-ons

- **Picnic MCP Server** (v1.0.0) - Model Context Protocol server for Picnic API communication
- **Picnic Shopping Cart** (v3.0.0) - E-ink optimized web interface for Picnic grocery delivery service

### New in v3.0: MCP Architecture

The application now uses a two-component architecture:
1. **MCP Server**: Handles all Picnic API communication and authentication
2. **Web UI**: Provides the user interface for Kobo e-readers and browsers

[📚 Read the full MCP Architecture documentation](MCP_ARCHITECTURE.md)

## Installation

### Quick Start

Both add-ons must be installed for the system to work:

**Step 1: Add the Repository**

Click this button to add the repository to your Home Assistant:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FThomasvansteenis%2FPicnic-kobo)

**Step 2: Install Picnic MCP Server**

1. Click on "Picnic MCP Server"
2. Click "Install"
3. Configure with your Picnic credentials:
   - Email address
   - Password
   - Country (NL/DE/BE)
4. Click "Start"
5. Wait for it to show as "Running"

**Step 3: Install Picnic Shopping Cart**

1. Click on "Picnic Shopping Cart"
2. Click "Install"
3. Configure:
   - Set a strong `flask_secret_key` (generate one with the command below)
   - MCP server URL defaults to `http://localhost:3000` (usually correct)
4. Click "Start"

### Method 2: Manual Repository Addition

1. Open your Home Assistant instance
2. Navigate to **Settings** → **Add-ons**
3. Click the **Add-on Store** tab
4. Click the **⋮** (three dots) in the top right corner
5. Select **Repositories**
6. Add this URL: `https://github.com/Thomasvansteenis/Picnic-kobo`
7. Click **Add**
8. Refresh the add-on store page
9. Find **"Picnic Shopping Cart"** in the list
10. Click on it and then click **Install**

## Configuration

After installation, configure the add-on:

1. Go to the **Configuration** tab
2. Set your `flask_secret_key` to a random string (minimum 32 characters)

   Generate one with:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Click **Save**
4. Go to the **Info** tab
5. Enable **Start on boot** (recommended)
6. Click **Start**

## Usage

### Accessing the Web Interface

After the add-on starts:
1. Click **Open Web UI** in the add-on page, OR
2. Navigate to `http://homeassistant.local:5000`, OR
3. Use your Home Assistant IP: `http://YOUR_HA_IP:5000`

### Login

Use your Picnic account credentials:
- **Email**: Your Picnic account email
- **Password**: Your Picnic password
- **Country**: NL (Netherlands), DE (Germany), or BE (Belgium)

### Using from Kobo E-reader

1. Connect your Kobo to the same WiFi network as Home Assistant
2. Open the Kobo web browser
3. Navigate to `http://YOUR_HA_IP:5000`
4. Login and start shopping!

The interface is optimized for e-ink displays with high contrast and simple design.

## Add to Home Assistant Sidebar (Optional)

Add this to your `configuration.yaml`:

```yaml
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

Then restart Home Assistant.

## Support

For issues, questions, or feature requests:
- [GitHub Issues](https://github.com/Thomasvansteenis/Picnic-kobo/issues)

## Features

- 🛒 Search Picnic grocery catalog
- 📦 Add/remove items from cart
- 🖥️ E-ink optimized interface
- 📱 Works on Kobo e-readers
- 🔒 Secure session-based authentication
- 🏠 Easy Home Assistant integration

## Disclaimer

This is an unofficial add-on and is not affiliated with, endorsed by, or connected to Picnic or Home Assistant. Use at your own risk.

## Credits

- Built with [Flask](https://flask.palletsprojects.com/) (Web UI) and [Node.js](https://nodejs.org/) (MCP Server)
- MCP Server based on [mcp-picnic](https://github.com/ivo-toby/mcp-picnic) by ivo-toby
- Uses [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- Picnic API integration via [picnic-api](https://www.npmjs.com/package/picnic-api) npm package
- Optimized for Kobo e-readers and e-ink displays

## License

MIT License - See [LICENSE](LICENSE) file for details
