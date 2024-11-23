# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2] / 'src'))
from net_dl import __version__  # noqa: E402

project = 'net-dl'
copyright = '2024, SIL Global'
author = 'Nate Marti'
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
]

# AutoAPI configuration
# https://sphinx-autoapi.readthedocs.io/en/latest/reference/config.html
autoapi_dirs = ['../../src/net_dl']
autoapi_options = [
    'members',
    # 'undoc-members',
    # 'private-members',
    # 'show-inheritance',
    'show-module-summary',
    # 'special-members',
    # 'imported-members',
]
autoapi_own_page_level = 'module'  # 'class'
autoapi_member_order = 'bysource'  # 'groupwise'

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'haiku'
html_theme = 'alabaster'  # default
html_static_path = ['_static']
