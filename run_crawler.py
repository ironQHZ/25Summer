from main_crawler import GuidanceCrawler
import argparse


def main():
    parser = argparse.ArgumentParser(description='Crawl medical guidance website for PDFs.')
    parser.add_argument('--url', type=str,
                        default='https://www.lcgdbzz.org/custom/showZNGS',
                        help='Base URL of the guidance website')
    parser.add_argument('--start-page', type=int, default=1,
                        help='Page number to start crawling from')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Maximum number of pages to crawl (default: all pages)')
    parser.add_argument('--download-dir', type=str, default='./',
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
        def _original_get_total_pages(self):
            total = super(GuidanceCrawler, self)._get_total_pages()
            return min(total, args.start_page + args.max_pages - 1)

        # Replace the method
        import types
        crawler._get_total_pages = types.MethodType(_original_get_total_pages, crawler)

    # Start the crawler
    crawler.start()


if __name__ == "__main__":
    main()