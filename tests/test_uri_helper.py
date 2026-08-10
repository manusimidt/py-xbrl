"""
This unit test tests the uri resolver.
It is often the case, that a taxonomy schema imports another taxonomy using a relative path.
i.e:
<link:linkbaseRef [..] xlink:href="./../example_lab.xml" [..]/>
The job of the uri resolver is to resolve those relative paths and urls and return an absolute path or url
"""

import logging
import sys
import unittest
import os
from xbrl.helper.uri_helper import resolve_uri, compare_uri

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class UriResolverTest(unittest.TestCase):
    def test_resolve_uri(self):
        """
        :return:
        """

        test_arr = [
            # test paths
            (
                ("D:\\path\\to\\some\\folder\\example.xsd", "/example-lab.xml"),
                os.sep.join(["D:", "path", "to", "some", "folder", "example-lab.xml"]),
            ),
            (
                (r"D:\path\to\xbrl_parser\some\folder\example.xsd", "/example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "some", "folder", "example-lab.xml"]),
            ),
            (
                ("D:/path/to/xbrl_parser/some/folder/example.xsd", "/example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "some", "folder", "example-lab.xml"]),
            ),
            # test different path separators
            (
                ("D:\\path\\to\\xbrl_parser\\some\\folder/example.xsd", "/example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "some", "folder", "example-lab.xml"]),
            ),
            # test directory traversal
            (
                ("D:/path/to/xbrl_parser/some/folder/", "/../example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "some", "example-lab.xml"]),
            ),
            (
                ("D:/path/to/xbrl_parser/some/folder", "./../example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "some", "example-lab.xml"]),
            ),
            (
                ("D:/path/to/xbrl_parser/some/folder/example.xsd", "../../example-lab.xml"),
                os.sep.join(["D:", "path", "to", "xbrl_parser", "example-lab.xml"]),
            ),
            # test urls
            (("http://example.com/a/b/c/d/e/f/g", "file.xml"), "http://example.com/a/b/c/d/e/f/g/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "/file.xml"), "http://example.com/a/b/c/d/e/f/g/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "./file.xml"), "http://example.com/a/b/c/d/e/f/g/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "../file.xml"), "http://example.com/a/b/c/d/e/f/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "/../file.xml"), "http://example.com/a/b/c/d/e/f/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "./../file.xml"), "http://example.com/a/b/c/d/e/f/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "../../file.xml"), "http://example.com/a/b/c/d/e/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "/../../file.xml"), "http://example.com/a/b/c/d/e/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g", "./../../file.xml"), "http://example.com/a/b/c/d/e/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g/", "../../../file.xml"), "http://example.com/a/b/c/d/file.xml"),
            (("http://example.com/a/b/c/d/e/f/g.xml", "../../../file.xml"), "http://example.com/a/b/c/file.xml"),
        ]
        for i, elem in enumerate(test_arr):
            # only windows uses the \\ file path separator
            # for now skip the first tests with \\ if we are on a unix system, since the \\ is an invalid path on
            # a unix like os such as macOS or linux
            if elem[0][0].startswith("D:\\") and os.sep != "\\":
                logging.info("Skipping Windows specific unit test case")
                continue
            expected = elem[1]
            received = resolve_uri(elem[0][0], elem[0][1])
            self.assertEqual(expected, received, msg=f"Failed at test elem {i}")

    def test_compare_uri(self):
        test_arr: list[tuple[str, str, bool]] = [
            ("./abc", "abc", True),
            ("./abc", "\\abc\\", True),
            ("./abc", "abcd", False),
            ("http://abc.de", "https://abc.de", True),
        ]
        for i, test_case in enumerate(test_arr):
            expected = test_case[2]
            received = compare_uri(test_case[0], test_case[1])
            self.assertEqual(expected, received, msg=f"Failed at test elem {i}")


if __name__ == "__main__":
    unittest.main()
