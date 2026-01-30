# Quick Start Guide - TL;DR

For experienced users who just want the commands:

## Prerequisites
- Home Assistant with SSH access
- Docker installed

## Installation Commands

```bash
# 1. SSH into Home Assistant
ssh root@homeassistant.local

# 2. Navigate to config and create apps directory
cd /config
mkdir -p apps
cd apps

# 3. Get the application files
# (You'll need to transfer files or use git if available)
# For now, create the directory structure:
mkdir Picnic-kobo
cd Picnic-kobo

# 4. Copy your project files here (from your dev machine)
# Or manually create them following the repository structure

# 5. Create environment file
cat > .env << 'EOF'
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
EOF

# 6. Start the application
docker-compose up -d

# 7. Check it's running
docker ps
docker logs picnic-kobo

# 8. Find your Home Assistant IP
hostname -I

# 9. Access from Kobo browser
# Navigate to: http://YOUR_HA_IP:5000
```

## Verification

```bash
# Check status
docker ps | grep picnic-kobo

# View logs
docker logs picnic-kobo

# Test from command line
curl http://localhost:5000
```

## Useful Commands

```bash
# Restart
docker-compose restart

# Stop
docker-compose stop

# Start
docker-compose start

# View logs in real-time
docker logs -f picnic-kobo

# Rebuild after changes
docker-compose up -d --build

# Remove everything
docker-compose down
```

## Access URLs

- **From Home Assistant network:** `http://YOUR_HA_IP:5000`
- **From Kobo on same network:** Same URL
- **Default port:** 5000

## Troubleshooting One-Liners

```bash
# Port already in use? Check what's using it
netstat -tulpn | grep 5000

# Container won't start? Check logs
docker logs picnic-kobo

# Need to change port? Edit docker-compose.yml
# Change "5000:5000" to "5001:5000"

# Restart Home Assistant to apply changes
# Go to Settings → System → Restart
```

## Optional: Add to Home Assistant UI

Add to `/config/configuration.yaml`:

```yaml
panel_iframe:
  picnic_cart:
    title: "Picnic Cart"
    url: "http://localhost:5000"
    icon: mdi:cart
    require_admin: false
```

Then restart Home Assistant.

---

**That's it! Access `http://YOUR_HA_IP:5000` from your Kobo browser and start shopping!**
