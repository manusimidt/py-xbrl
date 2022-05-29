"""
This module contains all classes and functions necessary for parsing a Instance file.

This module will also access other Modules i.e TaxonomySchema.py to parse the Instance file
as well as the taxonomies and linkbases used by the instance files
"""
import re
import abc
import logging
from io import StringIO, BytesIO, IOBase
from typing import List
import xml.etree.ElementTree as ET
from datetime import date, datetime

from xbrl import TaxonomyNotFound, InstanceParseException
from xbrl.cache import HttpCache
from xbrl.taxonomy import Concept, TaxonomySchema, parse_taxonomy, parse_common_taxonomy, parse_taxonomy_url
from xbrl.helper.uri_helper import resolve_uri
from xbrl.helper.xml_parser import parse_file
from xbrl.transformations import normalize, TransformationException, TransformationNotImplemented

logger = logging.getLogger(__name__)
LINK_NS: str = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS: str = "{http://www.w3.org/1999/xlink}"
XDS_NS: str = "{http://www.w3.org/2001/XMLSchema}"
XBRLI_NS: str = "{http://www.xbrl.org/2003/instance}"

NAME_SPACES: dict = {
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrldt": "http://xbrl.org/2005/xbrldt",
    "xbrli": "http://www.xbrl.org/2003/instance",
    "xbrldi": "http://xbrl.org/2006/xbrldi"
}


class ExplicitMember:
    """
    Representation of an explicit member in xbrl.

    XML Example:
    <xbrldi:explicitMember dimension="us-gaap:StatementBusinessSegmentsAxis">aapl:EuropeSegmentMember</xbrldi:explicitMember>
    """

    def __init__(self, dimension: Concept, member: Concept) -> None:
        self.dimension = dimension
        self.member = member

    def __str__(self) -> str:
        return "{} on dimension {}".format(self.member.name, self.dimension.name)


class AbstractContext(abc.ABC):
    """
    Abstract class used for a context

    The segment array stores the dimensional information about the context. According to the XBRL Dimensions 1.0
    specification, the segment array can either have explicit members or typed members. This parser will only
    parse explicit members.
    """

    def __init__(self, xml_id: str, entity: str) -> None:
        self.xml_id: str = xml_id
        self.entity: str = entity
        self.segments: List[ExplicitMember] = []


class InstantContext(AbstractContext):
    """
    Class representing an instant context:
    XML Example:
    <xbrli:context id="I2016Q3Sep9">
        <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0001495320</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:instant>2015-09-09</xbrli:instant></xbrli:period>
    </xbrli:context>
    """

    def __init__(self, xml_id: str, entity: str, instant_date: date) -> None:
        super().__init__(xml_id, entity)
        self.instant_date: date = instant_date

    def __str__(self) -> str:
        return '{} {} dimension'.format(self.instant_date, len(self.segments))


class TimeFrameContext(AbstractContext):
    """
    Class representing a time frame context
    XML Example:
    <xbrli:context id="FD2016Q2YTD">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0001495320</xbrli:identifier></xbrli:entity>
        <xbrli:period>
            <xbrli:startDate>2015-02-01</xbrli:startDate><xbrli:endDate>2015-08-01</xbrli:endDate>
        </xbrli:period>
    </xbrli:context>
    """

    def __init__(self, xml_id: str, entity: str, start_date: date, end_date: date) -> None:
        super().__init__(xml_id, entity)
        self.start_date: date = start_date
        self.end_date: date = end_date

    def __str__(self) -> str:
        return '{} to {} {} dimension'.format(self.start_date, self.end_date, len(self.segments))


class ForeverContext(AbstractContext):
    """
    Class representing a forever context
    XML Example:
    <xbrli:context id="Forever">
        <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000880285</xbrli:identifier></xbrli:entity>
        <xbrli:period><xbrli:forever/></xbrli:period>
    </xbrli:context>
    """

    def __init__(self, xml_id: str, entity: str) -> None:
        super().__init__(xml_id, entity)


class AbstractUnit(abc.ABC):
    """
    Class representing a Unit, defined in the instance file
    """

    def __init__(self, unit_id: str) -> None:
        self.unit_id: str = unit_id


