from main_crawler import GuidanceCrawler
import argparse
import sys


def check_requirements():
    """Check if required packages are installed."""
    try:
        import selenium
        import requests
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages using:")
        print("pip install selenium requests")
        sys.exit(1)


def main():
    check_requirements()

    parser = argparse.ArgumentParser(description='Crawl medical guidance website for PDFs.')
    parser.add_argument('--url', type=str,
                        default='https://example.com/path/to/guidance/page',
                        help='Base URL of the guidance website')
    parser.add_argument('--start-page', type=int, default=1,
                        help='Page number to start crawling from')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Maximum number of pages to crawl (default: all pages)')
    parser.add_argument('--download-dir', type=str, default='downloads',
                        help='Directory to save downloaded PDFs')

    args = parser.parse_args()

    print("Starting crawler in headless mode")
    print(f"Target URL: {args.url}")
    print(f"Starting page: {args.start_page}")
    if args.max_pages:
        print(f"Maximum pages to crawl: {args.max_pages}")

    crawler = GuidanceCrawler(args.url)
    crawler.current_page = args.start_page

    # Set max pages if specified
    if args.max_pages:
        # Store the original method
        original_get_total_pages = crawler._get_total_pages

        # Define a new method that limits the pages
        def limited_get_total_pages():
            original_total = original_get_total_pages()
            max_page = args.start_page + args.max_pages - 1
            return min(original_total, max_page)

        # Replace the method
        crawler._get_total_pages = limited_get_total_pages

    # Start the crawler
    crawler.start()


if __name__ == "__main__":
    main()