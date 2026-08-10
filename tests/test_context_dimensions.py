"""
Unit tests for dimensional information on contexts.

XBRL 2.1 allows dimensions to be carried in either xbrli:segment or
xbrli:scenario. US SEC filings generally use segment, while ESEF and other
IFRS filings use scenario.
"""

import unittest
import xml.etree.ElementTree as ET

from xbrl.instance import ExplicitMember, TypedMember, _parse_context_elements

NS_MAP = {"ex": "http://www.example.com/20210101"}

CONTEXT_TEMPLATE = """
<xbrli:context xmlns:xbrli="http://www.xbrl.org/2003/instance"
               xmlns:xbrldi="http://xbrl.org/2006/xbrldi"
               xmlns:ex="http://www.example.com/20210101"
               id="c1">
    <xbrli:entity>
        <xbrli:identifier scheme="http://www.sec.gov/CIK">0000000000</xbrli:identifier>
        {segment}
    </xbrli:entity>
    <xbrli:period>
        <xbrli:startDate>2020-01-01</xbrli:startDate>
        <xbrli:endDate>2020-12-31</xbrli:endDate>
    </xbrli:period>
    {scenario}
</xbrli:context>
"""

EXPLICIT = '<xbrldi:explicitMember dimension="ex:RegionAxis">ex:EuropeMember</xbrldi:explicitMember>'
TYPED = (
    '<xbrldi:typedMember dimension="ex:RegionAxis">'
    "<ex:RegionAxis.domain>EU</ex:RegionAxis.domain>"
    "</xbrldi:typedMember>"
)


class _FakeConcept:
    def __init__(self, name):
        self.name = name
        self.namespace = None


class _FakeTaxonomy:
    """Resolves any concept name to a concept of that name."""

    def __init__(self):
        self.name_id_map = _Everything()
        self.concepts = _Concepts()
        self.imports = []

    def get_taxonomy(self, _namespace):
        return self


class _Everything(dict):
    def __getitem__(self, key):
        return key


class _Concepts(dict):
    def __getitem__(self, key):
        return _FakeConcept(key)


def _parse(segment="", scenario=""):
    xml = CONTEXT_TEMPLATE.format(segment=segment, scenario=scenario)
    element = ET.fromstring(xml)
    taxonomy = _FakeTaxonomy()
    contexts = _parse_context_elements([element], dict(NS_MAP), taxonomy, None)
    return contexts["c1"]


class ContextDimensionsTest(unittest.TestCase):
    def test_explicit_member_in_segment(self):
        context = _parse(segment=f"<xbrli:segment>{EXPLICIT}</xbrli:segment>")

        self.assertEqual(len(context.segments), 1)
        member = context.segments[0]
        self.assertIsInstance(member, ExplicitMember)
        self.assertEqual(member.dimension.name, "RegionAxis")
        self.assertEqual(member.member.name, "EuropeMember")

    def test_explicit_member_in_scenario(self):
        """ESEF filings put dimensions in xbrli:scenario, not xbrli:segment."""
        context = _parse(scenario=f"<xbrli:scenario>{EXPLICIT}</xbrli:scenario>")

        self.assertEqual(len(context.segments), 1)
        member = context.segments[0]
        self.assertIsInstance(member, ExplicitMember)
        self.assertEqual(member.dimension.name, "RegionAxis")
        self.assertEqual(member.member.name, "EuropeMember")

    def test_typed_member_in_scenario(self):
        context = _parse(scenario=f"<xbrli:scenario>{TYPED}</xbrli:scenario>")

        self.assertEqual(len(context.segments), 1)
        member = context.segments[0]
        self.assertIsInstance(member, TypedMember)
        self.assertEqual(member.dimension.name, "RegionAxis")
        self.assertEqual(member.domain, ["EU"])

    def test_segment_and_scenario_are_both_collected(self):
        context = _parse(
            segment=f"<xbrli:segment>{EXPLICIT}</xbrli:segment>",
            scenario=f"<xbrli:scenario>{TYPED}</xbrli:scenario>",
        )

        self.assertEqual(len(context.segments), 2)
        self.assertIsInstance(context.segments[0], ExplicitMember)
        self.assertIsInstance(context.segments[1], TypedMember)

    def test_context_without_dimensions(self):
        context = _parse()

        self.assertEqual(context.segments, [])


if __name__ == "__main__":
    unittest.main()
