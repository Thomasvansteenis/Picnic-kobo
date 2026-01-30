# Picnic Shopping Cart Add-on

Manage your Picnic grocery shopping cart from your Kobo e-reader or any web browser.

This add-on provides a simple, e-ink optimized web interface for the Picnic grocery delivery service. Perfect for browsing and adding items to your cart from devices with limited browser capabilities like Kobo e-readers.

## Installation

1. Add this repository to your Home Assistant add-on store
2. Install the "Picnic Shopping Cart" add-on
3. Configure the add-on (see Configuration section below)
4. Start the add-on
5. Access the web interface at `http://homeassistant.local:5000`

## Configuration

The add-on requires minimal configuration:

```yaml
flask_secret_key: "change-this-to-a-random-secret-key-minimum-32-characters-long"
```

### Option: `flask_secret_key` (required)

This is the secret key used to encrypt session cookies. **You must change this from the default value for security.**

To generate a secure random key:
1. Open the Terminal add-on or SSH
2. Run: `python3 -c "import secrets; print(secrets.token_hex(32))"`
3. Copy the output and paste it in the configuration

**Default:** `change-this-to-a-random-secret-key-minimum-32-characters-long`

## How to Use

### Initial Setup

1. Start the add-on
2. Open the web interface:
   - Click "Open Web UI" button in the add-on page, OR
   - Navigate to `http://homeassistant.local:5000`, OR
   - Use your Home Assistant IP: `http://YOUR_HA_IP:5000`

### Login

1. Enter your Picnic account credentials:
   - **Email**: Your Picnic account email
   - **Password**: Your Picnic password
   - **Country**: Select NL (Netherlands), DE (Germany), or BE (Belgium)
2. Click "Login"

**Note:** Your credentials are stored only in your session and are not saved permanently.

### Searching for Products

1. Click "Search" in the navigation
2. Enter a product name (e.g., "milk", "bread", "tomatoes")
3. Browse the results
4. Adjust quantity if needed
5. Click "Add to Cart"

### Managing Your Cart

1. Click "Cart" in the navigation to view your items
2. Adjust quantities or remove items as needed
3. Use "Clear Cart" to empty your entire cart

### Completing Your Order

**Important:** This add-on only manages your shopping cart. To complete your order:

1. Open the official Picnic mobile app or website
2. Your cart will be synchronized automatically
3. Select your delivery slot
4. Complete the checkout process

## Using from Kobo E-reader

1. Connect your Kobo to the same WiFi network as your Home Assistant
2. Open the built-in web browser on your Kobo
3. Navigate to `http://YOUR_HA_IP:5000`
4. Login and start shopping

The interface is optimized for e-ink displays with:
- High contrast black and white design
- Large, easy-to-tap buttons
- No animations or graphics
- Simple, clean layout

## Adding to Home Assistant Dashboard (Optional)

You can add the app as a panel in your Home Assistant sidebar:

1. Edit your `configuration.yaml`:
   ```yaml
   panel_iframe:
     picnic_cart:
       title: "Picnic Cart"
       url: "http://localhost:5000"
       icon: mdi:cart
       require_admin: false
   ```
2. Restart Home Assistant
3. The "Picnic Cart" will appear in your sidebar

## Troubleshooting

### Cannot Login

- Verify your Picnic credentials are correct
- Ensure you selected the correct country
- Check if the Picnic service is available in your region
- View add-on logs for detailed error messages

### Cannot Access from Kobo/Other Device

- Ensure the device is on the same network as Home Assistant
- Check that the add-on is running (Status should be "Started")
- Try accessing from another device first to verify the service is working
- Check the add-on logs for errors

### Products Not Showing in Search

- Picnic API may have rate limits - wait a moment and try again
- Try more specific search terms
- Verify your Picnic account is active and has access to the catalog

### Viewing Logs

1. Go to the add-on page in Home Assistant
2. Click the "Log" tab
3. Look for any error messages

## Support

For issues and feature requests, please visit:
https://github.com/Thomasvansteenis/Picnic-kobo/issues

## Credits

- Built with Flask web framework
- Uses [python-picnic-api](https://github.com/MikeBrink/python-picnic-api) for Picnic integration
- Optimized for Kobo e-readers and e-ink displays

## Disclaimer

This is an unofficial add-on and is not affiliated with, endorsed by, or connected to Picnic or Home Assistant. Use at your own risk.
