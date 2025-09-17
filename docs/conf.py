from __future__ import annotations

from sphinx.domains.python import PythonDomain

import yandex_cloud_ml_sdk
import yandex_cloud_ml_sdk._sdk

# -- Project information -----------------------------------------------------

project = 'yandex-cloud-ml-sdk'
copyright = '2024, YANDEX LLC'  # pylint: disable=redefined-builtin
author = 'Vladimir Lipkin'
version = yandex_cloud_ml_sdk.__version__
release = yandex_cloud_ml_sdk.__version__

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.viewcode',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',

    'sphinx_toolbox.more_autodoc.typevars',
    'sphinx_toolbox.more_autodoc.genericalias',
    'sphinx_toolbox.more_autodoc.autotypeddict',
    'sphinx_toolbox.more_autodoc.generic_bases',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__call__',
    'exclude-members': '__weakref__,__init__',
    'inherited-members': True,
    'undoc-members': True
}
autodoc_inherit_docstrings = True
autodoc_type_aliases = {
    'BaseSDK': 'yandex_cloud_ml_sdk._sdk.BaseSDK',
    'asyncio': 'asyncio',
    'JsonArray': 'yandex_cloud_ml_sdk._types.schemas.JsonArray',
}
autodoc_member_order = 'bysource'
autodoc_class_signature = 'separated'
autodoc_typehints = 'description'

intersphinx_mapping = {
    'grpc': ('https://grpc.github.io/grpc/python/', None),
    'python': ('https://docs.python.org/3', None),
}

nitpicky = True

nitpick_ignore = {
    ('py:class', 'datetime'),
    # This will be not needed in python 3.13+
    ('py:class', 'integer -- return number of occurrences of value'),
    ('py:class', 'integer -- return first index of value.'),
    ('py:class', 'D[k] if k in D, else d.  d defaults to None.'),
    # This is a bug of sphinx or sphinx_autodoc_typehints
    ('py:class', 'TypeAliasForwardRef'),
    ('py:class', 'sphinx.util.inspect.TypeAliasForwardRef'),
    # This leaks from CloudClient and don't really makes any interest for user
    ('py:class', 'yandex_cloud_ml_sdk._client._T'),
    ('py:class', 'yandex_cloud_ml_sdk._client._D'),
    ('py:class', 'google.protobuf.message.Message'),
    ('py:class', 'httpx.AsyncClient'),
    ('py:class', 'httpx_sse._models.ServerSentEvent'),
    # It creates a ton of langchain refs I want to pass right now
    ('py:class', 'yandex_cloud_ml_sdk._types.langchain.BaseYandexLanguageModel'),
    ('py:class', 'BaseYandexLanguageModel'),
    # Json types documented as a py:data but some autodocs refs it with py:class
    ('py:class', 'yandex_cloud_ml_sdk._types.schemas.JsonArray'),
    ('py:class', "'yandex_cloud_ml_sdk._types.schemas.JsonArray'"),
    ('py:class', 'JsonObject'),
    ('py:class', 'JsonArray'),
    ('py:class', 'JsonSchemaType'),
    ('py:class', 'ResponseType'),
}

nitpick_ignore_regex = (
    ('py:class', r".+a view on D's.+"),
    # This proto is just a parameter for some generics and don't need for user
    ('py:class', r'yandex\.cloud\.ai\..+'),
    ('py:class', r'<google\.protobuf\.internal\.enum_type_wrapper\.EnumTypeWrapper.+'),
)

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'


def setup(_):
    original_find_obj = PythonDomain.find_obj

    def patched_find_obj(self, env, modname, name, *args, **kwargs):
        if modname.startswith('yandex_cloud_ml_sdk._retry'):
            modname = modname.replace('_retry', 'retry')
        return original_find_obj(self, env, modname, name, *args, **kwargs)

    PythonDomain.find_obj = patched_find_obj
