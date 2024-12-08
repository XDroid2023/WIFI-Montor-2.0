# WiFi Monitor

A simple Python application that monitors WiFi connections and displays information about available networks.

## Features
- Shows current WiFi connection details (SSID, signal strength, channel, transmit rate)
- Displays list of available WiFi networks
- Auto-refreshes every 10 seconds
- Manual refresh button
- Clean and simple GUI interface

## Requirements
- Python 3.x
- tkinter
- psutil

## Installation
1. Clone or download this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage
Run the application using Python:
```bash
python wifi_monitor.py
```

## Note
This application requires appropriate permissions to access network information. On macOS, it uses the built-in `airport` utility to gather WiFi information.
