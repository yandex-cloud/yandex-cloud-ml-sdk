from __future__ import annotations

import yandex_cloud_ml_sdk

# -- Project information -----------------------------------------------------

project = 'yandex-cloud-ml-sdk'
copyright = '2024, YANDEX LLC'
author = 'Vladimir Lipkin'
version = yandex_cloud_ml_sdk.__version__
release = yandex_cloud_ml_sdk.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.viewcode',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__call__',
    'exclude-members': '__weakref__',
    'inherited-members': True,
}
autodoc_inherit_docstrings = True
autodoc_type_aliases = {
    'BaseSDK': 'yandex_cloud_ml_sdk._sdk.BaseSDK',
    'asyncio': 'asyncio',
    'JsonArray': 'yandex_cloud_ml_sdk._types.schemas.JsonArray',
}

intersphinx_mapping = {
    'grpc': ('https://grpc.github.io/grpc/python/', None),
    'python': ('https://docs.python.org/3', None),
}

always_document_param_types = True
always_use_bars_union = True
typehints_defaults = 'comma'

nitpicky = True

nitpick_ignore = {
    ('py.class', 'integer'),
}

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']