class SimpleUnit(AbstractUnit):
    """
    Class representing a Simple Unit.
    XML example:
    <xbrli:unit id="shares">
        <xbrli:measure>xbrli:shares</xbrli:measure>
    </xbrli:unit>
    """

    def __init__(self, unit_id: str, unit: str) -> None:
        super().__init__(unit_id)
        self.unit: str = unit

    def __str__(self):
        return self.unit


class DivideUnit(AbstractUnit):
    """
    Class representing a divided unit (i.e usd/share)
    XML example:
    <xbrli:unit id="usdPerShare">
        <xbrli:divide>
            <xbrli:unitNumerator><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unitNumerator>
            <xbrli:unitDenominator><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unitDenominator>
        </xbrli:divide>
    </xbrli:unit>
  """

    def __init__(self, unit_id: str, numerator: str, denominator: str) -> None:
        super().__init__(unit_id)
        self.numerator: str = numerator
        self.denominator: str = denominator

    def __str__(self):
        return self.numerator + '/' + self.denominator


class AbstractFact(abc.ABC):
    """
    Class representing a XBRL Fact.
    A Fact combines a Value with a Concept and a Context
    """

    def __init__(self, concept: Concept, context: AbstractContext, value: any) -> None:
        """
        :param concept: concept from the taxonomy, that the fact is referencing
        :param context: context of the fact
        :param value: value of the fact (can be number or text)
        """
        self.concept: Concept = concept
        self.context: AbstractContext = context
        self.value: any = value
        self.footnote: Footnote or None = None

    def __str__(self) -> str:
        return "{}: {}".format(self.concept.name, str(self.value))


class NumericFact(AbstractFact):
    """
    Class representing a numeric XBRL Fact
    XML Example:
    <us-gaap:Assets contextRef="FI2015Q4" decimals="-3" id="Fact-7214827CB0865D3EDB8BC10FF27FAF5E"
        unitRef="usd">377284000</us-gaap:Assets>
    """

    def __init__(self, concept: Concept, context: AbstractContext, value: float or None, unit: AbstractUnit,
                 decimals: int or None) -> None:
        """
        :param concept: see Abstract Fact
        :param context: see Abstract Fact
        :param value: see Abstract Fact
        :param unit: unit of the Numeric fact (i.e usd or usd/share)
        :param decimals: how accurate the number is. If decimals is none, the value of the fact is considered as
        accurate, without rounding errors
        """
        super().__init__(concept, context, value)
        self.unit: AbstractUnit = unit
        self.decimals: int or None = decimals


class TextFact(AbstractFact):
    """
    Class representing a text XBRL Fact
    XML Example:
    <dei:DocumentFiscalPeriodFocus contextRef="c-123" id="f-123">Q2</dei:DocumentFiscalPeriodFocus>
    @warning The content of a Text fact can be huge. Especially for Text Blocks, those can also contain HTML code
    """

    def __init__(self, concept: Concept, context: AbstractContext, value: str) -> None:
        super().__init__(concept, context, value)


class Footnote:
    """
    Class representing a footnote
    https://www.xbrl.org/Specification/XBRL-2.1/REC-2003-12-31/XBRL-2.1-REC-2003-12-31+corrected-errata-2013-02-20.html#_4.11

    XML Example:
     <link:footnote id=".." xlink:label=".." xlink:role="http://www.xbrl.org/2003/role/footnote" xlink:type="resource"
     xml:lang="en-US">The domestic loss in 2020 versus domestic income in 2019 was mainly related to the ... </link:footnote>

    """

    def __init__(self, content: str, lang: str) -> None:
        """
        :param content: content of the footnote
        :param lang: language of the footnote
        """
        self.content = content
        self.lang = lang


class XbrlInstance(abc.ABC):
    """
    Class representing a xbrl instance file
    """
    def __init__(self, url: str or IOBase or StringIO, taxonomy: TaxonomySchema, facts: List[AbstractFact], context_map: dict,
                 unit_map: dict) -> None:
        """
        :param taxonomy: taxonomy file that the instance file references (via link:schemaRef)
        :param facts: array of all facts that the instance contains
        """
        self.taxonomy: TaxonomySchema = taxonomy
        self.facts: List[AbstractFact] = facts
        self.instance_url: str or IOBase or StringIO = url
        self.context_map: dict = context_map
        self.unit_map: dict = unit_map

    def __str__(self) -> str:
        if isinstance(self.instance_url, str):
            file_name: str = self.instance_url.split('/')[-1]
        elif isinstance(self.instance_url, IOBase):
            file_name: str = self.instance_url.__str__()
        return "{} with {} facts".format(file_name, len(self.facts))


