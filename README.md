# Gitingest

[![Image](./docs/frontpage.png "Gitingest main page")](https://gitingest.com)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/cyclotruc/gitingest/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/gitingest.svg)](https://badge.fury.io/py/gitingest)
[![GitHub stars](https://img.shields.io/github/stars/cyclotruc/gitingest?style=social.svg)](https://github.com/cyclotruc/gitingest)
[![Downloads](https://pepy.tech/badge/gitingest)](https://pepy.tech/project/gitingest)

[![Discord](https://dcbadge.limes.pink/api/server/https://discord.com/invite/zerRaGK9EC)](https://discord.com/invite/zerRaGK9EC)

Turn any Git repository into a prompt-friendly text ingest for LLMs.

You can also replace `hub` with `ingest` in any GitHub URL to access the corresponding digest.

[gitingest.com](https://gitingest.com) · [Chrome Extension](https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood) · [Firefox Add-on](https://addons.mozilla.org/firefox/addon/gitingest)

## 🚀 Features

- **Easy code context**: Get a text digest from a Git repository URL or a directory
- **Smart Formatting**: Optimized output format for LLM prompts
- **Statistics about**:
  - File and directory structure
  - Size of the extract
  - Token count
- **CLI tool**: Run it as a shell command
- **Python package**: Import it in your code

## 📚 Requirements

- Python 3.8+
- For private repositories: A GitHub Personal Access Token (PAT). You can generate one at [https://github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens) (Profile → Settings → Developer Settings → Personal Access Tokens → Fine-grained Tokens)

### 📦 Installation

Gitingest is available on [PyPI](https://pypi.org/project/gitingest/).
You can install it using `pip`:

```bash
pip install gitingest
```

However, it might be a good idea to use `pipx` to install it.
You can install `pipx` using your preferred package manager.

```bash
brew install pipx
apt install pipx
scoop install pipx
...
```

If you are using pipx for the first time, run:

```bash
pipx ensurepath
```

```bash
# install gitingest
pipx install gitingest
```

## 🧩 Browser Extension Usage

<!-- markdownlint-disable MD033 -->
<a href="https://chromewebstore.google.com/detail/adfjahbijlkjfoicpjkhjicpjpjfaood" target="_blank" title="Get Gitingest Extension from Chrome Web Store"><img height="48" src="https://github.com/user-attachments/assets/20a6e44b-fd46-4e6c-8ea6-aad436035753" alt="Available in the Chrome Web Store" /></a>
<a href="https://addons.mozilla.org/firefox/addon/gitingest" target="_blank" title="Get Gitingest Extension from Firefox Add-ons"><img height="48" src="https://github.com/user-attachments/assets/c0e99e6b-97cf-4af2-9737-099db7d3538b" alt="Get The Add-on for Firefox" /></a>
<a href="https://microsoftedge.microsoft.com/addons/detail/nfobhllgcekbmpifkjlopfdfdmljmipf" target="_blank" title="Get Gitingest Extension from Microsoft Edge Add-ons"><img height="48" src="https://github.com/user-attachments/assets/204157eb-4cae-4c0e-b2cb-db514419fd9e" alt="Get from the Edge Add-ons" /></a>
<!-- markdownlint-enable MD033 -->

The extension is open source at [lcandy2/gitingest-extension](https://github.com/lcandy2/gitingest-extension).

Issues and feature requests are welcome to the repo.

## 💡 Command line usage

The `gitingest` command line tool allows you to analyze codebases and create a text dump of their contents.

```bash
# Basic usage (writes to digest.txt by default)
gitingest /path/to/directory

# From URL
gitingest https://github.com/cyclotruc/gitingest

# or from specific subdirectory
gitingest https://github.com/cyclotruc/gitingest/tree/main/src/gitingest/utils
```

For private repositories, use the `--token/-t` option.

```bash
# Get your token from https://github.com/settings/personal-access-tokens
gitingest https://github.com/username/private-repo --token github_pat_...

# Or set it as an environment variable
export GITHUB_TOKEN=github_pat_...
gitingest https://github.com/username/private-repo
```

By default, the digest is written to a text file (`digest.txt`) in your current working directory. You can customize the output in two ways:

- Use `--output/-o <filename>` to write to a specific file.
- Use `--output/-o -` to output directly to `STDOUT` (useful for piping to other tools).

See more options and usage details with:

```bash
gitingest --help
```

## 🐍 Python package usage

```python
# Synchronous usage
from gitingest import ingest

summary, tree, content = ingest("path/to/directory")

# or from URL
summary, tree, content = ingest("https://github.com/cyclotruc/gitingest")

# or from a specific subdirectory
summary, tree, content = ingest("https://github.com/cyclotruc/gitingest/tree/main/src/gitingest/utils")
```

For private repositories, you can pass a token:

```python
# Using token parameter
summary, tree, content = ingest("https://github.com/username/private-repo", token="github_pat_...")

# Or set it as an environment variable
import os
os.environ["GITHUB_TOKEN"] = "github_pat_..."
summary, tree, content = ingest("https://github.com/username/private-repo")
```

By default, this won't write a file but can be enabled with the `output` argument.

```python
# Asynchronous usage
from gitingest import ingest_async
import asyncio

result = asyncio.run(ingest_async("path/to/directory"))
```

### Jupyter notebook usage

```python
from gitingest import ingest_async

# Use await directly in Jupyter
summary, tree, content = await ingest_async("path/to/directory")

```

This is because Jupyter notebooks are asynchronous by default.

## 🛠️ Local Development

### Prerequisites

- Python 3.8+ (Python 3.12 recommended)
- Git (required for repository cloning)
- Node.js (optional, for frontend development)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cyclotruc/gitingest.git
   cd gitingest
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development tools
   ```

4. **Set up environment variables (optional):**
   ```bash
   # Create a .env file for local configuration
   echo "GITHUB_TOKEN=your_github_token_here" > .env
   echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env
   ```

### Running the Development Server

Start the FastAPI development server:

```bash
# From the project root directory
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000 --reload
```

The application will be available at:
- **Main interface:** `http://localhost:8000`
- **Tree Explorer:** `http://localhost:8000/tree-explorer`
- **API Documentation:** `http://localhost:8000/api`
- **Health Check:** `http://localhost:8000/health`

### Development Tools

- **Linting:** `black . && pylint src/`
- **Testing:** `pytest tests/`
- **Pre-commit hooks:** `pre-commit install && pre-commit run --all-files`

### Features Available in Development

1. **Web Interface:** Browse and analyze repositories through the web UI
2. **Tree Explorer:** Interactive D3.js visualization of repository structure
3. **CLI Tool:** Use `gitingest` command for local analysis
4. **API Endpoints:** RESTful API for programmatic access

### Troubleshooting

- **Port already in use:** Change the port: `--port 8001`
- **Rate limiting issues:** Increase limits in `server/server_utils.py`
- **Static files not loading:** Ensure you're running from the project root
- **Repository cloning fails:** Check your GitHub token and network connectivity

## 🐳 Self-host

1. Build the image:

   ``` bash
   docker build -t gitingest .
   ```

2. Run the container:

   ``` bash
   docker run -d --name gitingest -p 8000:8000 gitingest
   ```

The application will be available at `http://localhost:8000`.

If you are hosting it on a domain, you can specify the allowed hostnames via env variable `ALLOWED_HOSTS`.

   ```bash
   # Default: "gitingest.com, *.gitingest.com, localhost, 127.0.0.1".
   ALLOWED_HOSTS="example.com, localhost, 127.0.0.1"
   ```

## 🤝 Contributing

### Non-technical ways to contribute

- **Create an Issue**: If you find a bug or have an idea for a new feature, please [create an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub. This will help us track and prioritize your request.
- **Spread the Word**: If you like Gitingest, please share it with your friends, colleagues, and on social media. This will help us grow the community and make Gitingest even better.
- **Use Gitingest**: The best feedback comes from real-world usage! If you encounter any issues or have ideas for improvement, please let us know by [creating an issue](https://github.com/cyclotruc/gitingest/issues/new) on GitHub or by reaching out to us on [Discord](https://discord.com/invite/zerRaGK9EC).

### Technical ways to contribute

Gitingest aims to be friendly for first time contributors, with a simple Python and HTML codebase. If you need any help while working with the code, reach out to us on [Discord](https://discord.com/invite/zerRaGK9EC). For detailed instructions on how to make a pull request, see [CONTRIBUTING.md](./CONTRIBUTING.md).

## 🛠️ Stack

- [Tailwind CSS](https://tailwindcss.com) - Frontend
- [FastAPI](https://github.com/fastapi/fastapi) - Backend framework
- [Jinja2](https://jinja.palletsprojects.com) - HTML templating
- [tiktoken](https://github.com/openai/tiktoken) - Token estimation
- [posthog](https://github.com/PostHog/posthog) - Amazing analytics

### Looking for a JavaScript/FileSystemNode package?

Check out the NPM alternative 📦 Repomix: <https://github.com/yamadashy/repomix>

## 🚀 Project Growth

[![Star History Chart](https://api.star-history.com/svg?repos=cyclotruc/gitingest&type=Date)](https://star-history.com/#cyclotruc/gitingest&Date)
