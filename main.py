import argparse
from src.scraper import Scraper

def main():
    """
    Main function to run the website content scraper.
    :return:
    """
    parser = argparse.ArgumentParser(description="Website Content Scraper")
    parser.add_argument('--start', required=True, help='Starting URL for the scraper')
    parser.add_argument('--ignore_after', required=False, help='Ignore this line of text, and everything after it')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with visible browser')
    parser.add_argument('--slow', action='store_true', help='Slow down the scraper to avoid rate limits')
    parser.add_argument('--compile-only', action='store_true', help='Only run the compilation step')
    args = parser.parse_args()

    scraper = Scraper(debug=args.debug)
    scraper.scrape_website(args.start, args.ignore_after, args.slow, args.compile_only)

if __name__ == "__main__":
    main()
