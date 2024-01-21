# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import iamai
from iamai import __version__
project = "IamAI"
release = __version__
copyright = "2023-PRESENT, Retrofor Wut?"
author = "Hsiang Nianian"
# html_title = "Who am I? I am AI."

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_logo = "https://cdn.jsdelivr.net/gh/retrofor/iamai@master/docs/public/retro.png"
html_favicon = html_logo

html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

html_theme_options = {
    "announcement": "<em>p<a href='#'>playground</a> is still under construction now, welcome any <a href='./pages/development/contributing.html'>contribution</a>!</em>",
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