def parse_xbrl_url(instance_url: str, cache: HttpCache) -> XbrlInstance:
    """
    Parses a instance file with it's taxonomy
    :param instance_url: url to the instance file (on the internet)
    :param cache: HttpCache instance
    This function will check, if the instance file is already in the cache and load it from there based on the
    instance_url.
    For EDGAR submissions: Before calling this method; extract the enclosure and copy the files to the cache.
        i.e. Use CacheHelper.extract_edgar_enclosure()
    :return:
    """
    instance_path: str = cache.cache_file(instance_url)
    return parse_xbrl(instance_path, cache, instance_url)


def parse_xbrl(instance_path: str or IOBase or StringIO, cache: HttpCache, instance_url: str or None = None) -> XbrlInstance:
    """
    Parses a instance file with it's taxonomy
    :param instance_path: url to the instance file (on the internet)
    :param cache: HttpCache instance
    :param instance_url: optional url to the instance file. Is sometimes necessary if the xbrl filings have their own
    extension taxonomy. If i.e. a submission from the sec is parsed, the instance file might reference the taxonomy schema
    with a relative path (since it is in the same directory as the instance file) schemaRef="./aapl-20211231.xsd"
    :return:
    """
    root: ET.Element = parse_file(instance_path).getroot()
    # get the link to the taxonomy schema and parse it
    schema_ref: ET.Element = root.find(LINK_NS + 'schemaRef')
    schema_uri: str = schema_ref.attrib[XLINK_NS + 'href']

    # check if the schema uri is relative or absolute
    # submissions from SEC normally have their own schema files, whereas submissions from the uk have absolute schemas
    if schema_uri.startswith('http'):
        # fetch the taxonomy extension schema from remote
        taxonomy: TaxonomySchema = parse_taxonomy_url(schema_uri, cache)
    elif instance_url:
        # fetch the taxonomy extension schema from remote by reconstructing the url
        schema_url = resolve_uri(instance_url, schema_uri)
        taxonomy: TaxonomySchema = parse_taxonomy_url(schema_url, cache)
    elif isinstance(instance_path, str):
        # try to find the taxonomy extension schema file locally because no full url can be constructed
        schema_path = resolve_uri(instance_path, schema_uri)
        taxonomy: TaxonomySchema = parse_taxonomy(schema_path, cache)
    elif isinstance(instance_path, IOBase):
        taxonomy: TaxonomySchema = parse_taxonomy(instance_path, cache)

    # parse contexts and units
    context_dir = _parse_context_elements(root.findall('xbrli:context', NAME_SPACES), root.attrib['ns_map'], taxonomy,
                                          cache)
    unit_dir = _parse_unit_elements(root.findall('xbrli:unit', NAME_SPACES))

    # parse facts
    facts: List[AbstractFact] = []
    for fact_elem in root:
        # skip contexts and units
        if 'context' in fact_elem.tag or 'unit' in fact_elem.tag or 'schemaRef' in fact_elem.tag:
            continue
        # check if the element has the required attributes
        if 'contextRef' not in fact_elem.attrib:
            continue

        # check if the fact has a value (some facts are like <us-gaap:Assets ... \>
        if fact_elem.text is None or len(str(fact_elem.text).strip()) == 0:
            continue

        # find the taxonomy where the tag is coming from
        taxonomy_ns, concept_name = fact_elem.tag.split('}')
        taxonomy_ns = taxonomy_ns.replace('{', '')
        # get the concept object from the taxonomy
        tax = taxonomy.get_taxonomy(taxonomy_ns)
        if tax is None:
            tax = _load_common_taxonomy(cache, taxonomy_ns, taxonomy)

        if concept_name in tax.name_id_map:
            concept: Concept = tax.concepts[tax.name_id_map[concept_name]]
            context: AbstractContext = context_dir[fact_elem.attrib['contextRef'].strip()]

            if 'unitRef' in fact_elem.attrib:
                # the fact is a numerical fact
                # get the unit
                unit: AbstractUnit = unit_dir[fact_elem.attrib['unitRef'].strip()]
                decimals_text: str = str(fact_elem.attrib['decimals']).strip()
                decimals: int = None if decimals_text.lower() == 'inf' else int(decimals_text)
                fact = NumericFact(concept, context, float(fact_elem.text), unit, decimals)
            else:
                # the fact is probably a text fact
                fact = TextFact(concept, context, fact_elem.text.strip())
            facts.append(fact)

    return XbrlInstance(instance_url if instance_url else instance_path, taxonomy, facts, context_dir, unit_dir)


