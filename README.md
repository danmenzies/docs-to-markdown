# Docs to Markdown

Docs to Markdown is a Python tool designed to scrape website content, specifically documentation, and save the content into a single markdown file. The scraped Markdown files can then be used as source data for custom GPTs, facilitating the creation of tailored language models with domain-specific knowledge.

## Features

- Scrapes website content starting from a given URL.
- Extracts the main content from web pages using common CSS selectors (or by querying the OpenAI API, if it can't figure out where the content is).
- Converts HTML content to Markdown format.
- Saves the Markdown content in a structured directory.
- Compiles all individual Markdown files into a single Markdown file.
- Configurable to ignore content after a specified string.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/danmenzies/docs-to-markdown.git
   cd docs-to-markdown
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install the dependencies**:
   ```bash
   pip install .
   ```

4. **Set up environment variables**:
   - Open the `.env` file and add your OpenAI API key:
     ```bash
     OPENAI_API_KEY=your_openai_api_key
     OPENAI_MODEL=gpt-4  # or any other model you prefer
     ```

## Usage

To use the Docs to Markdown tool, you can run the command-line interface as follows:

```bash
python main.py --start <URL> [--ignore_after <STRING>] [--debug]
```

### Arguments

- `--start`: The starting URL for the scraper (required).
- `--ignore_after`: A string after which content should be ignored (optional).
- `--debug`: Enable debug mode with a visible browser (optional).

### Examples

1. **Basic Usage**:
   ```bash
   scrape-website --start https://example.com/docs
   ```

2. **Ignoring Content After a Specific String**:
   ```bash
   scrape-website --start https://example.com/docs --ignore_after "Footer"
   ```

3. **Enabling Debug Mode**:
   ```bash
   scrape-website --start https://example.com/docs --debug
   ```

### Output

The tool will scrape the content from the specified URL and save it as Markdown files in the `downloaded` directory. It will also compile all individual Markdown files into a single Markdown file in the same directory.

## Project Structure

- `setup.py`: Script for setting up the package, including dependencies and entry points.
- `main.py`: Entry point for the command-line interface.
- `src/`: Directory containing the core modules.
  - `__init__.py`: Indicates that `src` is a Python package.
  - `utils.py`: Utility functions for saving and compiling Markdown files, converting HTML to Markdown, and sanitizing filenames.
  - `scraper.py`: Core scraper module for extracting and saving website content.

## License

This project is licensed under the MIT License.

## Author

Dan Menzies - [dan.menzies@gmail.com](mailto:dan.menzies@gmail.com)

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue on GitHub.

## Acknowledgements

- [Selenium](https://www.selenium.dev/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [OpenAI](https://www.openai.com/)
- [Markdownify](https://pypi.org/project/markdownify/)

---

By using Docs to Markdown, you can easily scrape and convert web-based documentation into Markdown format, providing a convenient way to compile and use this content for custom GPT models.

### Invitation to Contributors

We invite developers and enthusiasts to contribute to Docs to Markdown. Whether you have suggestions for new features, improvements to existing functionalities, or bug fixes, your contributions are highly valued. Feel free to fork the repository, submit pull requests, or open issues with any ideas or problems you encounter. Together, we can enhance this tool and make documentation scraping and conversion even more efficient and effective.