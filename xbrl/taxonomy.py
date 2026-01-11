"""
This module contains all classes and functions necessary for parsing Taxonomy schema files.
"""

import json
import logging
import os
import xml.etree.ElementTree as ET
from functools import lru_cache
from urllib.parse import unquote

from xbrl import TaxonomyNotFound, XbrlParseException
from xbrl.cache import HttpCache
from xbrl.helper.uri_helper import compare_uri, is_url, resolve_uri
from xbrl.linkbase import ExtendedLink, Label, Linkbase, LinkbaseType, parse_linkbase, parse_linkbase_url
from xbrl.ns_map import NS_MAP

logger = logging.getLogger(__name__)

LINK_NS: str = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS: str = "{http://www.w3.org/1999/xlink}"
XDS_NS: str = "{http://www.w3.org/2001/XMLSchema}"
XBRLI_NS: str = "{http://www.xbrl.org/2003/instance}"

# dictionary containing all common prefixes and the corresponding namespaces.
NAME_SPACES: dict = {
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrldt": "http://xbrl.org/2005/xbrldt",
}


class Concept:
    """
    Class representing a Concept defined in the schema (xs:element)
    i.e:
    <xs:element id='us-gaap_Assets' name='Assets' nillable='true'
    substitutionGroup='xbrli:item' type='xbrli:monetaryItemType'
    xbrli:balance='debit' xbrli:periodType='instant' />
    """

    def __init__(self, xml_id: str, schema_url: str, name: str) -> None:
        """
        :param xml_id: Id of the concept in the xml
        :param schema_url: url of the schema in which the concept is defined
        :param name: name of the concept
        """
        self.xml_id: str = xml_id
        self.schema_url: str = schema_url
        self.name: str = name
        self.substitution_group: str | None = None
        self.concept_type: str | None = None
        self.abstract: bool | None = None
        self.nillable: bool | None = None
        self.period_type: str | None = None
        self.balance: str | None = None
        self.labels: list[Label] = []

    def to_dict(self):
        """
        Converts the Concept object into a dictionary representation
        """
        return {
            "xml_id": self.xml_id,
            "schema_url": self.schema_url,
            "name": self.name,
            "substitution_group": self.substitution_group,
            "concept_type": self.concept_type,
            "abstract": self.abstract,
            "nillable": self.nillable,
            "period_type": self.period_type,
            "balance": self.balance,
            # Assuming Label class has to_dict()
            "labels": [label.to_dict() for label in self.labels] if self.labels else [],
        }

    def to_json(self):
        """
        Converts the Concept object into a JSON string
        """
        return json.dumps(self.to_dict(), indent=4)

    def __str__(self) -> str:
        return self.name


class ExtendedLinkRole:
    """
    Class representing a ELR.
    A ELR is a set of relations representing a piece of the report (i.e. "1003000 - Statement - Consolidated Balance Sheets")
    ELR's a used to separate Relation linkbases into smaller logical chunks, so it is commonly referenced in the
    calculation, definition and presentation linkbases
    """

    def __init__(self, role_id: str, uri: str, definition: str) -> None:
        """

        :param role_id:
        :param uri:
        :param definition:
        """
        self.xml_id: str = role_id
        self.uri: str = uri
        self.definition: str = definition
        self.definition_link: ExtendedLink | None = None
        self.presentation_link: ExtendedLink | None = None
        self.calculation_link: ExtendedLink | None = None

    def __str__(self) -> str:
        return self.definition


