"""
This module wraps the parse function of the Element Tree library to parse XML files with a
namespace map. Element tree discards all prefixes when parsing the file.
It is used by the different parsing modules.
"""

import xml.etree.ElementTree as ET
from io import StringIO
from weakref import WeakKeyDictionary

# Global storage for namespace maps, keyed by Element objects
# Using WeakKeyDictionary so entries are automatically removed when elements are garbage collected
_ns_map_store: WeakKeyDictionary[ET.Element, dict[str, str]] = WeakKeyDictionary()


def get_ns_map(elem: ET.Element) -> dict[str, str]:
    """
    Get the namespace map for an element.
    :param elem: The XML element
    :return: The namespace prefix to URI mapping dict
    """
    return _ns_map_store.get(elem, {})


def set_ns_map(elem: ET.Element, ns_map: dict[str, str]) -> None:
    """
    Set the namespace map for an element.
    :param elem: The XML element
    :param ns_map: The namespace prefix to URI mapping dict
    """
    _ns_map_store[elem] = ns_map


def parse_file(file: str | StringIO) -> ET.ElementTree:
    """
    Parses a file, returns the Root element with namespace maps stored for each element.
    Use get_ns_map(element) to retrieve the namespace map for any element.
    :param file: either the file path (str) or a file-like object
    :return: The parsed ElementTree
    """
    events = "start", "start-ns", "end-ns"

    root = None
    ns_map: list[tuple[str, str]] = []

    for event, elem in ET.iterparse(file, events):
        if event == "start-ns":
            # elem is a tuple[str, str] when event is "start-ns"
            ns_map.append(elem)  # type: ignore[arg-type]
        elif event == "end-ns":
            ns_map.pop()
        elif event == "start":
            if root is None:
                root = elem
            set_ns_map(elem, dict(ns_map))

    return ET.ElementTree(root)
