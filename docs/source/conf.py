import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "SecondBrain"
copyright = "2024, Your Name"
author = "Your Name"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"
html_static_path = ["_static"]

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_format = "short"

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