class TaxonomySchema:
    """
    Class represents a Generic Taxonomy Schema. Since this parser is optimized for EDGAR submission's,
    it will only differentiate between the Extending Taxonomy (the taxonomy that comes with the filing) and
    multiple base Taxonomies (i.e dei, us-gaap, exch, naics, sic ...).
    This parser will not parse all Schemas and imports, only what is necessary.
    """

    def __init__(self, schema_url: str, namespace: str):
        """
        The imports array stores an array of all Schemas that are imported.


        :param schema_url:
        :param namespace:
        """
        self.imports: list[TaxonomySchema] = []
        self.link_roles: list[ExtendedLinkRole] = []
        self.lab_linkbases: list[Linkbase] = []
        self.def_linkbases: list[Linkbase] = []
        self.cal_linkbases: list[Linkbase] = []
        self.pre_linkbases: list[Linkbase] = []

        self.schema_url = schema_url
        self.namespace = namespace
        # store the concepts in a dictionary with the concept_id as key
        self.concepts: dict = {}
        # The linkbases reference concepts by their id, the instance file by name.
        # In order to get O(1) in both cases, create a dictionary where the id of a concept can be looked up,
        # based on the name
        self.name_id_map: dict = {}

    def __str__(self) -> str:
        return self.namespace

    def get_taxonomy(self, url: str):
        """
        Returns the taxonomy with the given namespace (if it is the current taxonomy, or if it is imported)
        If the taxonomy cannot be found, the function will return None
        :param url: can either be the namespace or the schema url
        :return: either a TaxonomySchema obj or None
        """
        if compare_uri(self.namespace, url) or compare_uri(self.schema_url, url):
            return self

        for imported_tax in self.imports:
            result = imported_tax.get_taxonomy(url)
            if result is not None:
                return result
        return None

    def get_schema_urls(self) -> list[str]:
        """
        Returns an array of all taxonomy urls that are used by this taxonomy
        Also includes the schema url of this taxonomy
        :return:
        """
        urls: list[str] = [self.schema_url]
        for imported_tax in self.imports:
            urls += imported_tax.get_schema_urls()
        return list(set(urls))


def parse_common_taxonomy(cache: HttpCache, namespace: str) -> TaxonomySchema | None:
    """
    Parses a taxonomy by namespace. This is only possible for certain well known taxonomies, as we need the schema_url for
    parsing it.
    Some xbrl documents from the sec use namespaces without defining a schema url for those namespaces, so this function
    might come in handy
    :param cache:
    :param namespace: namespace of the taxonomy
    :return:
    """

    if namespace in NS_MAP:
        return parse_taxonomy_url(NS_MAP[namespace], cache)
    return None


def load_edgar_taxonomies(cache: HttpCache) -> dict[str, str]:
    """
    This function loads the https://www.sec.gov/files/edgartaxonomies.xml file and returns a namespace to schema url map

    :param cache: http cache instance to use for downloading the file
    :return: A directionary mapping namespace to schema url
    """
    edgar_taxonomies_url = "https://www.sec.gov/files/edgartaxonomies.xml"
    edgar_taxonomies_path = cache.cache_file(edgar_taxonomies_url)
    root: ET.Element = ET.parse(edgar_taxonomies_path).getroot()
    taxonomy_map: dict[str, str] = {}

    for loc in root.findall("Loc"):
        namespace_el = loc.find("Namespace")
        href_el = loc.find("Href")

        if namespace_el is not None and href_el is not None:
            namespace = namespace_el.text.strip()
            href = href_el.text.strip()
            taxonomy_map[namespace] = href
    return taxonomy_map


@lru_cache(maxsize=60)
def parse_taxonomy_url(
    schema_url: str, cache: HttpCache, imported_schema_uris: set = set()
) -> TaxonomySchema:
    """
    Parses a taxonomy schema file from the internet

    :param schema_url: full link to the taxonomy schema
    :param cache: :class:`xbrl.cache.HttpCache` instance
    :param imported_schema_uris: set of already imported schema uris
    :return: parsed :class:`xbrl.taxonomy.TaxonomySchema` object
    """
    if not is_url(schema_url):
        raise XbrlParseException(
            "This function only parses remotely saved taxonomies. Please use parse_taxonomy to parse local taxonomy schemas"
        )
    schema_path: str = cache.cache_file(schema_url)
    return parse_taxonomy(schema_path, cache, imported_schema_uris, schema_url)


