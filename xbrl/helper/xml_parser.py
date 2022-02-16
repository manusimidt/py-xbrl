"""
This module wraps the parse function of the Element Tree library to parse XML files with a
namespace map. Element tree discards all prefixes when parsing the file.
It is used by the different parsing modules.
"""
import xml.etree.ElementTree as ET


def parse_file(path: str) -> ET.ElementTree:
    """
    Parses a file, returns the Root element with an attribute 'ns_map' containing the prefix - namespaces map
    @return:
    """
    events = "start", "start-ns", "end-ns"

    root = None
    ns_map = []

    for event, elem in ET.iterparse(path, events):
        if event == "start-ns":
            ns_map.append(elem)
        elif event == "end-ns":
            ns_map.pop()
        elif event == "start":
            if root is None:
                root = elem
            elem.set('ns_map', dict(ns_map))

    return ET.ElementTree(root)


