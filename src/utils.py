import os
import html2text
import markdownify
import re

def save_markdown_file(url, content, base_path):
    """
    Save the content of a URL as a markdown file.

    :param url: The URL of the content.
    :param content: The content to save.
    :param base_path: The base directory to save the file in.
    """
    normalized_url = url.replace('https://', '').replace('http://', '').rstrip('/')
    file_path = os.path.join('downloaded', normalized_url.replace('/', os.sep) + '.md')

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)


def compile_markdown_files(base_path, compiled_markdown_path):
    """
    Compile all markdown files in the base_path into a single markdown file.

    :param base_path: The base directory containing markdown files.
    :param compiled_markdown_path: The path to save the compiled markdown file.
    """
    with open(compiled_markdown_path, 'w', encoding='utf-8') as compiled_file:
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        compiled_file.write(f.read())
                        compiled_file.write('\n\n')


def convert_html_to_markdown(html_content, ignore_after=None):
    """
    Convert HTML content to Markdown, ignoring content after the specified string.

    :param html_content: The HTML content to convert.
    :param ignore_after: The string after which content should be ignored.
    :return: The converted Markdown content.
    """
    markdown_content = markdownify.markdownify(html_content, heading_style="ATX")

    if ignore_after:
        ignore_index = markdown_content.find(ignore_after)
        if ignore_index != -1:
            markdown_content = markdown_content[:ignore_index]

    return markdown_content



def sanitize_filename(filename):
    """
    Sanitize the filename by removing invalid characters.

    :param filename: The filename to sanitize.
    :return: The sanitized filename.
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[#%&{}\\<>*?/ $!\'":@+`|=]', '', filename)
    return filename
