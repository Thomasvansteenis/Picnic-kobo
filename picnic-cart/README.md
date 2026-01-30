# Picnic Kobo Shopping Cart

A simple, e-ink optimized web application for managing your Picnic grocery shopping cart from your Kobo e-reader or any device. Designed to run on your local Home Assistant server or any other server.

## Features

- **E-ink Optimized UI**: High contrast, simple black and white interface perfect for e-readers
- **Product Search**: Search for groceries in the Picnic catalog
- **Cart Management**: Add, remove, and view items in your shopping cart
- **Session-based Authentication**: Secure login with session management
- **Lightweight**: Minimal JavaScript, works on devices with limited browser capabilities
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Prerequisites

- Home Assistant (for add-on installation)
- OR Python 3.11+ / Docker (for standalone deployment)
- A Picnic account (Netherlands, Germany, or Belgium)

## Installation

### Option 1: Home Assistant Add-on (Recommended ⭐)

The easiest way to install is as a Home Assistant add-on:

1. Open Home Assistant → **Settings** → **Add-ons**
2. Enable **Advanced Mode** in your user profile if not already enabled
3. Install **Terminal & SSH** add-on (if not installed)
4. Open Terminal and run:
   ```bash
   cd /addons
   mkdir -p picnic-cart
   cd picnic-cart
   ```
5. Copy all files from this repository to `/addons/picnic-cart/`
6. Make the run script executable:
   ```bash
   chmod +x run.sh
   ```
7. Go back to **Settings** → **Add-ons**
8. Click **⋮** (three dots) → **Reload**
9. Find **"Picnic Shopping Cart"** in the local add-ons
10. Click **Install**
11. Configure the `flask_secret_key` in the Configuration tab
12. Click **Start**
13. Click **Open Web UI** to access the app

**📖 See [ADDON_INSTALL.md](ADDON_INSTALL.md) for detailed step-by-step instructions.**

### Option 2: Standalone Python Deployment

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd Picnic-kobo
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Create a `.env` file:
   ```bash
   cp .env.example .env
   # Edit with your settings
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Access the application at `http://localhost:5000`

## Usage

### On Your Kobo E-reader

1. Connect your Kobo to WiFi
2. Open the built-in web browser
3. Navigate to `http://your-server-ip:5000`
4. Login with your Picnic credentials
5. Search for products and add them to your cart
6. Complete your order using the official Picnic mobile app

### Login

- **Email**: Your Picnic account email
- **Password**: Your Picnic password
- **Country**: Select NL (Netherlands), DE (Germany), or BE (Belgium)

Note: Credentials are stored only in your session and are not saved permanently.

### Searching for Products

1. Click "Search" in the navigation
2. Enter product name (e.g., "milk", "bread", "tomatoes")
3. Browse results and click "Add to Cart" to add items
4. Adjust quantity before adding if needed

### Managing Your Cart

1. Click "Cart" in the navigation
2. View all items in your cart
3. Remove items or adjust quantities
4. Use "Clear Cart" to empty the entire cart

### Completing Your Order

This application only manages your cart. To complete your order:
1. Open the official Picnic mobile app or website
2. Your cart will be synchronized
3. Select delivery slot and complete checkout

## Adding to Home Assistant Dashboard (Optional)

If you installed as a Home Assistant add-on, you can add it to your sidebar:

```yaml
# configuration.yaml
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

Then restart Home Assistant to see it in the sidebar.

## Security Notes

- This application uses the unofficial Picnic API
- Credentials are stored in session cookies (not saved to disk)
- Use HTTPS in production (consider using a reverse proxy like nginx)
- Change the `FLASK_SECRET_KEY` in production
- This app is for personal use only

## Troubleshooting

### Login fails

- Verify your Picnic credentials are correct
- Ensure you selected the right country
- Check if Picnic service is available in your region

### Cannot access from Kobo

- Verify your server is running: `docker-compose ps` or check if Python process is running
- Ensure Kobo and server are on the same network
- Check firewall settings on your server
- Try accessing from another device first to verify the server is working

### Products not showing in search

- Picnic API may have rate limits
- Try more specific search terms
- Verify your Picnic account is active and has access to the catalog

## Development

To modify the application:

1. Edit `app.py` for backend logic
2. Edit templates in `templates/` for UI changes
3. The CSS is embedded in `templates/base.html` for simplicity
4. Restart the application to see changes

## Credits

- Built with [Flask](https://flask.palletsprojects.com/)
- Uses [python-picnic-api](https://github.com/MikeBrink/python-picnic-api) by MikeBrink
- Optimized for Kobo e-readers and e-ink displays

## License

MIT License - See LICENSE file for details

## Disclaimer

This is an unofficial application and is not affiliated with, endorsed by, or connected to Picnic. Use at your own risk. The developers are not responsible for any issues that may arise from using this application.
