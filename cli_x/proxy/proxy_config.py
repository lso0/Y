# Residential Proxy Configuration
RESIDENTIAL_PROXY = {
    'server': '96.43.111.71:12323',  # IPRoyal proxy server without protocol
    'username': '14a94c1afc8c9',  # IPRoyal username
    'password': '5fd3ded7e4',  # IPRoyal password
    'country': 'us',  # Default country
    'session': True,  # Use session-based authentication
}

# Proxy rotation settings (if your service supports it)
PROXY_ROTATION = {  
    'enabled': False,  # Disabled since we only have one proxy
    'interval': 300,  # Rotate every 5 minutes (in seconds)
    'countries': ['us'],  # List of countries to rotate through
} 