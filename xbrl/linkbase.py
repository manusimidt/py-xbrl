"""
Module for parsing Linkbases

There are three types of Linkbase:
relation linkbases: calculation, definition and presentation
label linkbase: lab
reference linkbase: ref
"""
import abc
import os
from typing import List
from lxml import etree as ET
from abc import ABC
from enum import Enum

from xbrl import XbrlParseException, LinkbaseNotFoundException
from xbrl.cache import HttpCache
from xbrl.helper.uri_helper import resolve_uri

LINK_NS: str = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS: str = "{http://www.w3.org/1999/xlink}"
XBRLDT_NS: str = "{http://xbrl.org/2005/xbrldt}"
XML_NS: str = "{http://www.w3.org/XML/1998/namespace}"


class LinkbaseType(Enum):
    """ Enum of linkbase types, that this parser can parse """
    DEFINITION = 0x001
    CALCULATION = 0x002
    PRESENTATION = 0x003
    LABEL = 0x004

    @staticmethod
    def get_type_from_role(role: str) -> int or None:
        """
        Takes a xlink:role (i.e http://www.xbrl.org/2003/role/definitionLinkbaseRef) and returns the corresponding
        LinkbaseType
        @param role:
        @return: LinkbaseType or None if the role is unknown
        """
        return {
            'http://www.xbrl.org/2003/role/definitionLinkbaseRef': LinkbaseType.DEFINITION,
            'http://www.xbrl.org/2003/role/calculationLinkbaseRef': LinkbaseType.CALCULATION,
            'http://www.xbrl.org/2003/role/presentationLinkbaseRef': LinkbaseType.PRESENTATION,
            'http://www.xbrl.org/2003/role/labelLinkbaseRef': LinkbaseType.LABEL,
        }.get(role, None)

    @staticmethod
    def guess_linkbase_role(href: str) -> int or None:
        """
        Guesses the linkbase role based on the name of the linkbase
        @param href:
        @return:
        """
        return LinkbaseType.DEFINITION if '_def' in href \
            else LinkbaseType.CALCULATION if '_cal' in href \
            else LinkbaseType.PRESENTATION if '_pre' in href \
            else LinkbaseType.LABEL if '_lab' in href \
            else None


class AbstractArcElement(ABC):
    """
    Represents an abstract Arc
    An Arc links two Locators together and assigns a relation ship between those two items.
    Arcs are used in all linkbases (definition, calculation, presentation and label)

    From the Xbrl Specification 2.0:
    Standard Arc Element:
        An element derived from xl:arc that is defined in this specification, Specifically,
        one of: link:presentationArc, link:calculationArc, link:labelArc, link:referenceArc, or link:definitionArc.

    i.e:
    <link:definitionArc order="30"
        xlink:arcrole="http://xbrl.org/int/dim/arcrole/domain-member"
        xlink:from="loc_AssetsAbstract"
        xlink:to="loc_CashAndCashEquivalentsAtCarryingValue" xlink:type="arc"/>

    This arc describes the relationship between Assets and Cash and Cash Equivalents. Cash is a sub-domain from Assets.
    """

    def __init__(self, from_locator, arcrole: str, order: int) -> None:
        """

        @param from_locator: Locator Object from that the arc is pointing from
        to_locator: is missing here, because not all arc's point to another locator. A label arc for example points
            to multiple link:label's
        @type from_locator: Locator
        @param arcrole: Role of the arc
        @param order: Order attribute of the arc. Only makes sense in combination with the arc role.
            i.e arcrole parent-child together with the order attribute defines a hierarchical relationship between elements
            (XBRL for Interactive Data, 2009, p.59)
        """
        self.from_locator = from_locator
        self.arcrole: str = arcrole
        self.order: int = order

    @abc.abstractmethod
    def to_dict(self):
        """ Returns a dictionary representation of the arc """
        pass


