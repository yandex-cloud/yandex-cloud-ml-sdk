from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Final, Union

MAX_RECURSION_DEPTH: Final = 255
MAX_RECURSION_TEXT: Final = '<recursive parsing max depth reached>'
NestedDict = dict[str, Union[str, 'NestedDict']]


def get_element_text(element: ET.Element, depth: int = 0) -> str:
    """:meta private:

    Get an XML element and get its text and text of all descendants
    and join it.
    """
    if depth >= MAX_RECURSION_DEPTH:
        return MAX_RECURSION_TEXT

    parts = []
    if element.text:
        parts.append(element.text)

    for child in element:
        parts.append(
            get_element_text(child, depth + 1)
        )

    if element.tail:
        parts.append(element.tail)

    return ''.join(parts).rstrip('\n')


def get_subelement_text(subroot: ET.Element | None, name: str) -> str | None:
    """:meta private:

    Get text from some named subelement of given subroot;
    In case of lackage of such subelement returns None.
    """

    if subroot is None:
        return None

    element = subroot.find(name)
    if element is None:
        return None

    return get_element_text(element)


def get_element_text_dict(subroot: ET.Element | None) -> NestedDict:
    if subroot is None:
        return {}

    result: NestedDict = {}

    for element in subroot:
        if (
            element.text and element.text.strip()
            or element.tail and element.tail.strip()
        ):
            value = get_element_text(element)
            if value:
                result[element.tag] = value
        elif element and len(element) > 0:
            result[element.tag] = get_element_text_dict(element)

    return result
