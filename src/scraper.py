import os
import re
import time
import random
import tiktoken
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
        "#ja-current-content", # GTA Base
        "#ja-content", # GTA Base
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
        "#main"
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
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)")

        if not self.debug:
            chrome_options.add_argument("--headless")

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

        def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
            """Returns the number of tokens in a text string."""
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(string))
            return num_tokens

        def truncate_content(content: str, max_tokens: int = 6000) -> str:
            """Truncates content to fit within max_tokens."""
            while num_tokens_from_string(content) > max_tokens:
                content = content[:int(len(content) * 0.9)]  # Reduce by 10% each iteration
            return content

        dom_content = str(soup.prettify())
        truncated = False
        if num_tokens_from_string(dom_content) > 6000:
            dom_content = truncate_content(dom_content)
            truncated = True

        system_message = "You are a web scraping assistant, who's part of a larger automation project. Your task is to provide the CSS selector for the main content on a webpage."
        user_message = (
            "Please analyze the DOM structure and provide the CSS selector for the main content body, preferably "
            "excluding headers, footers, nav bars, and other UI Elements; we ONLY want to select the main article or "
            "main content (ie, the \"meat\" of the page content). Please ONLY return the CSS selector, and nothing "
            "else. Your output will be used by an automated system, to gather the page's content; it is imperative that "
            "you provide the correct CSS selector, and ONLY the CSS selector.")

        if truncated:
            user_message = "NOTE: The DOM structure provided is truncated due to length constraints. " + user_message

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": dom_content},
            {"role": "user", "content": user_message}
        ]

        backoff = 0
        backoff_next = 30
        backoff_factor = 0.5
        backoff_max = 5

        while backoff < backoff_max:
            try:
                response = self.client.chat.completions.create(
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

                backoff += 1
                time.sleep(backoff_next)
                backoff_next *= backoff_factor

        print(f"Failed to retrieve content selector for URL: {url}")
        return None

    def scrape_website(self, start_url, ignore_after=None, slow=None, compile_only=None):
        """
        Scrape the website starting from the given URL and save the content as markdown files.

        :param start_url: The starting URL for the scraper.
        :param ignore_after: The string after which content should be ignored.
        :param slow: Slow down the scraper to avoid rate limits.
        :param compile_only: Only run the compilation step.
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

        # If compile_only is set, compile the markdown files and exit
        if compile_only is not None and compile_only:
            compile_markdown_files(base_path, compiled_markdown_path)
            return None

        # Set the first flag
        first = True

        while to_scrape:
            url = to_scrape.pop(0)
            if url in scraped:
                continue

            scraped.add(url)
            self.browser.get(url)

            # If we're debugging, give the end user a chance to inspect the page
            if self.debug and first:
                input("Press Enter to continue...")

            first = False

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

            # Set up a random wait time to avoid rate limits
            wait_for = random.randint(1, 5)
            if slow:
                wait_for = random.randint(20, 35)

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