class RelationArc(AbstractArcElement, ABC):
    """
    A Relation arc is an abstract implementation of an AbstractArc Element that has the to_locator attribute
    """

    def __init__(self, from_locator, to_locator, arcrole: str, order: int) -> None:
        super().__init__(from_locator, arcrole, order)
        self.to_locator: Locator = to_locator


class DefinitionArc(RelationArc):
    """ Represents a definition arc (link:definitionArc) """

    def __init__(self, from_locator, to_locator, arcrole: str, order: int, closed: bool = None,
                 context_element: str = None) -> None:
        """
        @type from_locator: Locator
        @type to_locator: Locator
        @param arcrole: Can be one of the following: (XBRL for Interactive Data, 2009, p.140)
            - http://xbrl.org/int/dim/arcrole/all:
                connects a measure to a hypercube implying use of dimensions attached to this hypercube and their
                specified breakdowns
                Elements:
                    - closed: boolean,
                    - contextElement: (segment/scenario),
                    - targetRole: anyURI
            - http://xbrl.org/int/dim/arcrole/notAll
                connects a measure to a hypercube prohibiting use of dimensions attached to this hypercube and their
                specified breakdowns
                Elements:
                    - closed: boolean,
                    - contextElement: (segment/scenario),
                    - targetRole: anyURI
            - http://xbrl.org/int/dim/arcrole/hypercube-dimension
                connects a hypercube and a dimension item
                Elements:
                    - targetRole: anyURI
            - http://xbrl.org/int/dim/arcrole/dimension-domain
                connects a dimension item to its top level members in every variation of a breakdown
                Elements:
                    - usage: boolean,
                    - targetRole: anyURI
            - http://xbrl.org/int/dim/arcrole/domain-member
                defines hierarchical relations for measures and domain members; in case of measures implies inheritance
                of dimensional characteristics from upper-level concepts
                Elements:
                    - usage:boolean,
                    - targetRole: anyURI
            - http://xbrl.org/int/dim/arcrole/dimension-default
                links dimension item to its default member (usually total of the full breakdown)
                Elements:
                    None
        """
        super().__init__(from_locator, to_locator, arcrole, order)
        self.closed: bool or None = closed
        self.context_element: bool or None = context_element

    def __str__(self) -> str:
        return "Linking to {} as {}".format(str(self.to_locator.name), self.arcrole.split('/')[-1])

    def to_dict(self) -> dict:
        """ Returns a dictionary representation of the arc """
        return {"arcrole": self.arcrole, "order": self.order, "closed": self.closed,
                "contextElement": self.context_element,
                "locator": self.to_locator.to_dict()}


class CalculationArc(RelationArc):
    """ Represents a calculation arc (link:calculationArc) """

    def __init__(self, from_locator, to_locator, order: int, weight: float) -> None:
        """
        @type from_locator: Locator
        @type to_locator: Locator
        @param weight: Defines the sign and multiplication factor for two connected concepts
                        (XBRL for Interactive Data, 2009, p.61)
        """
        # A Calculation arc only has the summation-item arc role
        super().__init__(from_locator, to_locator, "http://www.xbrl.org/2003/arcrole/summation-item", order)
        self.weight: float = weight

    def to_dict(self):
        """ Returns a dictionary representation of the arc """
        return {"arcrole": self.arcrole, "order": self.order, "weight": self.weight,
                "locator": self.to_locator.to_dict()}

    def __str__(self) -> str:
        return "{} {}".format(self.arcrole.split('/')[-1], self.to_locator.concept_id)


class PresentationArc(RelationArc):
    """ Represents a presentation arc (link:presentationArc) """

    def __init__(self, from_locator, to_locator, order: int, priority: int, preferred_label: str = None) -> None:
        """
        @type from_locator: Locator
        @type to_locator: Locator
        @param preferred_label: indicates the most appropriate kind of label to use when presenting the arc's child Concept
        (XBRL Specification 2.1, 5.2.4.2.1)
        """
        # A Presentation arc only has the parent-child arc role
        super().__init__(from_locator, to_locator, "http://www.xbrl.org/2003/arcrole/parent-child", order)
        self.priority = priority
        self.preferred_label: str = preferred_label

    def to_dict(self):
        """ Returns a dictionary representation of the arc """
        return {"arcrole": self.arcrole, "order": self.order,
                "preferredLabel": self.preferred_label, "locator": self.to_locator.to_dict()}

    def __str__(self) -> str:
        return "{} {}".format(self.arcrole.split('/')[-1], self.to_locator.concept_id)


