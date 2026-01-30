# Home Assistant Setup Guide

Complete step-by-step guide to deploy the Picnic Kobo Cart app on your Home Assistant server.

## Prerequisites

- Home Assistant installed and running
- SSH access to your Home Assistant server
- Your Picnic account credentials (email, password, country)

---

## Step 1: Enable SSH Access to Home Assistant

### Option A: Home Assistant OS (Most Common)

1. Open your Home Assistant web interface (usually `http://homeassistant.local:8123`)
2. Go to **Settings** → **Add-ons**
3. Click **Add-on Store** (bottom right)
4. Search for **"SSH & Web Terminal"** or **"Terminal & SSH"**
5. Click on it and press **Install**
6. Once installed, go to the **Configuration** tab:
   - Set a password or add your SSH key
   - Enable "Show in sidebar" for easy access
7. Click **Start** and enable **Start on boot**

### Option B: Home Assistant Container/Supervised

If you're running Home Assistant in Docker, you likely already have SSH access to your host machine. Use your regular SSH method.

---

## Step 2: Access Your Home Assistant Server via SSH

### From Computer (Windows)

1. Open **PowerShell** or **Command Prompt**
2. Type: `ssh root@homeassistant.local`
   - Or use your Home Assistant IP: `ssh root@YOUR_HA_IP`
3. Enter the password you set in Step 1

### From Computer (Mac/Linux)

1. Open **Terminal**
2. Type: `ssh root@homeassistant.local`
   - Or: `ssh root@YOUR_HA_IP`
3. Enter your password

### From Home Assistant Web Interface

1. Click **Terminal** in the sidebar (if you enabled it in Step 1)
2. You'll have a terminal directly in your browser

---

## Step 3: Navigate to the Right Directory

Once connected via SSH, choose where to install:

### Option A: In Home Assistant config directory (Recommended)

```bash
# Navigate to config directory
cd /config

# Create an apps directory
mkdir -p apps
cd apps
```

### Option B: In root directory (Alternative)

```bash
# Navigate to root
cd /root
```

---

## Step 4: Install Git (If Not Already Installed)

Check if git is installed:
```bash
git --version
```

If not installed:

**For Home Assistant OS:**
```bash
apk add git
```

**For Debian/Ubuntu based systems:**
```bash
apt-get update && apt-get install -y git
```

---

## Step 5: Clone the Repository

```bash
# Clone the repository
git clone http://127.0.0.1:32185/git/Thomasvansteenis/Picnic-kobo.git

# Navigate into the directory
cd Picnic-kobo

# Switch to the correct branch
git checkout claude/kobo-grocery-cart-app-bsunW
```

**Note:** If the clone URL doesn't work, you may need to use your actual GitHub URL or copy the files manually (see Alternative Method below).

### Alternative Method: Download Files Manually

If git clone doesn't work, you can create files manually:

```bash
# Create directory
mkdir -p /config/apps/Picnic-kobo
cd /config/apps/Picnic-kobo

# You'll need to copy the files from your development machine
# Or recreate them using the template provided
```

---

## Step 6: Install Docker (If Using Home Assistant OS)

Home Assistant OS usually has Docker built-in. Verify:

```bash
docker --version
docker-compose --version
```

If `docker-compose` is not available, you might need to use `docker compose` (note the space) instead.

---

## Step 7: Configure the Application

### Create Environment File (Optional but Recommended)

```bash
# Copy the example environment file
cp .env.example .env

# Edit the environment file
nano .env
```

Add/modify:
```
FLASK_SECRET_KEY=your_random_secret_key_here_make_it_long_and_random
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

Press `Ctrl+X`, then `Y`, then `Enter` to save and exit.

### Generate a Strong Secret Key

```bash
# Generate a random secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your `FLASK_SECRET_KEY`.

---

## Step 8: Build and Start the Application

### Using Docker Compose (Recommended)

```bash
# Make sure you're in the Picnic-kobo directory
cd /config/apps/Picnic-kobo

# Build and start the container
docker-compose up -d
```

The `-d` flag runs it in the background (detached mode).

### Alternative: Using Docker Directly

If docker-compose doesn't work:

```bash
# Build the image
docker build -t picnic-kobo .

# Run the container
docker run -d \
  --name picnic-kobo \
  -p 5000:5000 \
  -e FLASK_SECRET_KEY=your_secret_key_here \
  --restart unless-stopped \
  picnic-kobo
```

---

## Step 9: Verify the Application is Running

```bash
# Check if container is running
docker ps

# You should see a container named "picnic-kobo"

# Check logs to verify it started correctly
docker logs picnic-kobo

# You should see something like:
# * Running on http://0.0.0.0:5000
```

---

