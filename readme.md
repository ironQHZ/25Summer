# Web PDF Crawler for Journal of Clinical Hepatology

A simple tool to automatically browse through web pages and download PDF files from Journal of Clinical Hepatology's webpage.

## Requirements

1. Chrome browser
pip install selenium requests
2. ChromeDriver: Download from [here](https://sites.google.com/chromium.org/driver/) (must match your Chrome version)

## Quick Start

1. Run the crawler:
python run_crawler.py --url "https://www.lcgdbzz.org/custom/showZNGS"

2. PDFs will be saved to the "downloads" folder by default

## Optional Arguments

- Start from a specific page:
python run_crawler.py --url "https://example.com" --start-page 3

- Limit how many pages to crawl:
python run_crawler.py --url "https://example.com" --max-pages 5

- Change where PDFs are saved:
python run_crawler.py --url "https://example.com" --download-dir "my_pdfs"

## Troubleshooting

- If no PDFs are found, the website may have a different structure than expected
- The program runs in headless mode (no visible browser) by default
- If you get errors, try updating ChromeDriver to match your Chrome version