def parse_ixbrl_url(instance_url: str, cache: HttpCache) -> XbrlInstance:
    """
    Parses a inline XBRL (iXBRL) instance file.
    :param cache: HttpCache instance
    :param instance_url: url to the instance file(on the internet)
    This function will check, if the instance file is already in the cache and load it from there based on the
    instance_url.
    For EDGAR submissions: Before calling this method; extract the enclosure and copy the files to the cache.
        i.e. Use CacheHelper.extract_edgar_enclosure()
    :return:
    """
    instance_path: str = cache.cache_file(instance_url)
    return parse_ixbrl(instance_path, cache, instance_url)


def parse_ixbrl(instance_path: str or IOBase or StringIO, cache: HttpCache, instance_url: str or None = None, encoding=None) -> XbrlInstance:
    """
    Parses a inline XBRL (iXBRL) instance file.
    :param instance_path: path to the submission you want to parse
    :param cache: HttpCache instance
    :param instance_url: url to the instance file(on the internet)
    :param encoding: optionally specify a file encoding
    This function will check, if the instance file is already in the cache and load it from there based on the
    instance_url.
    For EDGAR submissions: Before calling this method; extract the enclosure and copy the files to the cache.
        i.e. Use CacheHelper.extract_edgar_enclosure()
    :return:
    """
    """
    In contrary to the XBRL-parse method we use here the actual root instead of the root element!!!
    to the .getRoot() is missing. This has the benefit, that we can search the document with absolute xpath expressions
    => in the XBRL-parse function root is ET.Element, here just an instance of ElementTree class!
    """

    if isinstance(instance_path, str):
        instance_file = open(instance_path, "r", encoding=encoding)
    elif isinstance(instance_path, IOBase):
        instance_file = instance_path
    contents = instance_file.read()
    pattern = r'<[ ]*script.*?\/[ ]*script[ ]*>'
    contents = re.sub(pattern, '', contents, flags=(re.IGNORECASE | re.MULTILINE | re.DOTALL))

    root: ET.ElementTree = parse_file(StringIO(contents))
    ns_map: dict = root.getroot().attrib['ns_map']
    # get the link to the taxonomy schema and parse it
    schema_ref: ET.Element = root.find('.//{}schemaRef'.format(LINK_NS))
    schema_uri: str = schema_ref.attrib[XLINK_NS + 'href']

    # check if the schema uri is relative or absolute
    # submissions from SEC normally have their own schema files, whereas submissions from the uk have absolute schemas
    if schema_uri.startswith('http'):
        # fetch the taxonomy extension schema from remote
        taxonomy: TaxonomySchema = parse_taxonomy_url(schema_uri, cache)
    elif instance_url:
        # fetch the taxonomy extension schema from remote by reconstructing the url
        schema_url = resolve_uri(instance_url, schema_uri)
        taxonomy: TaxonomySchema = parse_taxonomy_url(schema_url, cache)
    elif isinstance(instance_path, str):
        # try to find the taxonomy extension schema file locally because no full url can be constructed
        schema_path = resolve_uri(instance_path, schema_uri)
        taxonomy: TaxonomySchema = parse_taxonomy(schema_path, cache)
    elif isinstance(instance_path, IOBase):
        taxonomy: TaxonomySchema = parse_taxonomy(instance_path, cache)

    # get all contexts and units
    xbrl_resources: ET.Element = root.find('.//ix:resources', ns_map)
    if xbrl_resources is None: raise InstanceParseException('Could not find xbrl resources in file')
    # parse contexts and units
    context_dir = _parse_context_elements(xbrl_resources.findall('xbrli:context', NAME_SPACES), ns_map, taxonomy, cache)
    unit_dir = _parse_unit_elements(xbrl_resources.findall('xbrli:unit', NAME_SPACES))

    # parse facts
    facts: List[AbstractFact] = []
    fact_elements: List[ET.Element] = root.findall('.//ix:nonFraction', ns_map) + root.findall('.//ix:nonNumeric',
                                                                                               ns_map)
    for fact_elem in fact_elements:
        # update the prefix map (sometimes the xmlns is defined at XML-Element level and not at the root element)
        _update_ns_map(ns_map, fact_elem.attrib['ns_map'])
        taxonomy_prefix, concept_name = fact_elem.attrib['name'].split(':')

        tax = taxonomy.get_taxonomy(ns_map[taxonomy_prefix])
        if tax is None: tax = _load_common_taxonomy(cache, ns_map[taxonomy_prefix], taxonomy)

        concept: Concept = tax.concepts[tax.name_id_map[concept_name]]
        context: AbstractContext = context_dir[fact_elem.attrib['contextRef'].strip()]
        # ixbrl values are not normalized! They are formatted (i.e. 123,000,000)

        if fact_elem.tag == '{' + ns_map['ix'] + '}nonFraction':
            fact_value: float or None = _extract_non_fraction_value(fact_elem)

            unit: AbstractUnit = unit_dir[fact_elem.attrib['unitRef'].strip()]
            decimals_text: str = str(fact_elem.attrib['decimals']).strip() if 'decimals' in fact_elem.attrib else '0'
            decimals: int = None if decimals_text.lower() == 'inf' else int(decimals_text)

            facts.append(NumericFact(concept, context, fact_value, unit, decimals))
        elif fact_elem.tag == '{' + ns_map['ix'] + '}nonNumeric':
            fact_value: str = _extract_non_numeric_value(fact_elem)
            facts.append(TextFact(concept, context, str(fact_value)))

    return XbrlInstance(instance_url if instance_url else instance_path, taxonomy, facts, context_dir, unit_dir)


