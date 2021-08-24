"""
This module contains all classes and functions necessary for parsing Taxonomy schema files.

A Taxonomy schema defines the reportable concepts and links the linkbases to
describe the relationships between the concepts.
Taxonomy schemas can import multiple different taxonomy schemas.

"""
import logging
import os
from typing import List
import xml.etree.ElementTree as ET
from functools import lru_cache
from urllib.parse import unquote

from xbrl import XbrlParseException, TaxonomyNotFound
from xbrl.cache import HttpCache
from xbrl.helper.uri_helper import resolve_uri, compare_uri
from xbrl.linkbase import Linkbase, ExtendedLink, LinkbaseType, parse_linkbase, parse_linkbase_url, Label

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
    "xbrldt": "http://xbrl.org/2005/xbrldt"
}

ns_schema_map: dict = {
    "http://fasb.org/srt/2018-01-31": "http://xbrl.fasb.org/srt/2018/elts/srt-2018-01-31.xsd",
    "http://fasb.org/srt/2019-01-31": "http://xbrl.fasb.org/srt/2019/elts/srt-2019-01-31.xsd",
    "http://fasb.org/srt/2020-01-31": "http://xbrl.fasb.org/srt/2020/elts/srt-2020-01-31.xsd",

    "http://xbrl.sec.gov/stpr/2018-01-31": "https://xbrl.sec.gov/stpr/2018/stpr-2018-01-31.xsd",
    # Replace draft taxonomy with official STPR 2021 one once it is released
    "http://xbrl.sec.gov/stpr/2021": "https://xbrl.sec.gov/stpr/2021/stpr-2021.xsd",

    "http://xbrl.sec.gov/country/2017-01-31": "https://xbrl.sec.gov/country/2017/country-2017-01-31.xsd",
    "http://xbrl.sec.gov/country/2020-01-31": "https://xbrl.sec.gov/country/2020/country-2020-01-31.xsd",

    "http://xbrl.us/invest/2009-01-31": "https://taxonomies.xbrl.us/us-gaap/2009/non-gaap/invest-2009-01-31.xsd",
    "http://xbrl.sec.gov/invest/2011-01-31": "https://xbrl.sec.gov/invest/2011/invest-2011-01-31.xsd",
    "http://xbrl.sec.gov/invest/2012-01-31": "https://xbrl.sec.gov/invest/2012/invest-2012-01-31.xsd",
    "http://xbrl.sec.gov/invest/2013-01-31": "https://xbrl.sec.gov/invest/2013/invest-2013-01-31.xsd",

    "http://xbrl.sec.gov/dei/2011-01-31": "https://xbrl.sec.gov/dei/2011/dei-2011-01-31.xsd",
    "http://xbrl.sec.gov/dei/2012-01-31": "https://xbrl.sec.gov/dei/2012/dei-2012-01-31.xsd",
    "http://xbrl.sec.gov/dei/2013-01-31": "https://xbrl.sec.gov/dei/2013/dei-2013-01-31.xsd",
    "http://xbrl.sec.gov/dei/2014-01-31": "https://xbrl.sec.gov/dei/2014/dei-2014-01-31.xsd",
    "http://xbrl.sec.gov/dei/2018-01-31": "https://xbrl.sec.gov/dei/2018/dei-2018-01-31.xsd",
    "http://xbrl.sec.gov/dei/2019-01-31": "https://xbrl.sec.gov/dei/2019/dei-2019-01-31.xsd",
    "http://xbrl.sec.gov/dei/2020-01-31": "https://xbrl.sec.gov/dei/2020/dei-2020-01-31.xsd",
    "http://xbrl.sec.gov/dei/2021": "https://xbrl.sec.gov/dei/2021/dei-2021.xsd",

    "http://fasb.org/us-gaap/2011-01-31": "http://xbrl.fasb.org/us-gaap/2011/elts/us-gaap-2011-01-31.xsd",
    "http://fasb.org/us-gaap/2012-01-31": "http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-2012-01-31.xsd",
    "http://fasb.org/us-gaap/2013-01-31": "http://xbrl.fasb.org/us-gaap/2013/elts/us-gaap-2013-01-31.xsd",
    "http://fasb.org/us-gaap/2014-01-31": "http://xbrl.fasb.org/us-gaap/2014/elts/us-gaap-2014-01-31.xsd",
    "http://fasb.org/us-gaap/2015-01-31": "http://xbrl.fasb.org/us-gaap/2015/elts/us-gaap-2015-01-31.xsd",
    "http://fasb.org/us-gaap/2016-01-31": "http://xbrl.fasb.org/us-gaap/2016/elts/us-gaap-2016-01-31.xsd",
    "http://fasb.org/us-gaap/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/elts/us-gaap-2017-01-31.xsd",
    "http://fasb.org/us-gaap/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/elts/us-gaap-2018-01-31.xsd",
    "http://fasb.org/us-gaap/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/elts/us-gaap-2019-01-31.xsd",
    "http://fasb.org/us-gaap/2020-01-31": "http://xbrl.fasb.org/us-gaap/2020/elts/us-gaap-2020-01-31.xsd",
    "http://fasb.org/us-gaap/2021-01-31": "http://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-2021-01-31.xsd"
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
        self.substitution_group: str or None = None
        self.concept_type: str or None = None
        self.abstract: bool or None = None
        self.nillable: bool or None = None
        self.period_type: str or None = None
        self.balance: str or None = None
        self.labels: [Label] = []

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
        self.definition_link: ExtendedLink or None = None
        self.presentation_link: ExtendedLink or None = None
        self.calculation_link: ExtendedLink or None = None

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
        The current Taxonomy Schema can override the extended schemas in the following way:
        1. Addition of new concepts:
            New concepts are added in this TaxonomySchema to extend the concepts declared in the base Taxonomy schemas
        2. Addition of resources:
            The Label Linkbase of this taxonomy can add new labels to existing concepts from the base taxonomy
        3. Overriding of relationships:
            All Linkbases of this taxonomy can override i.e the order of concepts in a definition linkbase
        4. Overriding of resources:
            The Label Linkbase of this taxonomy can override the labels of the base taxonomy!
        """
        self.imports: List[TaxonomySchema] = []
        self.link_roles: List[ExtendedLinkRole] = []
        self.lab_linkbases: List[Linkbase] = []
        self.def_linkbases: List[Linkbase] = []
        self.cal_linkbases: List[Linkbase] = []
        self.pre_linkbases: List[Linkbase] = []

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
        :return either a TaxonomySchema obj or None
        :return:
        """
        if compare_uri(self.namespace, url) or compare_uri(self.schema_url, url):
            return self

        for imported_tax in self.imports:
            result = imported_tax.get_taxonomy(url)
            if result is not None:
                return result
        return None


def parse_common_taxonomy(cache: HttpCache, namespace: str) -> TaxonomySchema or None:
    """
    Parses a taxonomy by namespace. This is only possible for certain well known taxonomies, as we need the schema_url for
    parsing it.
    Some xbrl documents from the sec use namespaces without defining a schema url for those namespaces, so this function
    might come in handy
    :param cache:
    :param namespace: namespace of the taxonomy
    :return:
    """

    if namespace in ns_schema_map:
        return parse_taxonomy_url(ns_schema_map[namespace], cache)
    return None


@lru_cache(maxsize=60)
def parse_taxonomy_url(schema_url: str, cache: HttpCache) -> TaxonomySchema:
    """
    Parses a taxonomy schema file from the internet
    :param schema_url:
    :param cache:
    :return:
    """
    if not schema_url.startswith('http'): raise XbrlParseException(
        'This function only parses remotely saved taxonomies. Please use parse_taxonomy to parse local taxonomy schemas')

    schema_path: str = cache.cache_file(schema_url)
    return parse_taxonomy(schema_path, cache, schema_url)


def parse_taxonomy(schema_path: str, cache: HttpCache, schema_url: str or None = None) -> TaxonomySchema:
    """
    Parses a taxonomy schema file.
    :param schema_path: url to the schema (on the internet)
    :param cache: HttpCache instance
    :param schema_url: if this url is set, the script will try to fetch additionally imported files such as linkbases or
    imported schemas from the remote location. If this url is None, the script will try to find those resources locally.
    :return:
    """
    if schema_path.startswith('http'): raise XbrlParseException(
        'This function only parses locally saved taxonomies. Please use parse_taxonomy_url to parse remote taxonomy schemas')
    if not os.path.exists(schema_path):
        raise TaxonomyNotFound(f"Could not find taxonomy schema at {schema_path}")

    # Get the local absolute path to the schema file (and download it if it is not yet cached)
    root: ET.Element = ET.parse(schema_path).getroot()
    # get the target namespace of the taxonomy
    target_ns = root.attrib['targetNamespace']
    taxonomy: TaxonomySchema = TaxonomySchema(schema_url if schema_url else schema_path, target_ns)

    import_elements: List[ET.Element] = root.findall('xsd:import', NAME_SPACES)

    for import_element in import_elements:
        import_uri = import_element.attrib['schemaLocation']

        # sometimes the import schema location is relative. i.e schemaLocation="xbrl-linkbase-2003-12-31.xsd"
        if import_uri.startswith('http'):
            # fetch the schema file from remote
            taxonomy.imports.append(parse_taxonomy_url(import_uri, cache))
        elif schema_url:
            # fetch the schema file from remote by reconstructing the full url
            import_url = resolve_uri(schema_url, import_uri)
            taxonomy.imports.append(parse_taxonomy_url(import_url, cache))
        else:
            # We have to try to fetch the linkbase locally because no full url can be constructed
            import_path = resolve_uri(schema_path, import_uri)
            taxonomy.imports.append(parse_taxonomy(import_path, cache))

    role_type_elements: List[ET.Element] = root.findall('xsd:annotation/xsd:appinfo/link:roleType', NAME_SPACES)
    # parse ELR's
    for elr in role_type_elements:
        elr_definition = elr.find(LINK_NS + 'definition')
        if elr_definition is None or elr_definition.text is None: continue
        taxonomy.link_roles.append(
            ExtendedLinkRole(elr.attrib['id'], elr.attrib['roleURI'], elr_definition.text.strip()))

    # find all elements that are defined in the schema
    for element in root.findall(XDS_NS + 'element'):
        # if a concept has no id, it can not be referenced by a linkbase, so just ignore it
        if 'id' not in element.attrib or 'name' not in element.attrib:
            continue
        el_id: str = element.attrib['id']
        el_name: str = element.attrib['name']

        concept = Concept(el_id, schema_url, el_name)
        concept.type = element.attrib['type'] if 'type' in element.attrib else False
        concept.nillable = bool(element.attrib['nillable']) if 'nillable' in element.attrib else False
        concept.abstract = bool(element.attrib['abstract']) if 'abstract' in element.attrib else False
        type_attr_name = XBRLI_NS + 'periodType'
        concept.period_type = element.attrib[type_attr_name] if type_attr_name in element.attrib else None
        balance_attr_name = XBRLI_NS + 'balance'
        concept.balance = element.attrib[balance_attr_name] if balance_attr_name in element.attrib else None
        # remove the prefix from the substitutionGroup (i.e xbrli:item -> item)
        concept.substitution_group = \
            element.attrib['substitutionGroup'].split(':')[-1] if 'substitutionGroup' in element.attrib else None

        taxonomy.concepts[concept.xml_id] = concept
        taxonomy.name_id_map[concept.name] = concept.xml_id

    linkbase_ref_elements: List[ET.Element] = root.findall('xsd:annotation/xsd:appinfo/link:linkbaseRef', NAME_SPACES)
    for linkbase_ref in linkbase_ref_elements:
        linkbase_uri = linkbase_ref.attrib[XLINK_NS + 'href']
        role = linkbase_ref.attrib[XLINK_NS + 'role'] if XLINK_NS + 'role' in linkbase_ref.attrib else None
        linkbase_type = LinkbaseType.get_type_from_role(role) if role is not None else LinkbaseType.guess_linkbase_role(
            linkbase_uri)

        # check if the linkbase url is relative
        if linkbase_uri.startswith('http'):
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
        for extended_def_links in [def_linkbase.extended_links for def_linkbase in taxonomy.def_linkbases]:
            for extended_def_link in extended_def_links:
                if extended_def_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.definition_link = extended_def_link
                    break
        for extended_pre_links in [pre_linkbase.extended_links for pre_linkbase in taxonomy.pre_linkbases]:
            for extended_pre_link in extended_pre_links:
                if extended_pre_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.presentation_link = extended_pre_link
                    break
        for extended_cal_links in [cal_linkbase.extended_links for cal_linkbase in taxonomy.cal_linkbases]:
            for extended_cal_link in extended_cal_links:
                if extended_cal_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.calculation_link = extended_cal_link
                    break

    for label_linkbase in taxonomy.lab_linkbases:
        for extended_link in label_linkbase.extended_links:
            for root_locator in extended_link.root_locators:
                # find the taxonomy the locator is referring to
                schema_url, concept_id = unquote(root_locator.href).split('#')
                c_taxonomy: TaxonomySchema = taxonomy.get_taxonomy(schema_url)
                if c_taxonomy is None:
                    if schema_url in ns_schema_map.values():
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
