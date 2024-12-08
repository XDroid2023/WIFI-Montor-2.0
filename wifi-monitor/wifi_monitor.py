import tkinter
import customtkinter as ctk
import subprocess
import json
import time
import psutil
import os
import re
import webview
from threading import Thread
from datetime import datetime

class NetworkListFrame(ctk.CTkFrame):
    def __init__(self, parent, on_network_select):
        super().__init__(parent, fg_color="transparent")
        self.on_network_select = on_network_select
        
        # Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill=tkinter.X, pady=(0, 10))
        
        ctk.CTkLabel(title_frame, 
                    text="Networks", 
                    font=ctk.CTkFont(family="SF Pro Display", size=20, weight="bold")).pack(side=tkinter.LEFT, padx=15)
        
        # Network buttons frame with scrollable container
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill=tkinter.BOTH, expand=True, padx=5)
        
        # Store network buttons
        self.network_buttons = []
        self.selected_button = None

    def update_networks(self, networks):
        # Clear existing buttons
        for btn in self.network_buttons:
            btn.destroy()
        self.network_buttons.clear()
        
        # Create new buttons for each network
        for network in networks:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=network,
                command=lambda n=network, b=None: self.select_network(n, b),
                height=40,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                anchor="w",
                corner_radius=8,
                font=ctk.CTkFont(family="SF Pro Display", size=14)
            )
            btn.pack(fill=tkinter.X, padx=5, pady=3)
            self.network_buttons.append(btn)
            
    def select_network(self, network, button):
        # Reset previous selection
        if self.selected_button:
            self.selected_button.configure(fg_color="transparent")
            
        # Set new selection
        for btn in self.network_buttons:
            if btn.cget("text") == network:
                btn.configure(fg_color=("gray75", "gray30"))
                self.selected_button = btn
                break
                
        self.on_network_select(network)

class WifiMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("WiFi Monitor")
        self.root.geometry("1200x800")
        
        # Set the theme
        ctk.set_appearance_mode("system")  # Use system theme
        ctk.set_default_color_theme("blue")

        # Initialize WiFi interface
        self.wifi_interface = self.get_wifi_interface()
        if not self.wifi_interface:
            self.show_error("Could not find WiFi interface")
        
        # Create main frame with padding
        self.main_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.main_frame.pack(fill=tkinter.BOTH, expand=True, padx=20, pady=20)
        
        # Header with modern design
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill=tkinter.X, padx=10, pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="WiFi Monitor", 
            font=ctk.CTkFont(family="SF Pro Display", size=28, weight="bold")
        )
        title_label.pack(side=tkinter.LEFT, pady=10)
        
        self.last_update_label = ctk.CTkLabel(
            header_frame, 
            text="Last Update: Never", 
            font=ctk.CTkFont(family="SF Pro Display", size=13),
            text_color=("gray40", "gray60")
        )
        self.last_update_label.pack(side=tkinter.RIGHT, pady=10)
        
        # Create container for split view
        content_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray95", "gray10"))
        content_frame.pack(fill=tkinter.BOTH, expand=True, padx=10, pady=10)
        
        # Create split view
        self.paned_window = tkinter.PanedWindow(
            content_frame,
            orient=tkinter.HORIZONTAL,
            sashwidth=4,
            bg=("gray90" if ctk.get_appearance_mode() == "light" else "gray20"),
            bd=0
        )
        self.paned_window.pack(fill=tkinter.BOTH, expand=True, padx=2, pady=2)
        
        # Left panel - Network List
        self.network_list = NetworkListFrame(self.paned_window, self.on_network_select)
        
        # Right panel - Network Details
        self.details_frame = ctk.CTkFrame(self.paned_window, fg_color="transparent")
        
        # Add frames to paned window
        self.paned_window.add(self.network_list, width=300)
        self.paned_window.add(self.details_frame, width=400)
        
        # Network details components
        details_title_frame = ctk.CTkFrame(self.details_frame, fg_color="transparent")
        details_title_frame.pack(fill=tkinter.X, padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            details_title_frame, 
            text="Network Details", 
            font=ctk.CTkFont(family="SF Pro Display", size=20, weight="bold")
        ).pack(side=tkinter.LEFT)
        
        self.details_text = ctk.CTkTextbox(
            self.details_frame,
            font=ctk.CTkFont(family="SF Pro Display", size=13),
            corner_radius=8
        )
        self.details_text.pack(fill=tkinter.BOTH, expand=True, padx=15, pady=10)
        
        # Add browser frame
        self.browser_frame = ctk.CTkFrame(self.details_frame)
        self.browser_frame.pack(fill=tkinter.BOTH, expand=True, padx=15, pady=10)
        self.browser_window = None

        # Control frame
        control_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent", height=50)
        control_frame.pack(fill=tkinter.X, padx=10, pady=(10, 0))
        
        # Status indicator with label
        status_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        status_frame.pack(side=tkinter.LEFT)
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="●", 
            font=ctk.CTkFont(size=20),
            text_color="gray"
        )
        self.status_label.pack(side=tkinter.LEFT, padx=5)
        
        self.status_text = ctk.CTkLabel(
            status_frame,
            text="Idle",
            font=ctk.CTkFont(family="SF Pro Display", size=13),
            text_color=("gray40", "gray60")
        )
        self.status_text.pack(side=tkinter.LEFT, padx=5)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        buttons_frame.pack(side=tkinter.RIGHT)
        
        # Debug button
        self.debug_btn = ctk.CTkButton(
            buttons_frame,
            text="Debug Info",
            command=self.show_debug_info,
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="SF Pro Display", size=13)
        )
        self.debug_btn.pack(side=tkinter.RIGHT, padx=5)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            buttons_frame,
            text="Refresh",
            command=self.refresh_data,
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="SF Pro Display", size=13)
        )
        self.refresh_btn.pack(side=tkinter.RIGHT, padx=5)
        
        # Router Login button
        self.router_btn = ctk.CTkButton(
            buttons_frame,
            text="Router Login",
            command=self.open_router_login,
            width=120,
            height=32,
            corner_radius=8,
            font=ctk.CTkFont(family="SF Pro Display", size=13)
        )
        self.router_btn.pack(side=tkinter.RIGHT, padx=5)
        
        # Initial scan
        self.refresh_data()

    def get_wifi_interface(self):
        """Get the name of the WiFi interface"""
        try:
            result = subprocess.run(['networksetup', '-listallhardwareports'],
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            lines = result.stdout.split('\n')
            for i, line in enumerate(lines):
                if 'Wi-Fi' in line or 'Airport' in line:
                    if i + 1 < len(lines):
                        match = re.search(r'Device:\s*(\w+)', lines[i + 1])
                        if match:
                            return match.group(1)
            return None
        except Exception as e:
            print(f"Error getting WiFi interface: {str(e)}")
            return None

    def show_error(self, message):
        """Show error in the details text box"""
        if hasattr(self, 'details_text'):
            self.details_text.delete("0.0", tkinter.END)
            self.details_text.insert("0.0", f"Error: {message}")
        else:
            print(f"Error: {message}")

    def show_debug_info(self):
        """Display debug information"""
        debug_info = []
        debug_info.append("=== Debug Information ===")
        
        # WiFi Interface
        debug_info.append(f"\nWiFi Interface: {self.wifi_interface}")
        
        # Network Hardware Ports
        try:
            result = subprocess.run(['networksetup', '-listallhardwareports'],
                                  capture_output=True, text=True)
            debug_info.append("\nHardware Ports:")
            debug_info.append(result.stdout)
        except Exception as e:
            debug_info.append(f"Error getting hardware ports: {str(e)}")
        
        # Current WiFi Info
        try:
            result = subprocess.run(['networksetup', '-getinfo', 'Wi-Fi'],
                                  capture_output=True, text=True)
            debug_info.append("\nWiFi Information:")
            debug_info.append(result.stdout)
        except Exception as e:
            debug_info.append(f"Error getting WiFi info: {str(e)}")
        
        # Display debug info
        self.details_text.delete("0.0", tkinter.END)
        self.details_text.insert("0.0", '\n'.join(debug_info))

    def get_network_password(self, network_name):
        """Get the password for a saved network using security command"""
        try:
            # Use security command to extract password from keychain
            cmd = [
                'security', 'find-generic-password',
                '-D', 'AirPort network password',
                '-a', network_name,
                '-w'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"Error getting password: {str(e)}")
        return None

    def get_network_info(self, network_name):
        """Get detailed information about a specific network"""
        info = []
        info.append(f"Network Name: {network_name}")
        
        try:
            # Get network security info
            security_info = subprocess.run(['networksetup', '-getinfo', 'Wi-Fi'],
                                         capture_output=True, text=True)
            
            # Try to get additional info using airport utility
            airport_cmd = ['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I']
            airport_info = subprocess.run(airport_cmd, capture_output=True, text=True)
            
            if airport_info.returncode == 0:
                for line in airport_info.stdout.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        if 'SSID' in key and value == network_name:
                            info.append("\nCurrent Connection:")
                            info.append("Status: Connected")
                            
                        if value == network_name:
                            if 'BSSID' in key:
                                info.append(f"BSSID: {value}")
                            elif 'channel' in key.lower():
                                info.append(f"Channel: {value}")
                            elif 'RSSI' in key:
                                info.append(f"Signal Strength: {value} dBm")
                            elif 'lastTxRate' in key:
                                info.append(f"Transmission Rate: {value} Mbps")
                            elif 'maxRate' in key:
                                info.append(f"Maximum Rate: {value} Mbps")
            
            # Check if network is in preferred networks
            preferred_cmd = ['networksetup', '-listpreferredwirelessnetworks', self.wifi_interface]
            preferred_result = subprocess.run(preferred_cmd, capture_output=True, text=True)
            if preferred_result.returncode == 0:
                if network_name in preferred_result.stdout:
                    info.append("\nNetwork Status:")
                    info.append("Saved: Yes")
                    
                    # Try to get password
                    password = self.get_network_password(network_name)
                    if password:
                        info.append(f"Password: {password}")
                    else:
                        info.append("Password: Not available")
                else:
                    info.append("\nNetwork Status:")
                    info.append("Saved: No")
            
            # Get security info
            scan_results = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-s'],
                                        capture_output=True, text=True)
            if scan_results.returncode == 0:
                for line in scan_results.stdout.split('\n'):
                    if network_name in line:
                        parts = line.split()
                        if len(parts) >= 7:
                            security = parts[6]
                            info.append(f"Security: {security}")
                            break
            
        except Exception as e:
            info.append(f"\nError: {str(e)}")
        
        return '\n'.join(info)

    def is_connected(self, network_name):
        """Check if we're connected to the specified network"""
        try:
            result = subprocess.run(['networksetup', '-getairportnetwork', self.wifi_interface],
                                  capture_output=True, text=True)
            return network_name in result.stdout
        except:
            return False

    def is_preferred_network(self, network_name):
        """Check if the network is in the preferred networks list"""
        try:
            result = subprocess.run(['networksetup', '-listpreferredwirelessnetworks', self.wifi_interface],
                                  capture_output=True, text=True)
            return network_name in result.stdout
        except:
            return False

    def on_network_select(self, network_name):
        """Handle network selection"""
        info = self.get_network_info(network_name)
        self.details_text.delete("0.0", tkinter.END)
        self.details_text.insert("0.0", info)

    def scan_networks(self):
        """Scan for available networks"""
        try:
            if not self.wifi_interface:
                return []
            
            networks = []
            
            # Try airport scan first
            airport_path = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
            if os.path.exists(airport_path):
                scan = subprocess.run([airport_path, '-s'],
                                    capture_output=True, text=True)
                if scan.returncode == 0:
                    for line in scan.stdout.split('\n')[1:]:  # Skip header
                        if line.strip():
                            ssid = line.split()[0]
                            if ssid not in networks:
                                networks.append(ssid)
            
            # Get preferred networks as backup
            preferred = subprocess.run(['networksetup', '-listpreferredwirelessnetworks', self.wifi_interface],
                                     capture_output=True, text=True)
            
            if preferred.returncode == 0:
                for line in preferred.stdout.split('\n'):
                    if line.strip() and not line.startswith('Preferred networks'):
                        if line.strip() not in networks:
                            networks.append(line.strip())
            
            return sorted(networks)
            
        except Exception as e:
            print(f"Error scanning networks: {str(e)}")
            return []

    def set_status(self, is_scanning):
        if is_scanning:
            self.status_label.configure(text_color=("blue", "#3a7ebf"))
            self.status_text.configure(text="Scanning...")
        else:
            self.status_label.configure(text_color=("gray60", "gray40"))
            self.status_text.configure(text="Idle")

    def refresh_data(self):
        self.set_status(True)
        try:
            self.refresh_btn.configure(state="disabled")
            
            # Scan for networks
            networks = self.scan_networks()
            
            # Update network list
            self.network_list.update_networks(sorted(networks))
            
            # Update timestamp
            self.last_update_label.configure(
                text=f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Reset status
            self.set_status(False)
            self.refresh_btn.configure(state="normal")
            
        except Exception as e:
            self.status_label.configure(text_color="red")
            self.refresh_btn.configure(state="normal")
            self.show_error(f"Error refreshing data: {str(e)}")

    def open_router_login(self):
        """Open the router login page in a new window"""
        # Common router IP addresses
        router_ips = ['192.168.1.1', '192.168.0.1', '10.0.0.1']
        
        # Try to find the default gateway
        try:
            result = subprocess.run(['netstat', '-nr'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    gateway = line.split()[1]
                    router_ips.insert(0, gateway)
                    break
        except Exception as e:
            print(f"Error finding default gateway: {e}")

        # Create a new window for the browser
        browser_window = ctk.CTkToplevel(self.root)
        browser_window.title("Router Login")
        browser_window.geometry("800x600")
        
        # Create a frame for the browser
        browser_container = ctk.CTkFrame(browser_window)
        browser_container.pack(fill=tkinter.BOTH, expand=True, padx=10, pady=10)
        
        # Try each router IP
        for ip in router_ips:
            try:
                url = f"http://{ip}"
                self.browser_window = webview.create_window('Router Login', url, width=800, height=600)
                webview.start(gui='cef')
                break
            except Exception as e:
                continue

    def on_closing(self):
        self.root.destroy()

def main():
    root = ctk.CTk()
    app = WifiMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
