# Web PDF Crawler

A simple tool to automatically browse through web pages and download PDF files.

## Requirements

1. Python 3.6 or higher
2. Chrome browser
3. Two Python packages:
pip install selenium requests
4. ChromeDriver: Download from [here](https://sites.google.com/chromium.org/driver/) (must match your Chrome version)

## Quick Start

1. Save all three Python files (`main_crawler.py`, `pdf_downloader.py`, `run_crawler.py`) in the same folder

2. Run the crawler:
python run_crawler.py --url "https://example.com/path/to/page"

3. PDFs will be saved to the "downloads" folder by default

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