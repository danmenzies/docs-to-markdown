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
    args = parser.parse_args()

    scraper = Scraper(debug=args.debug)
    scraper.scrape_website(args.start, args.ignore_after)

if __name__ == "__main__":
    main()
