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

- Python 3.11 or higher (for standalone deployment)
- Docker and Docker Compose (for containerized deployment)
- A Picnic account (Netherlands, Germany, or Belgium)

## Installation

### Option 1: Docker Deployment (Recommended for Home Assistant)

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd Picnic-kobo
   ```

2. Create a `.env` file (optional, you can also login via web interface):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred text editor
   ```

3. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. Access the application at `http://localhost:5000` or `http://your-server-ip:5000`

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

## Home Assistant Integration

### Running on Home Assistant OS

1. Install the "SSH & Web Terminal" add-on from the Add-on Store
2. SSH into your Home Assistant instance
3. Navigate to your config directory or create a custom apps folder
4. Clone this repository
5. Run with Docker Compose as shown above
6. Access via `http://homeassistant.local:5000`

### Adding to Home Assistant Dashboard

You can add this as an iframe panel in your Home Assistant:

```yaml
# configuration.yaml
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

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
