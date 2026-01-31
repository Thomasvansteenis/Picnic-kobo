# Picnic MCP Server - Home Assistant Add-on

Model Context Protocol (MCP) server for Picnic grocery delivery service. This add-on enables AI assistants and applications to interact with your Picnic account through a standardized API.

## Features

- **Product Search**: Search Picnic's product catalog
- **Cart Management**: Add, remove, and view items in your shopping cart
- **Delivery Information**: Check delivery slots and schedules
- **Account Details**: Access user profile and order history
- **Category Browsing**: Explore product categories
- **Shopping Lists**: Manage your shopping lists

## Installation

1. Add this repository to your Home Assistant Add-on Store
2. Install the "Picnic MCP Server" add-on
3. Configure your Picnic credentials in the add-on configuration
4. Start the add-on

## Configuration

```yaml
picnic_username: your.email@example.com
picnic_password: your_password
picnic_country: NL  # Options: NL, DE, BE
http_port: 3000
http_host: 0.0.0.0
```

### Options

- **picnic_username** (required): Your Picnic account email
- **picnic_password** (required): Your Picnic account password
- **picnic_country** (optional): Country code - NL (Netherlands), DE (Germany), or BE (Belgium). Default: NL
- **http_port** (optional): Port for the HTTP API server. Default: 3000
- **http_host** (optional): Host binding for the HTTP server. Default: 0.0.0.0

## API Endpoints

Once running, the MCP server exposes these HTTP endpoints:

### Health Check
```
GET http://homeassistant.local:3000/health
```

### List Available Tools
```
GET http://homeassistant.local:3000/tools
```

### Call a Tool
```
POST http://homeassistant.local:3000/call-tool
Content-Type: application/json

{
  "name": "search_products",
  "arguments": {
    "query": "milk"
  }
}
```

## Available Tools

### search_products
Search for products in the Picnic catalog.

**Arguments:**
- `query` (string): Search query for products

**Example:**
```json
{
  "name": "search_products",
  "arguments": { "query": "organic milk" }
}
```

### get_cart
Get the current shopping cart contents with all items and total price.

**Arguments:** None

**Example:**
```json
{
  "name": "get_cart",
  "arguments": {}
}
```

### add_to_cart
Add a product to the shopping cart.

**Arguments:**
- `productId` (string): Product ID to add
- `count` (number, optional): Quantity to add (default: 1)

**Example:**
```json
{
  "name": "add_to_cart",
  "arguments": {
    "productId": "10420042",
    "count": 2
  }
}
```

### remove_from_cart
Remove a product from the shopping cart.

**Arguments:**
- `productId` (string): Product ID to remove
- `count` (number, optional): Quantity to remove (default: 1)

**Example:**
```json
{
  "name": "remove_from_cart",
  "arguments": {
    "productId": "10420042",
    "count": 1
  }
}
```

### clear_cart
Remove all items from the shopping cart.

**Arguments:** None

**Example:**
```json
{
  "name": "clear_cart",
  "arguments": {}
}
```

### get_user
Get user account information.

**Arguments:** None

### get_deliveries
Get delivery slots and scheduled deliveries.

**Arguments:** None

### get_lists
Get user's shopping lists.

**Arguments:** None

### get_categories
Get product categories and subcategories.

**Arguments:** None

## Integration with Picnic Cart Web UI

The Picnic Shopping Cart add-on can be configured to use this MCP server instead of directly authenticating with Picnic. This provides:

- Centralized authentication
- Better session management
- Consistent API across multiple clients

See the Picnic Shopping Cart add-on documentation for configuration details.

## Support

For issues and feature requests, visit: https://github.com/Thomasvansteenis/Picnic-kobo

## Credits

Based on [mcp-picnic](https://github.com/ivo-toby/mcp-picnic) by ivo-toby.

## License

MIT
