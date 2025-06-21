import os
from dotenv import load_dotenv
from firecrawl.firecrawl import FirecrawlApp
from firecrawl.firecrawl import ScrapeOptions
from datetime import datetime

# Load environment variables
load_dotenv()

def save_to_file(data, filename):
    """Save data to a text file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(data))
    print(f"Results saved to {filename}")

def main():
    # Initialize Firecrawl with your API key
    api_key = os.getenv('FIRECRAWL_API_KEY')
    if not api_key:
        raise ValueError("Please set FIRECRAWL_API_KEY in your .env file")
    
    app = FirecrawlApp(api_key=api_key)
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get current timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Example 1: Basic scraping
    print("\n=== Example 1: Basic Scraping ===")
    url = "https://www.revenuecat.com/"
    scrape_status = app.scrape_url(
        url,
        formats=["markdown", "html"]
    )
    print(f"Scraping status for {url}:")
    print(scrape_status)
    
    # Save scraping results
    scrape_filename = os.path.join(output_dir, f"scrape_results_{timestamp}.txt")
    save_to_file(scrape_status, scrape_filename)
    
    # Example 2: Crawling a website
    print("\n=== Example 2: Crawling a Website ===")
    crawl_status = app.crawl_url(
        url,
        limit=5,  # Limit to 5 pages for demo
        scrape_options=ScrapeOptions(
            formats=["markdown", "html"],
        ),
        poll_interval=30
    )
    print(f"Crawling status for {url}:")
    print(crawl_status)
    
    # Save crawling results
    crawl_filename = os.path.join(output_dir, f"crawl_results_{timestamp}.txt")
    save_to_file(crawl_status, crawl_filename)

if __name__ == "__main__":
    main() 