def _extract_non_numeric_value(fact_elem: ET.Element) -> str:
    """
    This function parses a ix:nonNumeric fact as defined in:
    https://www.xbrl.org/Specification/inlineXBRL-part1/PWD-2013-02-13/inlineXBRL-part1-PWD-2013-02-13.html#d1e6391
    :param fact_elem:
    :return:
    """
    fact_value = '' if fact_elem.text is None else fact_elem.text

    # recursively iterate over all children (<ix:nonNumeric><b>data</b></ix:nonNumeric>)
    for children in fact_elem:
        fact_value += _extract_text_value(children)

    fact_format = fact_elem.attrib['format'] if 'format' in fact_elem.attrib else None
    if fact_format:
        # extract transformation registry namespace and transformation rule code
        registryPrefix, formatCode = fact_format.split(':')
        registryNS: str = fact_elem.attrib['ns_map'][registryPrefix]
        try:
            fact_value = normalize(registryNS, formatCode, fact_value)
        except TransformationNotImplemented:
            logging.info(f'Transformation rule {formatCode} of registry {registryPrefix} is not supported. '
                         f'The parser will just parse the value as it is and not transform it according to the rule.')
            return fact_value
        except TransformationException:
            logging.warning(f'Could not transform value "{fact_value}" with format {fact_format}')
            return fact_value
    return fact_value


