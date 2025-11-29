#!/bin/bash
# Cloudflare Tunnel Quick Setup Script
# Read CLOUDFLARE_TUNNEL_SETUP.md for detailed explanations

set -e

echo "=== Cloudflare Tunnel Setup for CTA Display ==="
echo ""

# Step 1: Install cloudflared
echo "Step 1: Installing cloudflared..."
if command -v cloudflared &> /dev/null; then
    echo "✓ cloudflared already installed"
    cloudflared --version
else
    echo "Downloading cloudflared..."
    wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64
    chmod +x cloudflared-linux-arm64
    sudo mv cloudflared-linux-arm64 /usr/local/bin/cloudflared
    echo "✓ cloudflared installed"
    cloudflared --version
fi

echo ""
echo "=== MANUAL STEPS REQUIRED ==="
echo ""

# Step 2: Authentication
echo "Step 2: Authenticate with Cloudflare"
echo "Run this command and follow the browser prompt:"
echo "  cloudflared tunnel login"
echo ""
echo "Press Enter after you've completed authentication..."
read -r

# Step 3: List existing tunnels
echo ""
echo "Step 3: Checking for existing tunnels..."
cloudflared tunnel list
echo ""
echo "Do you see tunnel ID 6e8543a9-6611-4286-b612-3d813c110e0e in the list above?"
echo "If YES, you can reuse it (if you have the credentials file)."
echo "If NO, or if you want a fresh start, we'll create a new tunnel."
echo ""
read -p "Create a NEW tunnel? (y/n): " create_new

if [[ "$create_new" =~ ^[Yy]$ ]]; then
    # Step 4: Create new tunnel
    echo ""
    echo "Step 4: Creating new tunnel..."
    cloudflared tunnel create cta-frame
    echo ""
    echo "✓ Tunnel created!"
    echo ""
    echo "IMPORTANT: Copy the tunnel ID from the output above."
    read -p "Enter the tunnel ID: " TUNNEL_ID
    
    # Step 5: Route DNS
    echo ""
    echo "Step 5: Configuring DNS..."
    cloudflared tunnel route dns "$TUNNEL_ID" frame.snappify.cc
    echo "✓ DNS configured"
else
    echo ""
    read -p "Enter your existing tunnel ID: " TUNNEL_ID
    echo ""
    echo "Make sure you have the credentials file at:"
    echo "  ~/.cloudflared/$TUNNEL_ID.json"
    echo ""
    read -p "Press Enter to continue..."
fi

# Step 6: Create config file
echo ""
echo "Step 6: Creating config file..."
sudo mkdir -p /etc/cloudflared

CONFIG_FILE="/etc/cloudflared/config.yml"
sudo tee "$CONFIG_FILE" > /dev/null <<EOF
tunnel: $TUNNEL_ID
credentials-file: /home/bilal/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: frame.snappify.cc
    service: http://localhost:5001
  - service: http_status:404
EOF

echo "✓ Config file created at $CONFIG_FILE"
echo ""
cat "$CONFIG_FILE"

# Step 7: Test tunnel manually
echo ""
echo "Step 7: Testing tunnel manually..."
echo "This will run the tunnel in the foreground. Press Ctrl+C to stop."
echo ""
read -p "Press Enter to test..."
cloudflared tunnel --config /etc/cloudflared/config.yml run

# Note: If user presses Ctrl+C, script continues here

# Step 8: Install systemd service
echo ""
echo "Step 8: Installing systemd service..."
sudo cloudflared service install
echo "✓ Service installed"

# Step 9: Enable and start
echo ""
echo "Step 9: Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
echo "✓ Service started"

# Step 10: Check status
echo ""
echo "Step 10: Checking service status..."
sudo systemctl status cloudflared --no-pager
echo ""

# Step 11: Show logs
echo ""
echo "Service logs (last 20 lines):"
sudo journalctl -u cloudflared -n 20 --no-pager
echo ""

# Step 12: Verification
echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Verify your setup:"
echo "  1. Check Flask backend: curl http://localhost:5001/health"
echo "  2. Check public endpoint: curl https://frame.snappify.cc/health"
echo "  3. View logs: sudo journalctl -u cloudflared -f"
echo ""
echo "Your upload URL is:"
echo "  https://frame.snappify.cc/upload/<YOUR_UPLOAD_TOKEN>"
echo ""
echo "For troubleshooting, see CLOUDFLARE_TUNNEL_SETUP.md"
