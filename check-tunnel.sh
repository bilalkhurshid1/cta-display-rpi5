#!/bin/bash
# Quick health check for CTA Display + Cloudflare Tunnel

echo "=== CTA Display & Cloudflare Tunnel Health Check ==="
echo ""

echo "1. Flask Backend (local)"
echo "   Testing: http://localhost:5001/health"
if curl -s -f http://localhost:5001/health > /dev/null 2>&1; then
    echo "   ✓ Flask backend is responding"
else
    echo "   ✗ Flask backend is NOT responding"
    echo "     - Check if photo_backend.py is running: ps aux | grep photo_backend"
    echo "     - Check logs: tail /home/bilal/cta-display-rpi5/photo_backend.log"
fi

echo ""
echo "2. Cloudflare Tunnel Service"
if systemctl is-active --quiet cloudflared; then
    echo "   ✓ Tunnel service is running"
    
    # Check if tunnel is actually connected
    if sudo journalctl -u cloudflared -n 20 --no-pager | grep -q "Connection.*registered"; then
        echo "   ✓ Tunnel is connected to Cloudflare"
    else
        echo "   ⚠ Service running but tunnel may not be connected"
        echo "     - Check logs: sudo journalctl -u cloudflared -n 50"
    fi
else
    echo "   ✗ Tunnel service is NOT running"
    echo "     - Start it: sudo systemctl start cloudflared"
    echo "     - Check status: sudo systemctl status cloudflared"
fi

echo ""
echo "3. Public Endpoint (internet)"
echo "   Testing: https://frame.snappify.cc/health"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://frame.snappify.cc/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ Public endpoint is accessible (HTTP $HTTP_CODE)"
else
    echo "   ✗ Public endpoint returned HTTP $HTTP_CODE"
    if [ "$HTTP_CODE" = "000" ]; then
        echo "     - Could not connect (DNS or network issue)"
    elif [ "$HTTP_CODE" = "502" ] || [ "$HTTP_CODE" = "504" ]; then
        echo "     - Tunnel connected but backend unreachable"
        echo "     - Verify Flask is running and config.yml points to correct port"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo "     - Tunnel connected but /health route not found"
        echo "     - Check if hostname is configured correctly in config.yml"
    fi
fi

echo ""
echo "4. DNS Configuration"
CNAME=$(dig +short frame.snappify.cc 2>/dev/null | tail -n 1)
if [[ "$CNAME" == *"cfargotunnel.com"* ]]; then
    echo "   ✓ DNS points to Cloudflare Tunnel"
    echo "     CNAME: $CNAME"
elif [ -n "$CNAME" ]; then
    echo "   ⚠ DNS exists but doesn't point to cfargotunnel.com"
    echo "     Current value: $CNAME"
    echo "     - Run: cloudflared tunnel route dns <TUNNEL_ID> frame.snappify.cc"
else
    echo "   ✗ No DNS record found for frame.snappify.cc"
    echo "     - Run: cloudflared tunnel route dns <TUNNEL_ID> frame.snappify.cc"
fi

echo ""
echo "5. Configuration Files"
if [ -f /etc/cloudflared/config.yml ]; then
    echo "   ✓ Config file exists: /etc/cloudflared/config.yml"
    TUNNEL_ID=$(grep "^tunnel:" /etc/cloudflared/config.yml | awk '{print $2}')
    CREDS_FILE=$(grep "^credentials-file:" /etc/cloudflared/config.yml | awk '{print $2}')
    
    if [ -n "$TUNNEL_ID" ]; then
        echo "     Tunnel ID: $TUNNEL_ID"
    fi
    
    if [ -n "$CREDS_FILE" ] && [ -f "$CREDS_FILE" ]; then
        echo "   ✓ Credentials file exists: $CREDS_FILE"
    elif [ -n "$CREDS_FILE" ]; then
        echo "   ✗ Credentials file NOT found: $CREDS_FILE"
    fi
else
    echo "   ✗ Config file NOT found: /etc/cloudflared/config.yml"
fi

echo ""
echo "=== Summary ==="
echo "If all checks pass (✓), your tunnel is working correctly."
echo "If any checks fail (✗), follow the suggestions above."
echo ""
echo "For detailed logs: sudo journalctl -u cloudflared -f"
echo "For more help: See CLOUDFLARE_TUNNEL_SETUP.md"
