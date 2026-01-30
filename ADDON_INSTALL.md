# Installing as a Home Assistant Add-on

This guide shows you how to install the Picnic Shopping Cart as a Home Assistant add-on.

## Method 1: Custom Repository Installation (Recommended ⭐)

This is the easiest method - install directly from the GitHub repository with automatic updates.

### Step 1: Add the Repository

#### Option A: One-Click Add (Easiest)

Click this button to add the repository automatically:

[![Add Repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FThomasvansteenis%2FPicnic-kobo)

Then skip to Step 2.

#### Option B: Manual Add

1. Open Home Assistant web interface (`http://homeassistant.local:8123`)
2. Navigate to **Settings** → **Add-ons**
3. Click the **Add-on Store** button
4. Click the **⋮** (three dots) menu in the top right corner
5. Select **Repositories**
6. Paste this URL: `https://github.com/Thomasvansteenis/Picnic-kobo`
7. Click **Add**
8. Close the repositories dialog

### Step 2: Install the Add-on

1. The add-on store will reload automatically
2. Scroll down to find **"Picnic Shopping Cart"**
3. Click on it
4. Click **Install**
5. Wait for the installation to complete (may take a few minutes as it builds the container)

### Step 3: Configure the Add-on

1. Once installed, go to the **Configuration** tab
2. Change the `flask_secret_key` to a secure random value:

   **Generate a secure key:**
   - Open **Terminal & SSH** add-on (install it first if needed)
   - Run this command:
     ```bash
     python3 -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Copy the output

3. Paste the key into the configuration:
   ```yaml
   flask_secret_key: "paste-your-generated-key-here"
   ```

4. Click **Save**

### Step 4: Start the Add-on

1. Go to the **Info** tab
2. Enable **Start on boot** (recommended)
3. Enable **Watchdog** (recommended)
4. Click **Start**
5. Wait for it to start (check the **Log** tab if there are issues)

### Step 5: Access the Web Interface

1. Click the **Open Web UI** button, OR
2. Navigate to `http://homeassistant.local:5000`, OR
3. Use your Home Assistant IP: `http://YOUR_HA_IP:5000`

### Step 6: Login and Use

1. Enter your Picnic credentials:
   - **Email**: Your Picnic account email
   - **Password**: Your Picnic password
   - **Country**: NL, DE, or BE

2. Start shopping!

---

## Method 2: Local Add-on Installation (For Development/Testing)

Use this method only if you want to modify the add-on or can't use the repository method.

### Step 1: Access Your Home Assistant

1. Open Home Assistant web interface
2. Go to **Settings** → **Add-ons**
3. Install **"Terminal & SSH"** if you haven't already
4. Open the Terminal

### Step 2: Create Local Add-on Directory

```bash
# Navigate to the add-ons directory
cd /addons

# If /addons doesn't exist, try:
# cd /usr/share/hassio/addons/local

# Create the add-on directory
mkdir -p picnic-cart
cd picnic-cart
```

### Step 3: Copy the Add-on Files

**Option A: Clone from Git (if available)**

```bash
# Install git if needed
apk add git

# Clone the repository
git clone https://github.com/Thomasvansteenis/Picnic-kobo.git temp
cd temp

# Copy only the add-on directory
cp -r picnic-cart/* /addons/picnic-cart/
cd /addons
rm -rf picnic-cart/temp
```

**Option B: Download and Extract**

1. Download the repository as a ZIP from GitHub
2. Extract it on your computer
3. Use the File Editor add-on or SCP to copy the contents of the `picnic-cart/` directory to `/addons/picnic-cart/`

**Option C: Manual File Creation**

Create each file manually in the `/addons/picnic-cart` directory. See the repository for file contents.

### Step 4: Set Permissions

```bash
chmod +x /addons/picnic-cart/run.sh
```

### Step 5: Reload Add-ons

1. In Home Assistant, go to **Settings** → **Add-ons**
2. Click the **⋮** (three dots) in the top right
3. Click **Reload** or **Check for updates**
4. Wait a few seconds

### Step 6: Install and Configure

Follow Steps 2-6 from Method 1 above.

---

## Using from Kobo E-reader

1. Connect your Kobo to the same WiFi network as Home Assistant
2. Open the built-in web browser on your Kobo
3. Navigate to `http://YOUR_HA_IP:5000`
   - Replace `YOUR_HA_IP` with your Home Assistant's IP address
   - Find your IP in Home Assistant: **Settings** → **System** → **Network**
4. Login with your Picnic credentials
5. Search for products and add to cart
6. Complete your order using the official Picnic app

The interface is optimized for e-ink displays with:
- High contrast black and white design
- Large touch-friendly buttons
- No animations
- Simple, clean layout

---

## Optional: Add to Home Assistant Sidebar

To access the cart directly from your Home Assistant sidebar:

1. Edit `/config/configuration.yaml`:

```yaml
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

2. Go to **Developer Tools** → **YAML** → **Restart**
3. The "Picnic Cart" panel will appear in your sidebar

---

## Troubleshooting

### Repository Not Showing Up

- Make sure you clicked **Add** after pasting the repository URL
- Refresh the add-on store page
- Check that the URL is correct: `https://github.com/Thomasvansteenis/Picnic-kobo`

### Add-on Not Appearing After Reload

- For local installation: Verify files are in `/addons/picnic-cart/`
- Check that `config.json` exists and is valid JSON
- Look at Home Assistant logs for errors

### Build Failed

- Check the **Log** tab for specific errors
- Ensure all required files are present
- Try rebuilding: Click **Rebuild** button

### Add-on Won't Start

- Check you changed the `flask_secret_key` from the default
- Verify port 5000 is not already in use
- Check logs for Python errors
- Ensure `run.sh` is executable (local install only)

### Cannot Access Web Interface

- Verify the add-on shows "Started" status
- Check the logs for Flask startup messages
- Try accessing from the same machine first: `http://localhost:5000`
- Verify your firewall isn't blocking port 5000

### Cannot Access from Kobo

1. Test from another device first (phone/computer)
2. Verify Kobo is on the same WiFi network
3. Check Home Assistant's IP address hasn't changed
4. Try accessing Home Assistant main page from Kobo first

---

## Updating the Add-on

### Repository Installation

Updates appear automatically when available:
1. Go to the add-on page
2. Click **Update** when the button appears
3. Wait for rebuild to complete
4. Click **Restart**

### Local Installation

1. Pull latest changes:
   ```bash
   cd /addons/picnic-cart
   git pull
   ```

2. Rebuild:
   - Go to add-on page
   - Click **Rebuild**
   - Click **Restart** when complete

---

## Uninstalling

1. Go to **Settings** → **Add-ons** → **Picnic Shopping Cart**
2. Click **Uninstall**
3. For repository: Optionally remove repository from the Repositories list
4. For local: Optionally delete `/addons/picnic-cart/` directory

---

## Next Steps

✅ Add-on installed and running
✅ Accessible at `http://YOUR_HA_IP:5000`
✅ Login with Picnic credentials
✅ Search for groceries from your Kobo
✅ Complete orders in the official Picnic app

Happy shopping! 🛒