def _extract_non_fraction_value(fact_elem: ET.Element) -> float or None or str:
    """
    https://www.xbrl.org/Specification/inlineXBRL-part1/PWD-2013-02-13/inlineXBRL-part1-PWD-2013-02-13.html#d1e5045
    :param fact_elem:
    :return:
    """
    if 'xsi' in fact_elem.attrib['ns_map']:
        xsi_nil_attrib: str = '{' + fact_elem.attrib['ns_map']['xsi'] + '}nil'
        if xsi_nil_attrib in fact_elem.attrib and fact_elem.attrib[xsi_nil_attrib] == 'true':
            return None

    fact_value = '' if fact_elem.text is None else fact_elem.text
    # recursively iterate over all children (<ix:nonNumeric><b>data</b></ix:nonNumeric>)
    for children in fact_elem:
        fact_value += _extract_text_value(children)

    fact_format = fact_elem.attrib['format'] if 'format' in fact_elem.attrib else None
    value_scale: int = int(fact_elem.attrib['scale']) if 'scale' in fact_elem.attrib else 0
    value_sign: str or None = fact_elem.attrib['sign'] if 'sign' in fact_elem.attrib else None

    if fact_format:
        # extract transformation registry namespace and transformation rule code
        registryPrefix, formatCode = fact_format.split(':')
        registryNS: str = fact_elem.attrib['ns_map'][registryPrefix]
        try:
            fact_value = normalize(registryNS, formatCode, fact_value)
        except TransformationNotImplemented:
            logging.info(f'Transformation rule {formatCode} of registry {registryPrefix} is not supported. '
                         f'The parser will just parse the value as it is and not transform it according to the rule.')
            return fact_value
        except TransformationException:
            logging.warning(f'Could not transform value "{fact_value}" with format {fact_format}')
            return fact_value

    scaled_value = float(fact_value) * pow(10, value_scale)
    # Floating-point error mitigation
    if abs(scaled_value) > 1e6: scaled_value = float(round(scaled_value))
    if value_sign == '-':
        scaled_value = -scaled_value

    return scaled_value


def _extract_text_value(element: ET.Element) -> str:
    text = '' if element.text is None else element.text
    if element.tail: text += element.tail
    for children in element:
        text += _extract_text_value(children)
    return text


def _parse_context_elements(context_elements: List[ET.Element], ns_map: dict, taxonomy: TaxonomySchema,
                            cache: HttpCache) -> dict:
    """
    Parses all context elements from the instance file and stores them into a dictionary with the
    context id as key
    :param context_elements: array of context elements from the xml of html
    :param ns_map: the prefix - namespace map of the document
    :param taxonomy: The taxonomy of the instance file (needed for parsing dimensional information)
    :return:
    """
    context_dict = {}
    for context_elem in context_elements:
        context_id: str = context_elem.attrib['id']
        entity: str = str(context_elem.find('xbrli:entity/xbrli:identifier', NAME_SPACES).text).strip()

        instant_date: ET.Element = context_elem.find('xbrli:period/xbrli:instant', NAME_SPACES)
        start_date: ET.Element = context_elem.find('xbrli:period/xbrli:startDate', NAME_SPACES)
        end_date: ET.Element = context_elem.find('xbrli:period/xbrli:endDate', NAME_SPACES)
        forever: ET.Element = context_elem.find('xbrli:period/xbrli:forever', NAME_SPACES)

        if instant_date is not None:
            # the context is a instant context
            context = InstantContext(context_id, entity,
                                     datetime.strptime(instant_date.text.strip()[:10], '%Y-%m-%d').date())
        elif forever is not None:
            context = ForeverContext(context_id, entity)
        else:
            # the context is a time frame context
            context = TimeFrameContext(context_id, entity,
                                       datetime.strptime(start_date.text.strip()[:10], '%Y-%m-%d').date(),
                                       datetime.strptime(end_date.text.strip()[:10], '%Y-%m-%d').date())

        # check if dimensional information exists on this context and parse it
        segment: ET.Element = context_elem.find('xbrli:entity/xbrli:segment', NAME_SPACES)
        if segment is not None:
            for explicit_member_elem in segment.findall('xbrldi:explicitMember', NAME_SPACES):
                _update_ns_map(ns_map, explicit_member_elem.attrib['ns_map'])
                dimension_prefix, dimension_concept_name = explicit_member_elem.attrib['dimension'].strip().split(':')
                member_prefix, member_concept_name = explicit_member_elem.text.strip().split(':')
                # get the taxonomy where the dimension attribute is defined
                dimension_tax = taxonomy.get_taxonomy(ns_map[dimension_prefix])
                # check if the taxonomy was found
                if dimension_tax is None:
                    # try to subsequently load the taxonomy
                    dimension_tax = _load_common_taxonomy(cache, ns_map[dimension_prefix], taxonomy)

                # get the taxonomy where the member attribute is defined
                member_tax = dimension_tax if member_prefix == dimension_prefix else taxonomy.get_taxonomy(
                    ns_map[member_prefix])
                # check if the taxonomy was found
                if member_tax is None:
                    # try to subsequently load the taxonomy
                    member_tax = _load_common_taxonomy(cache, ns_map[member_prefix], taxonomy)
                if dimension_concept_name in dimension_tax.name_id_map and member_concept_name in member_tax.name_id_map:
                    dimension_concept: Concept = dimension_tax.concepts[dimension_tax.name_id_map[dimension_concept_name]]
                    member_concept: Concept = member_tax.concepts[member_tax.name_id_map[member_concept_name]]

                    # add the explicit member to the context
                    context.segments.append(ExplicitMember(dimension_concept, member_concept))

        context_dict[context_id] = context
    return context_dict