## Step 10: Find Your Home Assistant IP Address

If you don't know your Home Assistant IP:

```bash
# On the Home Assistant terminal
hostname -I
```

Or check in Home Assistant:
1. Go to **Settings** → **System** → **Network**
2. Note your IP address (e.g., `192.168.1.100`)

---

## Step 11: Access from Your Kobo E-reader

1. **On your Kobo:**
   - Tap the **home** button
   - Tap **Settings** → **Wi-Fi connection**
   - Make sure you're connected to the same network as Home Assistant

2. **Open the browser:**
   - Tap **home** button
   - Swipe down from top
   - Tap the **web browser** icon
   - If you don't see it, you may need to enable it (varies by Kobo model)

3. **Navigate to the app:**
   - In the address bar, type: `http://YOUR_HA_IP:5000`
   - Example: `http://192.168.1.100:5000`

4. **Login:**
   - Enter your Picnic email
   - Enter your Picnic password
   - Select your country (NL, DE, or BE)
   - Tap **Login**

---

## Step 12: (Optional) Add to Home Assistant Dashboard

You can add the app as a panel in your Home Assistant UI:

1. **Edit Home Assistant configuration:**

```bash
# Open configuration.yaml
nano /config/configuration.yaml
```

2. **Add the following:**

```yaml
# Picnic Cart Panel
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

3. **Save and restart Home Assistant:**
   - Go to **Settings** → **System** → **Restart** → **Restart Home Assistant**

4. **Access it:**
   - You should now see "Picnic Cart" in your Home Assistant sidebar

---

## Step 13: (Optional) Set Up Auto-Start

The application should automatically start with Home Assistant if you used `docker-compose` with the `restart: unless-stopped` policy (which is already in the docker-compose.yml file).

To verify auto-start is enabled:

```bash
docker inspect picnic-kobo | grep -i restart
```

You should see: `"RestartPolicy": { "Name": "unless-stopped" }`

---

## Troubleshooting

### Container won't start

```bash
# Check logs for errors
docker logs picnic-kobo

# Check if port 5000 is already in use
netstat -tulpn | grep 5000

# If port is in use, change it in docker-compose.yml:
# ports:
#   - "5001:5000"  # Use 5001 instead
```

### Can't access from Kobo

1. **Test from another device first:**
   - From your phone or computer, try accessing `http://YOUR_HA_IP:5000`
   - If this doesn't work, the issue is with the server, not the Kobo

2. **Check firewall:**
   ```bash
   # On Home Assistant OS, firewall is usually not an issue
   # But verify the container is listening
   docker exec picnic-kobo netstat -tlnp
   ```

3. **Verify Kobo and HA are on same network:**
   - Check Kobo Wi-Fi settings
   - Make sure it's connected to the same network as Home Assistant

### Login fails

- Verify your Picnic credentials are correct
- Make sure you selected the correct country
- Check if Picnic service is working (try logging in on phone app)

### Application stops after reboot

```bash
# Manually restart it
docker-compose up -d

# Or
docker start picnic-kobo

# Check restart policy
docker update --restart unless-stopped picnic-kobo
```

---

## Updating the Application

To update to a newer version:

```bash
# Navigate to directory
cd /config/apps/Picnic-kobo

# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

---

## Stopping/Removing the Application

### Stop temporarily:
```bash
docker-compose stop
```

### Stop and remove:
```bash
docker-compose down
```

### Remove completely (including images):
```bash
docker-compose down --rmi all
rm -rf /config/apps/Picnic-kobo
```

---

## Next Steps

1. ✅ Application is running at `http://YOUR_HA_IP:5000`
2. ✅ Access from Kobo browser
3. ✅ Login with Picnic credentials
4. ✅ Search for products and add to cart
5. ✅ Complete order using official Picnic app

---

## Security Recommendations

1. **Change the secret key** in `.env` to a random string
2. **Use HTTPS** if accessing from outside your home network (use a reverse proxy like Nginx Proxy Manager)
3. **Don't expose port 5000** to the internet directly
4. **Keep your Picnic credentials secure** - they're only stored in session cookies

---

## Support

If you encounter issues:
1. Check the logs: `docker logs picnic-kobo`
2. Verify the container is running: `docker ps`
3. Test from another device before trying Kobo
4. Check Home Assistant community forums for Docker-related issues

---

## Summary of Key Commands

```bash
# Navigate to app directory
cd /config/apps/Picnic-kobo

# Start application
docker-compose up -d

# Stop application
docker-compose stop

# Restart application
docker-compose restart

# View logs
docker logs picnic-kobo

# Follow logs in real-time
docker logs -f picnic-kobo

# Check status
docker ps
```

---

**You're all set! Happy shopping! 🛒**