def parse_taxonomy(
    schema_path: str,
    cache: HttpCache,
    imported_schema_uris: set = set(),
    schema_url: str | None = None,
) -> TaxonomySchema:
    """
    Parses a taxonomy schema file.

    :param schema_path: url to the schema (on the internet)
    :param cache: :class:`xbrl.cache.HttpCache` instance
    :param imported_schema_uris: set of already imported schema uris
    :param schema_url: if this url is set, the script will try to fetch additionally imported files such as linkbases or
        imported schemas from the remote location. If this url is None, the script will try to find those resources locally.
    :return: parsed :class:`xbrl.taxonomy.TaxonomySchema` object
    """
    schema_path = str(schema_path)
    if is_url(schema_path):
        raise XbrlParseException(
            "This function only parses locally saved taxonomies. Please use parse_taxonomy_url to parse remote taxonomy schemas"
        )
    if not os.path.exists(schema_path):
        raise TaxonomyNotFound(f"Could not find taxonomy schema at {schema_path}")

    # Get the local absolute path to the schema file (and download it if it is not yet cached)
    root: ET.Element = ET.parse(schema_path).getroot()
    # get the target namespace of the taxonomy
    target_ns = root.attrib["targetNamespace"]
    taxonomy: TaxonomySchema = TaxonomySchema(
        schema_url if schema_url else schema_path, target_ns
    )

    import_elements: list[ET.Element] = root.findall("xsd:import", NAME_SPACES)

    for import_element in import_elements:
        import_uri = import_element.attrib["schemaLocation"].strip()

        # Skip empty imports
        if import_uri == "":
            continue

        # Skip already imported URIs
        if import_uri in imported_schema_uris:
            continue

        # sometimes the import schema location is relative. i.e schemaLocation="xbrl-linkbase-2003-12-31.xsd"
        if is_url(import_uri):
            # fetch the schema file from remote
            taxonomy.imports.append(parse_taxonomy_url(import_uri, cache))
        elif schema_url:
            # fetch the schema file from remote by reconstructing the full url
            import_url = resolve_uri(schema_url, import_uri)
            imported_schema_uris.add(import_uri)
            taxonomy.imports.append(parse_taxonomy_url(import_url, cache))
        else:
            # We have to try to fetch the linkbase locally because no full url can be constructed
            import_path = resolve_uri(schema_path, import_uri)
            taxonomy.imports.append(
                parse_taxonomy(import_path, cache, imported_schema_uris)
            )

    role_type_elements: list[ET.Element] = root.findall(
        "xsd:annotation/xsd:appinfo/link:roleType", NAME_SPACES
    )
    # parse ELR's
    for elr in role_type_elements:
        elr_definition = elr.find(LINK_NS + "definition")
        if elr_definition is None or elr_definition.text is None:
            continue
        taxonomy.link_roles.append(
            ExtendedLinkRole(
                elr.attrib["id"], elr.attrib["roleURI"], elr_definition.text.strip()
            )
        )

    # find all elements that are defined in the schema
    for element in root.findall(XDS_NS + "element"):
        # if a concept has no id, it can not be referenced by a linkbase, so just ignore it
        if "id" not in element.attrib or "name" not in element.attrib:
            continue
        el_id: str = element.attrib["id"]
        el_name: str = element.attrib["name"]

        concept = Concept(el_id, schema_url, el_name)
        concept.concept_type = (
            element.attrib["type"] if "type" in element.attrib else None
        )
        concept.nillable = (
            bool(element.attrib["nillable"]) if "nillable" in element.attrib else False
        )
        concept.abstract = (
            bool(element.attrib["abstract"]) if "abstract" in element.attrib else False
        )
        type_attr_name = XBRLI_NS + "periodType"
        concept.period_type = (
            element.attrib[type_attr_name] if type_attr_name in element.attrib else None
        )
        balance_attr_name = XBRLI_NS + "balance"
        concept.balance = (
            element.attrib[balance_attr_name]
            if balance_attr_name in element.attrib
            else None
        )
        # remove the prefix from the substitutionGroup (i.e xbrli:item -> item)
        concept.substitution_group = (
            element.attrib["substitutionGroup"].split(":")[-1]
            if "substitutionGroup" in element.attrib
            else None
        )

        taxonomy.concepts[concept.xml_id] = concept
        taxonomy.name_id_map[concept.name] = concept.xml_id

    linkbase_ref_elements: list[ET.Element] = root.findall(
        "xsd:annotation/xsd:appinfo/link:linkbaseRef", NAME_SPACES
    )
    for linkbase_ref in linkbase_ref_elements:
        linkbase_uri = linkbase_ref.attrib[XLINK_NS + "href"]
        role = (
            linkbase_ref.attrib[XLINK_NS + "role"]
            if XLINK_NS + "role" in linkbase_ref.attrib
            else None
        )
        linkbase_type = (
            LinkbaseType.get_type_from_role(role)
            if role is not None
            else LinkbaseType.guess_linkbase_role(linkbase_uri)
        )

        # check if the linkbase url is relative
        if is_url(linkbase_uri):
            # fetch the linkbase from remote
            linkbase: Linkbase = parse_linkbase_url(linkbase_uri, linkbase_type, cache)
        elif schema_url:
            # fetch the linkbase from remote by reconstructing the full URL
            linkbase_url = resolve_uri(schema_url, linkbase_uri)
            linkbase: Linkbase = parse_linkbase_url(linkbase_url, linkbase_type, cache)
        else:
            # We have to try to fetch the linkbase locally because no full url can be constructed
            linkbase_path = resolve_uri(schema_path, linkbase_uri)
            linkbase: Linkbase = parse_linkbase(linkbase_path, linkbase_type)

        # add the linkbase to the taxonomy
        if linkbase_type == LinkbaseType.DEFINITION:
            taxonomy.def_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.CALCULATION:
            taxonomy.cal_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.PRESENTATION:
            taxonomy.pre_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.LABEL:
            taxonomy.lab_linkbases.append(linkbase)

    # loop over the ELR's of the schema and assign the extended links from the linkbases
    for elr in taxonomy.link_roles:
        for extended_def_links in [
            def_linkbase.extended_links for def_linkbase in taxonomy.def_linkbases
        ]:
            for extended_def_link in extended_def_links:
                if extended_def_link.elr_id.split("#")[1] == elr.xml_id:
                    elr.definition_link = extended_def_link
                    break
        for extended_pre_links in [
            pre_linkbase.extended_links for pre_linkbase in taxonomy.pre_linkbases
        ]:
            for extended_pre_link in extended_pre_links:
                if extended_pre_link.elr_id.split("#")[1] == elr.xml_id:
                    elr.presentation_link = extended_pre_link
                    break
        for extended_cal_links in [
            cal_linkbase.extended_links for cal_linkbase in taxonomy.cal_linkbases
        ]:
            for extended_cal_link in extended_cal_links:
                if extended_cal_link.elr_id.split("#")[1] == elr.xml_id:
                    elr.calculation_link = extended_cal_link
                    break

    for label_linkbase in taxonomy.lab_linkbases:
        for extended_link in label_linkbase.extended_links:
            for root_locator in extended_link.root_locators:
                # find the taxonomy the locator is referring to
                schema_url, concept_id = unquote(root_locator.href).split("#")
                c_taxonomy: TaxonomySchema = taxonomy.get_taxonomy(schema_url)
                if c_taxonomy is None:
                    if schema_url in NS_MAP.values():
                        c_taxonomy = parse_taxonomy_url(schema_url, cache)
                        taxonomy.imports.append(c_taxonomy)
                    else:
                        continue
                concept: Concept = c_taxonomy.concepts[concept_id]
                concept.labels = []
                for label_arc in root_locator.children:
                    for label in label_arc.labels:
                        concept.labels.append(label)

    return taxonomy
