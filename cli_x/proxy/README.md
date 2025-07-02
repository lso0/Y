# Proxy Browser Project

This project uses pyppeteer (Python port of Puppeteer) to automate browser tasks with proxy support.

## Setup Instructions

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies (if not already installed):
   ```bash
   pip3 install -r requirements.txt
   ```

3. Configure your proxy settings:
   - Open `proxy_browser.py`
   - Update the proxy configuration with your details:
     ```python
     proxy = {
         'server': 'http://your-proxy-server:port',
         'username': 'your-username',  # if required
         'password': 'your-password'   # if required
     }
     ```

4. Run the script:
   ```bash
   python3 proxy_browser.py
   ```

## Project Structure
- `proxy_browser.py`: Main script for browser automation with proxy
- `requirements.txt`: Project dependencies
- `venv/`: Python virtual environment directory

## Notes
- The script runs in non-headless mode by default (you'll see the browser window)
- The browser will stay open for 5 seconds by default
- Make sure to keep your proxy credentials secure 