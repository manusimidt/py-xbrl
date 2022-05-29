"""
This module wraps the parse function of the Element Tree library to parse XML files with a
namespace map. Element tree discards all prefixes when parsing the file.
It is used by the different parsing modules.
"""
import xml.etree.ElementTree as ET
from io import StringIO, IOBase


def parse_file(file: str or IOBase or StringIO) -> ET.ElementTree:
    """
    Parses a file, returns the Root element with an attribute 'ns_map' containing the prefix - namespaces map
    :param file: either the file path (str) or a file-like object
    @return:
    """
    events = "start", "start-ns", "end-ns"

    root = None
    ns_map = []

    # sets the file pointer back to the beginning in case it was read from multiple times
    if isinstance(file, IOBase):
        file.seek(0, 0)

    for event, elem in ET.iterparse(file, events):
        if event == "start-ns":
            ns_map.append(elem)
        elif event == "end-ns":
            ns_map.pop()
        elif event == "start":
            if root is None:
                root = elem
            elem.set('ns_map', dict(ns_map))

    return ET.ElementTree(root)
