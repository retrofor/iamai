# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import iamai
import os, sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

DATA = None
PYPROJECT = os.path.join("..", "pyproject.toml")
with open(PYPROJECT, "r", encoding="utf8") as f:
    pyproject = f.read()
    DATA = tomllib.loads(pyproject)
PROJECT_VERSION = DATA["project"]["version"]
PROJECT_NAME = DATA["project"]["name"]
AUTHOR_TABLE = DATA["project"]["authors"]
AUTHORS = ",".join([f"{aut['name']}<{aut['email']}>" for aut in AUTHOR_TABLE])
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = PROJECT_NAME  # "IamAI"
release = PROJECT_VERSION  # "latest"
copyright = "2023-PRESENT, Retrofor Wut?"
author = AUTHORS

# html_title = "Who am I? I am AI."

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.extlinks",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
extlinks = {
    "issue": ("https://github.com/retrofor/iamai/%s", "issue %s"),
    "doc": ("https://iamai.is-a.dev/en/latest/%s", "pages/%s"),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "https://cdn.jsdelivr.net/gh/retrofor/iamai@master/docs/_static/retro.png"
html_favicon = html_logo

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

html_theme_options = {
    "announcement": "<em><a href='#'>playground</a> is still under construction now, welcome any <a href='./pages/development/contributing.html'>contribution</a>!</em>",
    "source_repository": "https://github.com/retrofor/iamai/",
    "source_branch": "master",
    "source_directory": "docs/",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/retrofor/iamai/",
            "html": "",
            "class": "fa-brands fa-github",
        },
        {
            "name": "Pypi",
            "url": "https://pypi.org/project/iamai/",
            "html": "",
            "class": "fa-brands fa-python",
        },
    ],
}
