import os
import re
import time
import random
from openai import OpenAI
from urllib.parse import urljoin, urlparse, urldefrag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
from dotenv import load_dotenv, find_dotenv
from src.utils import save_markdown_file, compile_markdown_files, convert_html_to_markdown, sanitize_filename

load_dotenv(find_dotenv())


class Scraper:
    """
    A class to scrape the main content from a website.

    :param debug: If True, enable debug mode.
    """

    DOM_SELECTORS = [
        "main",  # HTML5 main element
        "article",  # HTML5 article element
        "div#content",  # Common content div
        "div.content",  # Common content div
        "div.main-content",  # Common content div
        "div.post",  # Common post div
        "section.content",  # Common content section
        "section.main-content",  # Common content section
        "section.post",  # Common post section
        "#markdown-page",  # Common markdown page
    ]

    def __init__(self, debug=False):
        self.debug = debug
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.browser = self.init_browser()

    def init_browser(self):
        """
        Initialize a Chrome browser instance with optional headless mode.

        :return: A Selenium WebDriver instance.
        """
        chrome_options = Options()
        if not self.debug:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chromedriver_autoinstaller.install()
        return webdriver.Chrome(options=chrome_options)

    def get_main_content_selector(self, url='', soup=None):
        """
        Get the CSS selector for the main content on the webpage using common patterns and OpenAI's ChatCompletion API.

        :param url: The URL of the webpage.
        :param soup: The BeautifulSoup object of the webpage.
        :return: The CSS selector as a string.
        """
        if soup:
            for selector in self.DOM_SELECTORS:
                elements = soup.select(selector)
                if elements and all(element.get_text(strip=True) for element in elements):
                    return selector

        return self._fetch_selector_from_openai(url, soup)

    def _fetch_selector_from_openai(self, url, soup):
        """
        Fetch the CSS selector from OpenAI's ChatCompletion API.

        :param url: The URL of the webpage.
        :param soup: The BeautifulSoup object of the webpage.
        :return: The CSS selector as a string.
        """
        messages = [
            {"role": "system", "content":
                "You are a web scraping assistant, who's part of a larger automation project. Your task is to provide the "
                "CSS selector for the main content on a webpage."},
            {"role": "assistant",
             "content": "Please provide me with the DOM structure of the main content on the target web page"},
            {"role": "user", "content": str(soup.prettify())},
            {"role": "assistant", "content": "Thank you. What's next?"},
            {"role": "user", "content":
                "Please analyze the DOM structure and provide the CSS selector for the main content body, preferably "
                "excluding headers, footers, nav bars, and other UI Elements; we ONLY want to select the main article or "
                "main content (ie, the \"meat\" of the page content). Please ONLY return the CSS selector, and nothing "
                "else. Your output will be used by an automated system, to gather the page's content; it is imperative that "
                "you provide the correct CSS selector, and ONLY the CSS selector."}
        ]

        backoff = 0
        backoff_next = 30
        backoff_factor = 0.5
        backoff_max = 5

        while backoff < backoff_max:
            try:
                response = self.client.chat_completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                    messages=messages,
                    max_tokens=10,
                    temperature=0.3
                )

                selector = str(response.choices[0].message.content).strip()
                if soup.select(selector) and all(element.get_text(strip=True) for element in soup.select(selector)):
                    print(f"Generated selector for URL: {url}")
                    self.DOM_SELECTORS.append(selector)
                    return selector

            except Exception as e:
                if self.debug:
                    print(f"Unexpected error: {e}")
                    return None

                backoff += 1
                time.sleep(backoff_next)
                backoff_next *= backoff_factor

        return None

    def scrape_website(self, start_url, ignore_after=None):
        """
        Scrape the website starting from the given URL and save the content as markdown files.

        :param start_url: The starting URL for the scraper.
        :param ignore_after: The string after which content should be ignored.
        """
        normalized_start_url = self.normalize_url(start_url)
        base_path = os.path.join('downloaded', os.path.dirname(normalized_start_url.replace('/', os.sep)))

        starting_point = start_url.split('/')[-1]
        cwd = os.getcwd()
        domain_root = normalized_start_url.split('/')[0]
        compiled_markdown_path = os.path.join(cwd, 'downloaded', domain_root, starting_point + '.md')

        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        to_scrape = [start_url]
        scraped = set()

        while to_scrape:
            url = to_scrape.pop(0)
            if url in scraped:
                continue

            scraped.add(url)
            self.browser.get(url)

            if self.browser.title.lower() == '404 not found':
                print(f"404 error encountered at URL: {url}")
                continue

            soup = BeautifulSoup(self.browser.page_source, 'html.parser')
            self.make_urls_absolute_and_encode(soup, url)

            content_selector = self.get_main_content_selector(url, soup)
            if content_selector:
                main_content = soup.select_one(content_selector)
                main_content_html = str(main_content.prettify())
                markdown_content = convert_html_to_markdown(main_content_html, ignore_after)
                save_markdown_file(url, markdown_content, base_path)
            else:
                print(f"Failed to retrieve content selector for URL: {url}")
                continue

            links = soup.find_all('a', href=True)
            for link in links:
                new_url = urljoin(url, urldefrag(link['href'])[0])
                parsed_new_url = urlparse(new_url)
                parsed_start_url = urlparse(start_url)
                if new_url.startswith(
                        start_url) and new_url not in scraped and parsed_new_url.netloc == parsed_start_url.netloc:
                    to_scrape.append(new_url)

            wait_for = random.randint(1, 5)
            print(f'Waiting for {wait_for} seconds...')
            time.sleep(wait_for)

        compile_markdown_files(base_path, compiled_markdown_path)
        self.browser.quit()

    @staticmethod
    def normalize_url(url):
        """
        Normalize a URL by removing the protocol and trailing slash.

        :param url: The URL to normalize.
        :return: The normalized URL.
        """
        return re.sub(r'^(?:https?://)?(?:www\.)?', '', url).rstrip('/')

    @staticmethod
    def make_urls_absolute_and_encode(soup, base_url):
        """
        Convert all URLs (images and links) in the BeautifulSoup object to absolute URLs and encode them.

        :param soup: The BeautifulSoup object.
        :param base_url: The base URL to join with relative URLs.
        """
        for tag in soup.find_all(['img', 'a']):
            if tag.has_attr('src'):
                tag['src'] = urljoin(base_url, tag['src'])
                tag['src'] = re.sub(r' ', '%20', tag['src'])
            if tag.has_attr('href'):
                tag['href'] = urljoin(base_url, tag['href'])
                tag['href'] = re.sub(r' ', '%20', tag['href'])