def _update_ns_map(ns_map: dict, new_ns_map: dict) -> None:
    """
    Compares the new_ns_map with the ns_map and adds prefix/namespace mappings that are not present in ns_map
    :param ns_map:
    :param new_ns_map:
    :return:
    """
    for prefix in new_ns_map:
        if prefix not in ns_map:
            ns_map[prefix] = new_ns_map[prefix]


def _parse_unit_elements(unit_elements: List[ET.Element]) -> dict:
    """
    Parses all unit elements from the instance file and stores them into a dictionary with the
    unit id as key
    :param unit_elements:
    :return:
    """
    unit_dict = {}
    for unit_elem in unit_elements:
        unit_id: str = unit_elem.attrib['id']

        simple_unit: ET.Element = unit_elem.find('xbrli:measure', NAME_SPACES)
        divide: ET.Element = unit_elem.find('xbrli:divide', NAME_SPACES)

        if simple_unit is not None:
            unit = SimpleUnit(unit_id, simple_unit.text.strip())
        else:
            unit = DivideUnit(unit_id,
                              divide.find('xbrli:unitNumerator/xbrli:measure', NAME_SPACES).text.strip(),
                              divide.find('xbrli:unitDenominator/xbrli:measure', NAME_SPACES).text.strip())
        unit_dict[unit_id] = unit
    return unit_dict


def _load_common_taxonomy(cache: HttpCache, namespace: str, taxonomy: TaxonomySchema) -> TaxonomySchema:
    """
    tries to load a common taxonomy
    :param cache: http cache instance
    :param namespace: namespace of the taxonomy
    :raises TaxonomyNotFound: if the taxonomy could not be loaded
    :return:
    """
    tax = parse_common_taxonomy(cache, namespace)
    if tax is None: raise TaxonomyNotFound(namespace)
    taxonomy.imports.append(tax)
    return tax


class XbrlParser:
    """
    XbrlParser to make interaction easier.

    """

    def __init__(self, cache: HttpCache):
        self.cache = cache

    def parse_instance(self, url: str) -> XbrlInstance:
        """
        Parses a xbrl instance (either xbrl or ixbrl)
        :param url: url to the instance file.
            i.e: https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm
        :return:
        """
        if url.split('.')[-1] == 'xml' or url.split('.')[-1] == 'xbrl':
            return parse_xbrl_url(url, self.cache)
        return parse_ixbrl_url(url, self.cache)

    def parse_instance_locally(self, path: str, instance_url: str or None = None) -> XbrlInstance:
        """
        Parses a locally stored xbrl instance (either xbrl or ixbrl)
        NOTE:
            If the instance document or extension taxonomy have relative imports the parser will also search for those
            files locally!
            Example: your instance document is located at './data/aapl/2020/aapl-20200926.html' and the instance document
            imports the taxonomy using a relative path '<schemaRef href="./aapl-20200926.xsd"/>' the parser will search
            the document at "./data/aapl/2020/aapl-20200926.xsd".

        :param path: the path to the instance document you want to parse
        :param instance_url: this parameter overrides the above described behaviour. If you also provide the url where the
        instance document was downloaded, the parser can fetch relative imports using this base url
        :return:
        """

        if path.split('.')[-1] == 'xml' or path.split('.')[-1] == 'xbrl':
            return parse_xbrl(path, self.cache, instance_url)
        return parse_ixbrl(path, self.cache, instance_url)

    def parse_file_obj(self, file_obj, instance_url: str or None = None, is_xbrl: bool = True):
        if is_xbrl is True:
            return parse_xbrl(file_obj, self.cache, instance_url)
        return parse_ixbrl(file_obj, self.cache, instance_url)

    def __str__(self) -> str:
        return 'XbrlParser with cache dir at {}'.format(self.cache.cache_dir)
