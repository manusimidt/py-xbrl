"""
This module contains all classes and functions necessary for parsing Taxonomy schema files.
"""

import json
import logging
import os
import xml.etree.ElementTree as ET
from collections import OrderedDict
from urllib.parse import unquote, urldefrag, urljoin, urlparse

from xbrl import TaxonomyNotFound
from xbrl.cache import HttpCache
from xbrl.helper.uri_helper import compare_uri, is_url, resolve_uri
from xbrl.linkbase import ExtendedLink, Label, LabelArc, Linkbase, LinkbaseType, parse_linkbase, parse_linkbase_url
from xbrl.ns_map import NS_MAP

logger = logging.getLogger(__name__)

LINK_NS: str = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS: str = "{http://www.w3.org/1999/xlink}"
XDS_NS: str = "{http://www.w3.org/2001/XMLSchema}"
XBRLI_NS: str = "{http://www.xbrl.org/2003/instance}"

# dictionary containing all common prefixes and the corresponding namespaces.
NAME_SPACES: dict[str, str] = {
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
        self.namespace: str | None = None
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
        self.concepts: dict[str, Concept] = {}
        # The linkbases reference concepts by their id, the instance file by name.
        # In order to get O(1) in both cases, create a dictionary where the id of a concept can be looked up,
        # based on the name
        self.name_id_map: dict[str, str] = {}

    def __str__(self) -> str:
        return self.namespace

    def get_taxonomy(self, url: str, visited: None | set[str] = None):
        """
        Returns the taxonomy with the given namespace (if it is the current taxonomy, or if it is imported)
        If the taxonomy cannot be found, the function will return None
        :param url: can either be the namespace or the schema url
        :param visited: set of already visited schema urls to prevent infinite recursion
        :return: either a TaxonomySchema obj or None
        """
        if visited is None:
            visited = set()

        # Prevent infinite recursion from circular imports
        if self.schema_url in visited:
            return None
        visited.add(self.schema_url)

        if compare_uri(self.namespace, url) or compare_uri(self.schema_url, url):
            return self

        for imported_tax in self.imports:
            result = imported_tax.get_taxonomy(url, visited)
            if result is not None:
                return result
        return None

    def get_schema_urls(self, visited: None | set[str] = None) -> list[str]:
        """
        Returns an array of all taxonomy urls that are used by this taxonomy
        Also includes the schema url of this taxonomy
        :return:
        """
        if visited is None:
            visited = set()
        # IF the taxonomy imports have already been added to the list, do not add them again
        if self.schema_url in visited:
            return []
        visited.add(self.schema_url)

        urls: list[str] = [self.schema_url]
        for imported_tax in self.imports:
            urls += imported_tax.get_schema_urls(visited)
        return list(set(urls))


class TaxonomyParser:
    """
    Helper class to parse taxonomies and cache namespace maps
    """

    """
    :param use_local_ns_map: if enabled the parser will use a local namespace map as fallback to try resolving taxonomies
    :param fetch_edgar_taxonomies: if enabled, the parser will upfront load the EDGAR Common Taxonomies from
        https://www.sec.gov/files/edgartaxonomies.xml and use them as fallback
    :param resolve_referenced_schemas: if enabled, namespace lookup may fetch schema URLs referenced by already parsed
        schemas and linkbases. Only trusted schema hosts are eligible, and targetNamespace must match.
    """

    def __init__(
        self,
        cache: HttpCache,
        use_local_ns_map: bool = True,
        fetch_edgar_taxonomies: bool = False,
        fetch_py_xbrl_ns_map: bool = True,
        max_taxonomy_cache_size: int = 60,
        resolve_referenced_schemas: bool = False,
    ) -> None:
        self.cache = cache
        self.use_local_ns_map = use_local_ns_map
        self.fetch_edgar_taxonomies = fetch_edgar_taxonomies
        self.fetch_py_xbrl_ns_map = fetch_py_xbrl_ns_map
        self.max_taxonomy_cache_size = max_taxonomy_cache_size
        self.resolve_referenced_schemas = resolve_referenced_schemas

        # Cache for global namespace to schema url mapping of common taxonomies
        self.global_ns_map: dict[str, str] = {}
        # Cache for parsed taxonomies with LRU eviction, the key is the schema url
        self.taxonomy_cache: OrderedDict[str, TaxonomySchema] = OrderedDict()
        # Trusted schema hosts and namespace-host relationships are derived from NS_MAP.
        # They constrain both disk-cache scanning and opt-in network resolution.
        self.trusted_hosts, self._namespace_schema_hosts = self._build_trusted_host_maps()
        # Lazy per-schema-host cache index: host -> {normalized_namespace -> local_schema_path}.
        self._cache_host_ns_index: dict[str, dict[str, str]] = {}
        # Ordered, bounded schema candidates collected from parsed documents.
        self._referenced_schema_urls: list[str] = []
        self._referenced_schema_url_set: set[str] = set()
        self._max_referenced_schema_urls = 500

        if self.use_local_ns_map:
            self._add_local_ns_map()
        if self.fetch_edgar_taxonomies:
            self._add_edgar_taxonomies()

    def _add_local_ns_map(self):
        """
        Adds the local NS_MAP to the global namespace map
        """
        for ns, url in NS_MAP.items():
            self.global_ns_map[self._normalize_namespace(ns)] = url

    def _add_edgar_taxonomies(self):
        """
        Adds the Edgar taxonomy namespace map to the global namespace map
        """
        edgar_taxonomies_url = "https://www.sec.gov/files/edgartaxonomies.xml"
        edgar_taxonomies_path = self.cache.cache_file(edgar_taxonomies_url)
        root: ET.Element = ET.parse(edgar_taxonomies_path).getroot()

        for loc in root.findall("Loc"):
            namespace_el = loc.find("Namespace")
            href_el = loc.find("Href")

            if namespace_el is not None and href_el is not None:
                namespace_text = namespace_el.text
                href_text = href_el.text
                if namespace_text is None or href_text is None:
                    continue
                namespace = self._normalize_namespace(namespace_text)
                href = href_text.strip()
                self.global_ns_map[namespace] = href

    def _add_to_cache(self, schema_path: str, taxonomy: TaxonomySchema):
        self.taxonomy_cache[schema_path] = taxonomy
        self.taxonomy_cache.move_to_end(schema_path)

        # Remove oldest entry if cache exceeds max size
        if len(self.taxonomy_cache) > self.max_taxonomy_cache_size:
            self.taxonomy_cache.popitem(last=False)

    def _is_in_cache(self, schema_path: str) -> bool:
        return schema_path in self.taxonomy_cache

    def _load_from_cache(self, schema_path: str) -> TaxonomySchema | None:
        if self._is_in_cache(schema_path):
            # Move to end (mark as recently used)
            self.taxonomy_cache.move_to_end(schema_path)
            return self.taxonomy_cache[schema_path]
        return None

    @staticmethod
    def _normalize_namespace(namespace: str) -> str:
        """Normalize insignificant whitespace and one or more trailing slashes."""
        return str(namespace).strip().rstrip("/")

    @staticmethod
    def _uri_host(uri: str) -> str:
        parsed = urlparse(str(uri).strip())
        if parsed.scheme.lower() not in ("http", "https"):
            return ""
        return (parsed.hostname or "").lower().strip()

    def _build_trusted_host_maps(self) -> tuple[set[str], dict[str, set[str]]]:
        """Derive trusted schema hosts and namespace-host to schema-host relationships."""
        trusted_schema_hosts: set[str] = set()
        namespace_schema_hosts: dict[str, set[str]] = {}
        for namespace, schema_url in NS_MAP.items():
            namespace_host = self._uri_host(namespace)
            schema_host = self._uri_host(schema_url)
            if not schema_host:
                continue
            trusted_schema_hosts.add(schema_host)
            if namespace_host:
                namespace_schema_hosts.setdefault(namespace_host, set()).add(schema_host)
        return trusted_schema_hosts, namespace_schema_hosts

    def _build_namespace_index_for_host(self, host: str) -> dict[str, str]:
        """Build a targetNamespace index from cached XSD files under one trusted schema host."""
        host_lc = host.lower().strip()
        if host_lc in self._cache_host_ns_index:
            return self._cache_host_ns_index[host_lc]

        host_index: dict[str, str] = {}
        host_root = os.path.join(self.cache.cache_dir, host_lc)
        if os.path.isdir(host_root):
            for dirpath, dirnames, filenames in os.walk(host_root):
                dirnames.sort()
                for filename in sorted(filenames):
                    if not filename.lower().endswith(".xsd"):
                        continue
                    schema_path = os.path.join(dirpath, filename)
                    try:
                        target_ns = ET.parse(schema_path).getroot().attrib.get("targetNamespace")
                    except (OSError, ET.ParseError):
                        continue
                    normalized_ns = self._normalize_namespace(target_ns or "")
                    if normalized_ns and normalized_ns not in host_index:
                        host_index[normalized_ns] = schema_path

        self._cache_host_ns_index[host_lc] = host_index
        return host_index

    def _find_cached_schema_path_for_namespace(self, namespace: str) -> str | None:
        """Locate a cached XSD by namespace without scanning untrusted cache directories."""
        wanted_ns = self._normalize_namespace(namespace)
        namespace_host = self._uri_host(wanted_ns)
        if not namespace_host:
            return None

        schema_hosts = self._namespace_schema_hosts.get(namespace_host, set())
        if namespace_host in self.trusted_hosts:
            schema_hosts = schema_hosts | {namespace_host}
        for schema_host in sorted(schema_hosts):
            cached_path = self._build_namespace_index_for_host(schema_host).get(wanted_ns)
            if cached_path is not None:
                return cached_path
        return None

    def _try_taxonomy_from_local_cache(self, namespace: str) -> TaxonomySchema | None:
        """Resolve a namespace from parsed taxonomies or the trusted on-disk HTTP cache."""
        wanted_ns = self._normalize_namespace(namespace)
        for cached_taxonomy in reversed(list(self.taxonomy_cache.values())):
            if self._normalize_namespace(cached_taxonomy.namespace) == wanted_ns:
                return cached_taxonomy

        cached_schema_path = self._find_cached_schema_path_for_namespace(wanted_ns)
        if cached_schema_path is None:
            return None
        try:
            cached_taxonomy = self.parse_taxonomy(cached_schema_path)
        except Exception as exc:
            logger.debug(
                "Failed loading cached taxonomy for namespace %s from %s: %s", wanted_ns, cached_schema_path, exc
            )
            return None
        if self._normalize_namespace(cached_taxonomy.namespace) != wanted_ns:
            return None

        self.global_ns_map[wanted_ns] = cached_schema_path
        logger.info("Resolved taxonomy namespace %s from trusted local cache %s", wanted_ns, cached_schema_path)
        return cached_taxonomy

    def _register_referenced_schema_url(self, base_uri: str, href: str) -> None:
        if not self.resolve_referenced_schemas or len(self._referenced_schema_urls) >= self._max_referenced_schema_urls:
            return
        candidate, _fragment = urldefrag(urljoin(base_uri, str(href).strip()))
        if not candidate.lower().endswith(".xsd"):
            return
        if self._uri_host(candidate) not in self.trusted_hosts:
            return
        if candidate in self._referenced_schema_url_set:
            return
        self._referenced_schema_url_set.add(candidate)
        self._referenced_schema_urls.append(candidate)

    def _register_schema_references(self, root: ET.Element, base_uri: str) -> None:
        """Collect trusted XSD URLs from xlink references in a parsed XML document."""
        if not self.resolve_referenced_schemas:
            return
        for element in root.iter():
            href = element.attrib.get(XLINK_NS + "href")
            if href:
                self._register_referenced_schema_url(base_uri, href)

    def _register_linkbase_schema_references(self, linkbase: Linkbase) -> None:
        if not self.resolve_referenced_schemas or not linkbase.linkbase_uri:
            return
        source_uri = linkbase.linkbase_uri
        linkbase_path = self.cache.url_to_path(source_uri) if is_url(source_uri) else source_uri
        try:
            linkbase_root = ET.parse(linkbase_path).getroot()
        except (OSError, ET.ParseError) as exc:
            logger.debug("Could not inspect parsed linkbase %s for schema references: %s", source_uri, exc)
            return
        self._register_schema_references(linkbase_root, source_uri)

    def _try_taxonomy_from_referenced_schemas(self, namespace: str) -> TaxonomySchema | None:
        """Fetch trusted referenced schemas until one declares the requested targetNamespace."""
        if not self.resolve_referenced_schemas:
            return None
        wanted_ns = self._normalize_namespace(namespace)
        for schema_url in tuple(self._referenced_schema_urls):
            try:
                schema_path = self.cache.cache_file(schema_url)
                candidate_ns = ET.parse(schema_path).getroot().attrib.get("targetNamespace", "")
            except Exception as exc:
                logger.debug("Referenced schema candidate %s could not be inspected: %s", schema_url, exc)
                continue
            if self._normalize_namespace(candidate_ns) != wanted_ns:
                continue
            try:
                taxonomy = self.parse_taxonomy(schema_path, schema_url=schema_url)
            except Exception as exc:
                logger.debug("Referenced schema candidate %s could not be parsed: %s", schema_url, exc)
                continue
            if self._normalize_namespace(taxonomy.namespace) != wanted_ns:
                continue
            self.global_ns_map[wanted_ns] = schema_url
            logger.info("Resolved taxonomy namespace %s from trusted referenced schema %s", wanted_ns, schema_url)
            return taxonomy
        return None

    def try_taxonomy_from_namespace(self, namespace: str) -> TaxonomySchema:
        """
        Resolve a taxonomy by namespace from the static/global map, local caches, or opted-in trusted references.

        :param namespace: Namespace of the taxonomy
        :return: Parsed TaxonomySchema object or None if not found
        """
        wanted_ns = self._normalize_namespace(namespace)
        if wanted_ns in self.global_ns_map:
            schema_url = self.global_ns_map[wanted_ns]
            return self.parse_taxonomy(schema_url)

        cached_taxonomy = self._try_taxonomy_from_local_cache(wanted_ns)
        if cached_taxonomy is not None:
            return cached_taxonomy

        referenced_taxonomy = self._try_taxonomy_from_referenced_schemas(wanted_ns)
        if referenced_taxonomy is not None:
            return referenced_taxonomy
        raise TaxonomyNotFound(wanted_ns)

    def parse_taxonomy(
        self, schema_path: str, imported_schema_uris: set[str] = set(), schema_url: str | None = None
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
        schema_path = str(schema_path).strip()
        if is_url(schema_path):
            # If the path is acually a url, we set the schema_url to it and download the file first
            schema_url = schema_path
            schema_path = self.cache.cache_file(schema_path)

        if not os.path.exists(schema_path):
            raise TaxonomyNotFound(f"Could not find taxonomy schema at {schema_path}")

        cached = self._load_from_cache(schema_path)
        if cached is not None:
            return cached

        # Get the local absolute path to the schema file (and download it if it is not yet cached)
        root: ET.Element = ET.parse(schema_path).getroot()
        self._register_schema_references(root, schema_url if schema_url else schema_path)
        # get the target namespace of the taxonomy
        target_ns = root.attrib["targetNamespace"]
        taxonomy: TaxonomySchema = TaxonomySchema(schema_url if schema_url else schema_path, target_ns)

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
                taxonomy.imports.append(self.parse_taxonomy(import_uri))
            elif schema_url:
                # fetch the schema file from remote by reconstructing the full url
                import_url = resolve_uri(schema_url, import_uri)
                imported_schema_uris.add(import_uri)
                taxonomy.imports.append(self.parse_taxonomy(import_url))
            else:
                # We have to try to fetch the linkbase locally because no full url can be constructed
                import_path = resolve_uri(schema_path, import_uri)
                taxonomy.imports.append(self.parse_taxonomy(import_path, imported_schema_uris))

        role_type_elements: list[ET.Element] = root.findall("xsd:annotation/xsd:appinfo/link:roleType", NAME_SPACES)
        # parse ELR's
        for elr_elem in role_type_elements:
            elr_definition = elr_elem.find(LINK_NS + "definition")
            if elr_definition is None or elr_definition.text is None:
                continue
            taxonomy.link_roles.append(
                ExtendedLinkRole(elr_elem.attrib["id"], elr_elem.attrib["roleURI"], elr_definition.text.strip())
            )

        # find all elements that are defined in the schema
        for element in root.findall(XDS_NS + "element"):
            # if a concept has no id, it can not be referenced by a linkbase, so just ignore it
            if "id" not in element.attrib or "name" not in element.attrib:
                continue
            el_id: str = element.attrib["id"]
            el_name: str = element.attrib["name"]

            new_concept = Concept(el_id, schema_url or schema_path, el_name)
            new_concept.concept_type = element.attrib["type"] if "type" in element.attrib else None
            new_concept.nillable = bool(element.attrib["nillable"]) if "nillable" in element.attrib else False
            new_concept.abstract = bool(element.attrib["abstract"]) if "abstract" in element.attrib else False
            type_attr_name = XBRLI_NS + "periodType"
            new_concept.period_type = element.attrib[type_attr_name] if type_attr_name in element.attrib else None
            balance_attr_name = XBRLI_NS + "balance"
            new_concept.balance = element.attrib[balance_attr_name] if balance_attr_name in element.attrib else None
            # remove the prefix from the substitutionGroup (i.e xbrli:item -> item)
            new_concept.substitution_group = (
                element.attrib["substitutionGroup"].split(":")[-1] if "substitutionGroup" in element.attrib else None
            )

            taxonomy.concepts[new_concept.xml_id] = new_concept
            taxonomy.name_id_map[new_concept.name] = new_concept.xml_id

        linkbase_ref_elements: list[ET.Element] = root.findall(
            "xsd:annotation/xsd:appinfo/link:linkbaseRef", NAME_SPACES
        )
        for linkbase_ref in linkbase_ref_elements:
            linkbase_uri = linkbase_ref.attrib[XLINK_NS + "href"]
            role = linkbase_ref.attrib[XLINK_NS + "role"] if XLINK_NS + "role" in linkbase_ref.attrib else None
            linkbase_type = (
                LinkbaseType.get_type_from_role(role)
                if role is not None
                else LinkbaseType.guess_linkbase_role(linkbase_uri)
            )
            if linkbase_type is None:
                logger.info(f"Ignoring unsupported linkbase: {role}")
                continue

            # check if the linkbase url is relative
            linkbase: Linkbase
            if is_url(linkbase_uri):
                # fetch the linkbase from remote
                linkbase = parse_linkbase_url(linkbase_uri, linkbase_type, self.cache)
            elif schema_url:
                # fetch the linkbase from remote by reconstructing the full URL
                linkbase_url = resolve_uri(schema_url, linkbase_uri)
                linkbase = parse_linkbase_url(linkbase_url, linkbase_type, self.cache)
            else:
                # We have to try to fetch the linkbase locally because no full url can be constructed
                linkbase_path = resolve_uri(schema_path, linkbase_uri)
                linkbase = parse_linkbase(linkbase_path, linkbase_type)

            self._register_linkbase_schema_references(linkbase)

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
        all_def_links = [def_linkbase.extended_links for def_linkbase in taxonomy.def_linkbases]
        all_pre_links = [pre_linkbase.extended_links for pre_linkbase in taxonomy.pre_linkbases]
        all_cal_links = [cal_linkbase.extended_links for cal_linkbase in taxonomy.cal_linkbases]
        for elr in taxonomy.link_roles:
            for extended_def_links in all_def_links:
                for extended_def_link in extended_def_links:
                    if extended_def_link.elr_id is None:
                        continue
                    if extended_def_link.elr_id.split("#")[1] == elr.xml_id:
                        elr.definition_link = extended_def_link
                        break
            for extended_pre_links in all_pre_links:
                for extended_pre_link in extended_pre_links:
                    if extended_pre_link.elr_id is None:
                        continue
                    if extended_pre_link.elr_id.split("#")[1] == elr.xml_id:
                        elr.presentation_link = extended_pre_link
                        break
            for extended_cal_links in all_cal_links:
                for extended_cal_link in extended_cal_links:
                    if extended_cal_link.elr_id is None:
                        continue
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
                            c_taxonomy = self.parse_taxonomy(schema_url)
                            taxonomy.imports.append(c_taxonomy)
                        else:
                            continue
                    concept: Concept = c_taxonomy.concepts[concept_id]
                    concept.labels = []
                    for label_arc in root_locator.children:
                        if isinstance(label_arc, LabelArc):
                            for label in label_arc.labels:
                                concept.labels.append(label)

        self._add_to_cache(schema_path, taxonomy)
        return taxonomy
