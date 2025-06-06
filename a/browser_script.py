from playwright.sync_api import sync_playwright
import time
import os

def run_browser():
    with sync_playwright() as p:
        # Launch browser with proxy settings
        browser = p.chromium.launch(
            proxy={
                "server": "http://127.0.0.1:8080",
                "bypass": "127.0.0.1,localhost"
            },
            args=['--ignore-certificate-errors'],  # Required for mitmproxy
            headless=False  # <-- Make browser visible
        )
        
        # Create a new context with specific settings
        context = browser.new_context(
            ignore_https_errors=True,  # Required for mitmproxy
            viewport={'width': 1280, 'height': 720}
        )
        
        # Create a new page
        page = context.new_page()
        
        try:
            # Navigate to Fastmail
            print("Navigating to Fastmail...")
            page.goto("https://app.fastmail.com/", wait_until="networkidle")
            
            # Wait for the page to load
            page.wait_for_load_state("networkidle")
            
            # Keep the browser open for a while to capture requests
            print("Browser is open. Press Ctrl+C to close...")
            while True:
                time.sleep(1)
    
        except KeyboardInterrupt:
            print("\nClosing browser...")
        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    run_browser() 