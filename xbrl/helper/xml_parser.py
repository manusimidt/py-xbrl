"""
This module wraps the parse function of the Element Tree library to parse XML files with a
namespace map. Element tree discards all prefixes when parsing the file.
It is used by the different parsing modules.
"""
import lxml.html
from lxml import etree as ET

def parse_file(path: str) -> ET:
    """
    Parses a file, returns the Root element with an attribute 'ns_map' containing the prefix - namespaces map
    @return:
    """

    # parse even html as xml to retain namespace, otherwise ignores it 
    # https://stackoverflow.com/questions/6597271/how-to-preserve-namespace-information-when-parsing-html-with-lxml
    # parse as xml, xsd
    tree = ET.parse(path)

    return ET.ElementTree(tree.getroot())
 