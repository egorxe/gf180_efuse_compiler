# Configuration file for the Sphinx documentation builder.

# -- Project information -----------------------------------------------------

import os

project = 'GF180MCU eFuse compiler'
copyright = '2026, egorxe'
author = 'egorxe'
release = '0.1'

# -- General configuration ---------------------------------------------------

extensions = [ 'myst_parser', 'sphinxcontrib.rsvgconverter' ]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

myst_heading_anchors = 2

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']

html_title = "GF180MCU eFuse compiler documentation v." + release

# add PDF to HTML if running from CI
html_extra_path = ["_build/latex/gf180mcuefusecompiler.pdf"] if "CI" in os.environ else []

# -- Options for PDF output --------------------------------------------------

latex_elements = {
  'extraclassoptions': 'openany,oneside'
}
