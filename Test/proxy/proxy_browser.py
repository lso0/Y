import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from proxy_config import RESIDENTIAL_PROXY
import time
import random
import logging
import json
import os
import base64
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyBrowser:
    def __init__(self):
        self.proxy = RESIDENTIAL_PROXY
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'
        ]
        # Create output directory with timestamp
        self.output_dir = f"security_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.output_dir, exist_ok=True)

    def _get_random_viewport(self):
        # Random but realistic viewport sizes
        widths = [1366, 1440, 1536, 1920]
        heights = [768, 900, 864, 1080]
        width = random.choice(widths)
        height = random.choice(heights)
        return width, height

    def _setup_proxy_extension(self):
        # Create proxy extension directory
        proxy_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proxy_folder')
        os.makedirs(proxy_folder, exist_ok=True)

        # Extract proxy details
        proxy_host = self.proxy['server'].split(':')[0]
        proxy_port = self.proxy['server'].split(':')[1]
        proxy_username = self.proxy['username']
        proxy_password = self.proxy['password']

        # Create manifest.json
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "storage",
                "webRequest",
                "webRequestAuthProvider"
            ],
            "host_permissions": [
                "<all_urls>"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "minimum_chrome_version": "22.0.0"
        }
        """

        # Create background.js
        background_js = """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt("%s")
                },
                bypassList: ["localhost"]
            }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """ % (proxy_host, proxy_port, proxy_username, proxy_password)

        # Write extension files
        with open(os.path.join(proxy_folder, "manifest.json"), "w") as f:
            f.write(manifest_json)
        with open(os.path.join(proxy_folder, "background.js"), "w") as f:
            f.write(background_js)

        return proxy_folder

    def create_browser(self):
        try:
            options = uc.ChromeOptions()
            
            # Set up proxy extension
            proxy_extension_path = self._setup_proxy_extension()
            options.add_argument(f'--load-extension={proxy_extension_path}')
            
            # Set user agent
            user_agent = random.choice(self.user_agents)
            options.add_argument(f'user-agent={user_agent}')
            
            # Add other options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-infobars')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--allow-insecure-localhost')
            options.add_argument('--remote-debugging-port=0')
            options.add_argument('--disable-extensions-except=' + proxy_extension_path)
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Disable WebRTC
            options.add_argument('--disable-webrtc')
            options.add_argument('--disable-webrtc-hw-encoding')
            options.add_argument('--disable-webrtc-hw-decoding')
            options.add_argument('--disable-webrtc-multiple-routes')
            options.add_argument('--disable-webrtc-hw-vp8-encoding')
            options.add_argument('--disable-webrtc-hw-vp8-decoding')
            options.add_argument('--disable-webrtc-hw-h264-encoding')
            options.add_argument('--disable-webrtc-hw-h264-decoding')
            
            # Set window size
            width, height = self._get_random_viewport()
            options.add_argument(f'--window-size={width},{height}')
            
            # Create the driver with undetected-chromedriver
            driver = uc.Chrome(
                options=options,
                version_main=135,  # Specify your Chrome version
                driver_executable_path=None,  # Let it auto-detect
                browser_executable_path=None,  # Let it auto-detect
                suppress_welcome=True,  # Suppress welcome screen
                headless=False,  # Run in visible mode
                use_subprocess=True  # Use subprocess for better stability
            )
            
            # Set window size
            driver.set_window_size(width, height)
            
            return driver
        except Exception as e:
            logger.error(f"Failed to create browser: {e}")
            raise

def main():
    proxy_browser = ProxyBrowser()
    driver = None
    
    try:
        # Create browser
        driver = proxy_browser.create_browser()
        logger.info("Browser launched successfully. It will stay open for 2 minutes.")
        
        # Keep the browser open for 2 minutes
        time.sleep(120)  # 120 seconds = 2 minutes
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        if driver:
            error_screenshot_path = os.path.join(proxy_browser.output_dir, 'error_screenshot.png')
            driver.save_screenshot(error_screenshot_path)
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    main() 