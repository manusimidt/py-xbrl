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

from xbrl.helper.transformation import transform_ixt, transform_ixt_sec
from xbrl.transformations import normalize

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

testTransforms = {
    "http://www.xbrl.org/inlineXBRL/transformation/2015-02-26": [
        # [format,value,expected]
        ['booleanfalse', 'no', 'false'],
        ['booleantrue', 'yeah', 'true'],

        ['datedaymonth', '2.12', '--12-02'],
        ['datedaymonthen', '2. December', '--12-02'],
        ['datedaymonthyear', '2.12.2021', '2021-12-02'],
        ['datedaymonthyearen', '02. December 2021', '2021-12-02'],
        ['datemonthday', '1.2', '--01-02'],
        ['datemonthdayen', 'Jan 02', '--01-02'],
        ['datemonthdayyear', '12-30-2021', '2021-12-30'],
        ['datemonthdayyearen', 'March 31, 2021', '2021-03-31'],
        ['dateyearmonthday', '2021.12.31', '2021-12-31'],

        ['datemonthyear', '12 2021', '2021-12'],
        ['datemonthyearen', 'December 2021', '2021-12'],
        ['dateyearmonthen', '2021 December', '2021-12'],

        ['nocontent', 'Bla bla', ''],
        ['numcommadecimal', '1.499,99', '1499.99'],
        ['numdotdecimal', '1,499.99', '1499.99'],

        ['zerodash', '-', '0'],
    ],
    "http://www.xbrl.org/inlineXBRL/transformation/2020-02-12": [
        # [format,value,expected]
    ],
    "http://www.sec.gov/inlineXBRL/transformation/2015-08-31": [
        # [format,value,expected]
        ['numwordsen', 'no', '0'],
        ['numwordsen', 'None', '0'],
        ['numwordsen', 'nineteen hundred forty-four', '1944'],
        ['numwordsen', 'Seventy Thousand and one', '70001'],
        ['boolballotbox', '☐', 'false'],
        ['boolballotbox', '☑', 'true'],
        ['boolballotbox', '☒', 'true'],
        ['durwordsen', 'Five years, two months', 'P5Y2M0D'],
        ['durwordsen', '9 years, 2 months', 'P9Y2M0D'],
        ['durwordsen', '12 days', 'P0Y0M12D']
    ]
}


class TransformationTest(unittest.TestCase):

    def test_normalize(self):
        """
        :return:
        """
        for namespace in testTransforms:
            for i, testCase in enumerate(testTransforms[namespace]):
                formatCode, testInput, expected = testCase
                testOutput = normalize(namespace, formatCode, testInput)
                self.assertEqual(expected, testOutput, msg=f'Failed at test elem {i}')


if __name__ == '__main__':
    unittest.main()
