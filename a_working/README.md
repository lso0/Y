# Fastmail Request Logger

This project sets up a proxy to intercept and log requests between a browser and Fastmail.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

2. Install mitmproxy certificate:
```bash
mitmproxy
```
Then visit http://mitm.it in your browser and install the certificate for your system.

## Usage

1. In one terminal, start the mitmproxy:
```bash
mitmproxy -s mitm_script.py
```

2. In another terminal, run the browser automation:
```bash
python browser_script.py
```

The requests will be logged to `requests.log` in the current directory.

## Notes

- The browser will stay open until you press Ctrl+C
- All requests and responses will be logged with timestamps
- The log file will be in JSON format for easy parsing 