class Label:
    """
    Class representing a label (link:label)
    This class is only used by LabelArcs in label Linkbases

    Example for label in label linkbase:
    <link:label id="lab_Assets_label_en-US" xlink:label="lab_Assets" xlink:role="http://www.xbrl.org/2003/role/label"
        xlink:type="resource" xml:lang="en-US">Assets</link:label>
    """

    def __init__(self, label: str, label_type: str, language: str, text: str) -> None:
        """
        @param label: the xlink:label of the label (locators will be referencing the label over the xlink:label attribute)
        @param label_type: the role of the label, possible values (XBRL for Interactive Data, 2009, p.61):
            - http://www.xbrl.org/2003/role/label:
                Standard label for a concept
            - http://www.xbrl.org/2003/role/terseLabel:
                Short label for a concept, often omitting text that should be inferable when the concept is reported
                in the context of other related concepts
            - http://www.xbrl.org/2003/role/verboseLabel:
                Extended label for a concept, making sure not to omit text that is required to enable the label to be
                understood on a standalone basis
            - http://www.xbrl.org/2003/role/totalLabel:
                The label for a concept for use in presenting values associated with the concept when it is being
                reported as the total of a set of other values
            - http://www.xbrl.org/2003/role/periodStartLabel & http://www.xbrl.org/2003/role/periodEndLabel:
                The label for a concept with periodType="instant" for use in presenting values associated with the
                concept when it is being reported as a start (end) of period value
            - http://www.xbrl.org/2003/role/documentation:
                Documentation of a concept, providing an explanation of its meaning and its appropriate usage and any
                other documentation deemed necessary
        """
        # the label of the link:label element (see Locator label) i.e: lab_Assets
        self.label: str = label
        self.language = language
        # the label itself i.e: "Defined Benefit Plan Disclosure [Line Items]"
        self.text: str = text.strip() if text is not None else text
        # the role of the label i.e: http://www.xbrl.org/2003/role/terseLabel
        self.label_type: str = label_type

    def __str__(self) -> str:
        return self.text


class LabelArc(AbstractArcElement):
    """
    Represents a label arc (link:labelArc)
    The xml representation of a label arc also has a xlink:to attribute, like the Relational Arcs.
    However in contrast to the xlink:to attribute of relational arcs which is pointing to another locator (1:1), the xlink:to
    attribute of a label arc points to multiple label elements

    """

    def __init__(self, from_locator, order: int, labels: List[Label]) -> None:
        """
        @type from_locator: Locator
        @param labels: Array of label objects, the arc is pointing to
        @type labels: Label[]
        """
        # A Label Arc only has the concept-label arc role
        super().__init__(from_locator, "http://www.xbrl.org/2003/arcrole/concept-label", order)
        self.labels = labels

    def __str__(self) -> str:
        return "LabelArc with {} labels".format(len(self.labels))

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the label arc.
        """
        label_obj = {}
        # dynamically add all available labels
        for label in self.labels:
            label_obj[label.label_type] = label.text

        return label_obj


class Locator:
    """
    Represents a Locator. The Locator points from the Linkbase back to the Concept, that is defined in the schema file
    i.e: <link:loc xlink:href="../elts/us-gaap-2019-01-31.xsd#us-gaap_Goodwill" xlink:label="loc_Goodwill"
                xlink:type="locator"/>
    """

    def __init__(self, href: str, name: str):
        """
        @param href: The link, the locator is pointing to. IN ABSOLUTE FORMAT (starting with http...)
        @param name: The name (xlink:label) from the locator
        """
        # the link of the concept the locator is pointing to (i.e: ../elts/us-gaap-2019-01-31.xsd#us-gaap_Goodwill)
        self.href: str = href
        # the label of the Locator (i.e: loc_Goodwill)
        self.name: str = name
        # the id of the concept (i.e: us-gaap_Goodwill)
        self.concept_id: str = href.split('#')[1]
        # This array stores the locators that that are connected with this locator via a label arc, there
        # the current locator was in the to attribute. This array is only used for finding the root locators (the locators
        # that have no parents)
        self.parents: List[Locator] = []
        # This array stores all the labelArcs that reference this locator in the "from" attribute
        self.children: List[AbstractArcElement] = []

    def __str__(self) -> str:
        return "{} with {} children".format(self.name, len(self.children))

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the Locator.
        This method will ignore the parents array and will take the children for building the
        recursive dictionary hierarchy
        @return:
        """
        return {"name": self.name, "href": self.href, "concept_id": self.concept_id,
                "children": [arc_element.to_dict() for arc_element in self.children]}

    def to_simple_dict(self) -> dict:
        """
        Does the same as to_dict() but ignores the ArcElements.
        So it basically returns the hierarchy, without the information in which type of relationship
        parent and children are
        @return:
        """
        return {"concept_id": self.concept_id,
                "children": [arc_element.to_locator.to_simple_dict() for arc_element in self.children]}


