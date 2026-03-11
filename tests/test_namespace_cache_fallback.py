"""
Unit tests for namespace resolution fallback from local cache.
"""

import os
import tempfile
import unittest

from xbrl import TaxonomyNotFound
from xbrl.cache import HttpCache
from xbrl.taxonomy import TaxonomyParser


def _write_minimal_xsd(path: str, target_namespace: str) -> None:
    # Minimal valid XSD sufficient for TaxonomyParser.parse_taxonomy()
    # and namespace extraction via targetNamespace.
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
            f'targetNamespace="{target_namespace}" '
            'elementFormDefault="qualified" attributeFormDefault="unqualified">\n'
            "</xsd:schema>\n"
        )


class NamespaceCacheFallbackTest(unittest.TestCase):
    def test_resolves_from_local_cache_and_normalizes_namespace(self):
        # Simulate a cached SEC taxonomy file that is missing from static NS_MAP.
        ns = "http://xbrl.sec.gov/unit-test-tax/2099"
        with tempfile.TemporaryDirectory(prefix="xbrl_cache_") as cache_dir:
            schema_path = os.path.join(
                cache_dir,
                "xbrl.sec.gov",
                "unit-test-tax",
                "2099",
                "unit-test-tax-2099.xsd",
            )
            _write_minimal_xsd(schema_path, ns)

            parser = TaxonomyParser(HttpCache(cache_dir))
            # Ensure we are exercising cache fallback, not static map lookup.
            self.assertNotIn(ns, parser.global_ns_map)

            # First lookup should discover taxonomy from local cache and hydrate map.
            tax_1 = parser.try_taxonomy_from_namespace(ns)
            self.assertEqual(tax_1.namespace, ns)
            self.assertEqual(parser.global_ns_map[ns], schema_path)

            # Trailing slash should normalize to the same namespace key.
            tax_2 = parser.try_taxonomy_from_namespace(ns + "/")
            self.assertEqual(tax_2.namespace, ns)
            self.assertEqual(parser.global_ns_map[ns], schema_path)
            self.assertNotIn(ns + "/", parser.global_ns_map)

    def test_untrusted_host_is_not_scanned(self):
        # Same shape as above but on a host not present in trusted_hosts.
        # Fallback must refuse scanning this host, even if a matching XSD exists.
        ns = "http://example.invalid/unit-test-tax/2099"
        with tempfile.TemporaryDirectory(prefix="xbrl_cache_") as cache_dir:
            schema_path = os.path.join(
                cache_dir,
                "example.invalid",
                "unit-test-tax",
                "2099",
                "unit-test-tax-2099.xsd",
            )
            _write_minimal_xsd(schema_path, ns)

            parser = TaxonomyParser(HttpCache(cache_dir))
            self.assertNotIn("example.invalid", parser.trusted_hosts)

            # Internal cache lookup should not return a schema for untrusted domains.
            self.assertIsNone(parser._find_cached_schema_path_for_namespace(ns))
            self.assertNotIn("example.invalid", parser._cache_host_ns_index)

            # Public API should still fail with TaxonomyNotFound.
            with self.assertRaises(TaxonomyNotFound):
                parser.try_taxonomy_from_namespace(ns)


if __name__ == "__main__":
    unittest.main()
