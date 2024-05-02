# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../tsbot/"))
sys.path.append(os.path.abspath("./ext"))

# -- Project information -----------------------------------------------------


import datetime

project = "TSBot"
copyright = "{}, 0x4aK".format(datetime.date.today().year)
author = "0x4aK"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx_rtd_theme",
    "myst_parser",
    "autodoc-decoratormethod",
]

source_suffix = {
    ".md": "markdown",
    ".txt": "markdown",
    ".rst": "restructuredtext",
}

# -- AutoDoc Options --------------------
autodoc_typehints = "signature"
autodoc_member_order = "bysource"
autodoc_preserve_defaults = True
autoclass_content = "both"


# -- MyST Options -----------------------
myst_heading_anchors = 3
myst_enable_extensions = [
    "substitution",
]

# -- Intersphinx Options ----------------
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["./templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["./static"]

html_css_files = ["custom.css"]
html_js_files = ["custom.js"]