class ExtendedLink:
    """
    Generic class for definitionLink, labelLink, referenceLink and calculationLink elements

    From the Xbrl Specification 2.0:
    Standard Extended Link Element:
        An element derived from xl:link that is defined in this specification. Specifically, one of:
        link:presentationLink, link:calculationLink, link:labelLink, link:referenceLink, or link:definitionLink.

    """

    def __init__(self, role: str, elr_id: str or None, root_locators: List[Locator]) -> None:
        """
        @param role: role of the extended link element
        @param elr_id: the link to the extended Link role (as defined in the schema file)
            i.e aapl-20180929.xsd#ConsolidatedStatementsOfComprehensiveIncome
            Is none for label linkbases!
        @param root_locators: Label array of all root locators (all locators that have no parents)
        """
        self.role: str = role
        self.elr_id: str or None = elr_id
        self.root_locators: List[Locator] = root_locators

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the ExtendedLinkElement
        @return:
        """
        return {"role": self.role, "elr_id": self.elr_id,
                "root_locators": [loc.to_dict() for loc in self.root_locators]}

    def to_simple_dict(self) -> dict:
        """
        Does the same as to_dict() but ignores the ArcElements.
        So it basically returns the hierarchy, without the information in which type of relationship
        parent and children are
        @return:
        """
        return {"role": self.role, "children": [loc.to_simple_dict() for loc in self.root_locators]}

    def __str__(self) -> str:
        return self.elr_id


class Linkbase:
    """
    Represents the complete Linkbase
    """

    def __init__(self, extended_links, linkbase_type: LinkbaseType) -> None:
        """
        @param extended_links: All standard extended links that are defined in the linkbase
        @type extended_links: [ExtendedDefinitionLink] or [ExtendedCalculationLink] or [ExtendedPresentationLink] or
                                [ExtendedLabelArc]
        """
        self.extended_links: List[ExtendedLink] = extended_links
        self.type = linkbase_type

    def to_dict(self) -> dict:
        """
        Converts the Linkbase object with in a dictionary representing the Hierarchy of the locators
        @return:
        """
        return {"standardExtendedLinkElements": [el.to_dict() for el in self.extended_links]}

    def to_simple_dict(self) -> dict:
        """
        Does the same as to_dict() but ignores the ArcElements.
        So it basically returns the hierarchy, without the information in which type of relationship
        parent and children are
        @return:
        """
        return {"standardExtendedLinkElements": [el.to_simple_dict() for el in self.extended_links]}


def parse_linkbase_url(linkbase_url: str, linkbase_type: LinkbaseType, cache: HttpCache) -> Linkbase:
    """
    Parses a linkbase given given a url
    """
    if not linkbase_url.startswith('http'): raise XbrlParseException(
        'This function only parses remotely saved linkbases. Please use parse_linkbase to parse local linkbases')

    linkbase_path: str = cache.cache_file(linkbase_url)
    return parse_linkbase(linkbase_path, linkbase_type, linkbase_url)


def parse_linkbase(linkbase_path: str, linkbase_type: LinkbaseType, linkbase_url: str or None = None) -> Linkbase:
    """
    Parses a linkbase and returns a Linkbase object containing all
    locators, arcs and links of the linkbase in a hierarchical order (a Tree)
    A Linkbase usually does not import any additional files.
    Thus we do not need a cache instance
    :param linkbase_path: path to the linkbase
    :param linkbase_type: Type of the linkbase
    :param linkbase_url: if the locator of the linkbase contain relative references to concepts (i.e.: './../schema.xsd#Assets'
    the url has to be set so that the parser can connect the locator with concept from the taxonomy
    :return:
    """
    if linkbase_path.startswith('http'): raise XbrlParseException(
        'This function only parses locally saved linkbases. Please use parse_linkbase_url to parse remote linkbases')
    if not os.path.exists(linkbase_path):
        raise LinkbaseNotFoundException(f"Could not find linkbase at {linkbase_path}")

    root: ET.Element = ET.parse(linkbase_path).getroot()
    # store the role refs in a dictionary, with the role uri as key.
    # Role Refs are xlink's that connect the extended Links to the ELR defined in the schema
    role_refs: dict = {}
    for role_ref in root.findall(LINK_NS + 'roleRef'):
        role_refs[role_ref.attrib['roleURI']] = role_ref.attrib[XLINK_NS + 'href']

    # Loop over all definition/calculation/presentation/label links.
    # Each extended link contains the locators and the definition arc's
    extended_links: List[ExtendedLink] = []

    # figure out if we want to search for definitionLink, calculationLink, presentationLink or labelLink
    # figure out for what type of arcs we are searching; definitionArc, calculationArc, presentationArc or labelArc
    extended_link_tag: str
    arc_type: str
    if linkbase_type == LinkbaseType.DEFINITION:
        extended_link_tag = "definitionLink"
        arc_type = "definitionArc"
    elif linkbase_type == LinkbaseType.CALCULATION:
        extended_link_tag = "calculationLink"
        arc_type = "calculationArc"
    elif linkbase_type == LinkbaseType.PRESENTATION:
        extended_link_tag = "presentationLink"
        arc_type = "presentationArc"
    else:
        extended_link_tag = "labelLink"
        arc_type = "labelArc"

    # loop over all extended links. Extended links can be: link:definitionLink, link:calculationLink e.t.c
    # Note that label linkbases only have one extended link
    for extended_link in root.findall(LINK_NS + extended_link_tag):
        extended_link_role: str = extended_link.attrib[XLINK_NS + 'role']
        # find all locators (link:loc) and arcs (i.e link:definitionArc or link:calculationArc)
        locators = extended_link.findall(LINK_NS + 'loc')
        arc_elements = extended_link.findall(LINK_NS + arc_type)

        # store the locators in a dictionary. The label attribute is the key. This way we can access them in O(1)
        locator_map = {}
        for loc in locators:
            loc_label: str = loc.attrib[XLINK_NS + 'label']
            # check if the locator href is absolute
            locator_href = loc.attrib[XLINK_NS + 'href']
            if not locator_href.startswith('http'):
                # resolve the path
                # todo, try to get the URL here, instead of the path!!!
                locator_href = resolve_uri(linkbase_url if linkbase_url else linkbase_path, locator_href)
            locator_map[loc_label] = Locator(locator_href, loc_label)

        # Performance: extract the labels in advance. The label name (xlink:label) is the key and the value is
        # an array of all labels that have this name. This can be multiple labels (label, terseLabel, documentation...)
        label_map = {}
        if linkbase_type == LinkbaseType.LABEL:
            for label_element in extended_link.findall(LINK_NS + 'label'):
                label_name: str = label_element.attrib[XLINK_NS + 'label']
                label_role: str = label_element.attrib[XLINK_NS + 'role']
                label_lang: str = label_element.attrib[XML_NS + 'lang']
                label_obj = Label(label_name, label_role, label_lang, label_element.text)
                if label_name in label_map:
                    label_map[label_name].append(label_obj)
                else:
                    label_map[label_name] = [label_obj]

        for arc_element in arc_elements:
            # if the use of the element referenced by the arc is prohibited, just ignore it
            if 'use' in arc_element.attrib and arc_element.attrib['use'] == 'prohibited': continue
            # extract the attributes if the arc. The arc always connects two locators through the from and to attributes
            # additionally it defines the relationship between these two locators (arcrole)
            arc_from: str = arc_element.attrib[XLINK_NS + 'from']
            arc_to: str = arc_element.attrib[XLINK_NS + 'to']
            arc_role: str = arc_element.attrib[XLINK_NS + 'arcrole']
            arc_order: int = arc_element.attrib['order'] if 'order' in arc_element.attrib else None

            # the following attributes are linkbase specific, so we have to check if they exist!
            # Needed for (sometimes) definitionArc
            arc_closed: bool = bool(arc_element.attrib[XBRLDT_NS + "closed"]) \
                if (XBRLDT_NS + "weight") in arc_element.attrib else None
            arc_context_element: str = arc_element.attrib[XBRLDT_NS + "contextElement"] if \
                (XBRLDT_NS + "contextElement") in arc_element.attrib else None
            # Needed for calculationArc
            arc_weight: float = float(arc_element.attrib["weight"]) if "weight" in arc_element.attrib else None
            # Needed for presentationArc
            arc_priority: int = int(arc_element.attrib["priority"]) if "priority" in arc_element.attrib else None
            arc_preferred_label: str = arc_element.attrib[
                "preferredLabel"] if "preferredLabel" in arc_element.attrib else None

            # Create the arc object based on the current linkbase type
            arc_object: AbstractArcElement
            if linkbase_type == LinkbaseType.DEFINITION:
                arc_object = DefinitionArc(
                    locator_map[arc_from], locator_map[arc_to], arc_role, arc_order, arc_closed,
                    arc_context_element)
            elif linkbase_type == LinkbaseType.CALCULATION:
                arc_object = CalculationArc(locator_map[arc_from], locator_map[arc_to], arc_order, arc_weight)
            elif linkbase_type == LinkbaseType.PRESENTATION:
                arc_object = PresentationArc(locator_map[arc_from], locator_map[arc_to], arc_order, arc_priority,
                                             arc_preferred_label)
            else:
                # find all labels that are referenced by this arc.
                # These where preprocessed previously, so we can just take them
                arc_object = LabelArc(locator_map[arc_from], arc_order, label_map[arc_to])

            # Build the hierarchy for the Locators.
            if linkbase_type != LinkbaseType.LABEL:
                # This does not work for label linkbase, since link:labelArcs only link to link:labels
                # and not to other locators!!
                locator_map[arc_to].parents.append(locator_map[arc_from])
            locator_map[arc_from].children.append(arc_object)

        # find the top elements of the three (all elements that have no parents)
        root_locators = []
        for locator in locator_map.values():
            if len(locator.parents) == 0:
                root_locators.append(locator)

        # only add the extended link to the linkbase if the link references a role
        # (some filers have empty links in which we are not interested:
        # <definitionLink xlink:type="extended" xlink:role="http://www.xbrl.org/2003/role/link"/>)
        if extended_link_role in role_refs:
            extended_links.append(
                ExtendedLink(extended_link_role, role_refs[extended_link_role], root_locators))
        elif linkbase_type == LinkbaseType.LABEL:
            extended_links.append(ExtendedLink(extended_link_role, None, root_locators))
    return Linkbase(extended_links, linkbase_type)
