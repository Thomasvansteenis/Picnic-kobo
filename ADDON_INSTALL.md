# Installing as a Home Assistant Add-on

This guide shows you how to install the Picnic Shopping Cart as a Home Assistant add-on.

## Method 1: Local Add-on Installation (Recommended for Testing)

This is the easiest method if you want to test the add-on or don't want to set up a public repository.

### Step 1: Access Your Home Assistant

1. Open Home Assistant web interface (`http://homeassistant.local:8123`)
2. Go to **Settings** → **Add-ons**
3. Install **"SSH & Web Terminal"** or **"Terminal & SSH"** if you haven't already
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

You have several options:

**Option A: Clone from Git (if available)**

```bash
# Install git if needed
apk add git

# Clone the repository
git clone https://github.com/Thomasvansteenis/Picnic-kobo.git .
git checkout claude/kobo-grocery-cart-app-bsunW
```

**Option B: Manual File Creation**

Create each file manually in the `/addons/picnic-cart` directory:

1. `config.json` - Add-on configuration
2. `Dockerfile` - Container build instructions
3. `build.json` - Build configuration
4. `run.sh` - Startup script
5. `app.py` - Main application
6. `requirements.txt` - Python dependencies
7. `templates/` - Template files (base.html, login.html, cart.html, search.html)

**Option C: Copy from Another Location**

If you already have the files on your Home Assistant system:

```bash
# Copy all files to the add-on directory
cp -r /path/to/Picnic-kobo/* /addons/picnic-cart/
```

### Step 4: Set Proper Permissions

```bash
# Make the run script executable
chmod +x /addons/picnic-cart/run.sh
```

### Step 5: Reload Add-ons

1. In Home Assistant web interface, go to **Settings** → **Add-ons**
2. Click the **⋮** (three dots) in the top right
3. Click **Reload** or **Check for updates**
4. Wait a few seconds

### Step 6: Install the Add-on

1. You should now see **"Picnic Shopping Cart"** in the list of local add-ons
2. Click on it
3. Click **Install**
4. Wait for installation to complete (it will build the Docker image)

### Step 7: Configure the Add-on

1. Go to the **Configuration** tab
2. Change the `flask_secret_key` to a random string:
   ```yaml
   flask_secret_key: "your-random-secret-key-here-at-least-32-characters"
   ```

   To generate a secure key, in the Terminal:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

3. Click **Save**

### Step 8: Start the Add-on

1. Go to the **Info** tab
2. Enable **Start on boot** (recommended)
3. Enable **Watchdog** (recommended)
4. Click **Start**

### Step 9: Access the Web Interface

1. Click **Open Web UI** in the add-on, OR
2. Navigate to `http://homeassistant.local:5000`, OR
3. Use your Home Assistant IP: `http://YOUR_HA_IP:5000`

---

## Method 2: Custom Repository (For Advanced Users)

If you want to share the add-on or have it update automatically:

### Step 1: Create a GitHub Repository

1. Push your add-on to a GitHub repository
2. The repository should contain all the add-on files

### Step 2: Add Repository to Home Assistant

1. Go to **Settings** → **Add-ons**
2. Click **Add-on Store**
3. Click the **⋮** (three dots) in the top right
4. Click **Repositories**
5. Add your repository URL: `https://github.com/YOUR_USERNAME/YOUR_REPO`
6. Click **Add**

### Step 3: Install from Repository

1. The add-on should now appear in the add-on store
2. Click on it and follow the installation steps from Method 1, Step 6 onwards

---

## Verifying Installation

### Check Add-on Status

1. Go to **Settings** → **Add-ons** → **Picnic Shopping Cart**
2. The status should show "Started" with a green indicator
3. Check the **Log** tab for any errors

### Test the Web Interface

1. Open `http://homeassistant.local:5000` in your browser
2. You should see the Picnic login page
3. Try logging in with your Picnic credentials

### Access from Kobo

1. Connect your Kobo to the same WiFi network
2. Open the web browser
3. Navigate to `http://YOUR_HA_IP:5000`
4. You should see the login page

---

## File Structure

Your add-on directory should look like this:

```
/addons/picnic-cart/
├── config.json          # Add-on metadata and configuration
├── build.json           # Build configuration for different architectures
├── Dockerfile           # Container build instructions
├── run.sh               # Entry point script
├── app.py               # Flask application
├── requirements.txt     # Python dependencies
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── cart.html
│   └── search.html
├── DOCS.md             # Add-on documentation
├── README.md           # General documentation
└── LICENSE
```

---

## Troubleshooting

### Add-on Not Appearing

- Make sure you ran the **Reload** command in Step 5
- Check that files are in the correct directory (`/addons/picnic-cart/`)
- Verify `config.json` exists and is valid JSON

### Build Failed

- Check the **Log** tab for build errors
- Ensure all required files are present
- Verify `Dockerfile` and `build.json` are correct

### Add-on Won't Start

- Check the **Log** tab for errors
- Verify you changed the `flask_secret_key` in configuration
- Ensure port 5000 is not already in use
- Check that `run.sh` is executable: `chmod +x /addons/picnic-cart/run.sh`

### Cannot Access Web Interface

- Verify the add-on is started
- Check the logs for Flask startup messages
- Try accessing from the same machine first: `http://localhost:5000`
- Check firewall settings

---

## Updating the Add-on

### Local Installation

1. Update the files in `/addons/picnic-cart/`
2. Go to the add-on page
3. Click **Rebuild**
4. Once rebuilt, click **Restart**

### Repository Installation

1. Update the version in `config.json`
2. Push changes to GitHub
3. In Home Assistant, go to the add-on page
4. Click **Update** when available

---

## Uninstalling

1. Go to **Settings** → **Add-ons** → **Picnic Shopping Cart**
2. Click **Uninstall**
3. Optionally, remove the directory:
   ```bash
   rm -rf /addons/picnic-cart
   ```

---

## Next Steps

Once installed:
1. ✅ Login with your Picnic credentials
2. ✅ Search for groceries
3. ✅ Add items to your cart
4. ✅ Complete your order in the official Picnic app

Enjoy easy grocery shopping from your Kobo! 🛒
