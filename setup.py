import os
import shutil
from setuptools import setup, find_packages

# Remove previous installations
removable = [
    "dist",
    "build",
    "docs_to_markdown.egg-info"
]
for item in removable:
    if os.path.exists(item):
        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

# Read the content of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Call the setup function
setup(
    name="docs_to_markdown",
    version="1.0.0",
    author="Dan Menzies",
    author_email="dan.menzies@gmail.com",
    description="A tool to scrape website content and save it as markdown files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/danmenzies/docs-to-markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "selenium",
        "chromedriver-autoinstaller",
        "python-dotenv",
        "openai==1.11.1",
        "beautifulsoup4",
        "requests",
        "markdown",
        "html2text",
        "markdownify",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'scrape-website=main:main',
        ],
    },
)

# Copy the .env.example file to .env, if it doesn't already exist
env_path = os.path.join(this_directory, ".env")
example_path = os.path.join(this_directory, ".env.example")
if not os.path.exists(env_path):
    with open(example_path, "r") as example_env_file:
        with open(env_path, "w") as env_file:
            env_file.write(example_env_file.read())
