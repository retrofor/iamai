# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

# DATA = None
# PYPROJECT = os.path.join("..", "..", "cargo.toml")
# with open(PYPROJECT, "r", encoding="utf8") as f:
#     pyproject = f.read()
#     DATA = tomllib.loads(pyproject)
# print(DATA)
# PROJECT_VERSION = DATA["package"]["version"]
# PROJECT_NAME = DATA["project"]["name"]
# AUTHOR_TABLE = DATA["project"]["authors"]
# AUTHORS = ",".join([f"{aut['name']}<{aut['email']}>" for aut in AUTHOR_TABLE])

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Comprehensive AI Toolkit" # PROJECT_NAME
# release = PROJECT_VERSION
copyright = "2023-PRESENT, Retrofor Wut?"
author = "HsiangNianian"  # AUTHORS

html_title = "Comprehensive AI Toolkit"

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
    'sphinx_last_updated_by_git',
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
extlinks = {
    "issue": ("https://github.com/retrofor/iamai/%s", "issue %s"),
    "doc": ("https://iamai.is-a.dev/en/latest/%s", "pages/%s"),
}
source_suffix = {
    ".rst": "restructuredtext",
    ".txt": "markdown",
    ".md": "markdown",
}

locale_dirs = ["../locales/"]  # path is example but recommended.
gettext_compact = False  # optional.
gettext_uuid = True  # optional.
translation_progress_classes = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["../_static"]
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
    "source_directory": "docs/source/",
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

#
# The following code was added during an automated build on readthedocs.org
# It is auto created and injected for every build. The result is based on the
# conf.py.tmpl file found in the readthedocs.org codebase:
# https://github.com/rtfd/readthedocs.org/blob/main/readthedocs/doc_builder/templates/doc_builder/conf.py.tmpl
#
# Note: this file shouldn't rely on extra dependencies.

import sys  # noqa: E402
import os.path  # noqa: E402

# User's Sphinx configurations
language_user = globals().get("language", None)
latex_engine_user = globals().get("latex_engine", None)
latex_elements_user = globals().get("latex_elements", None)

# Remove this once xindy gets installed in Docker image and XINDYOPS
# env variable is supported
# https://github.com/rtfd/readthedocs-docker-images/pull/98
latex_use_xindy = False
