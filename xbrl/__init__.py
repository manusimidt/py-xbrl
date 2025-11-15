"""xbrl_parser - Parser for parsing XBRL and iXBRL files (instance documents, taxonomy schemas, taxonomy linkbases)."""

"""
This package contains all classes and methods for parsing both XBRL and iXBRL
The Basics of XBRL are: Concepts, Taxonomies, Values, Contexts, Facts, Instances and Dimension's

Concepts:
A Concept is the definition of a defined term in a particular domain. For example the concept profit should be displayed
as “loss” when there were more expenses than income.

Taxonomies:
A Taxonomy is a collection of related concepts

Value:
A value is a numeric, boolean or text information.

Context:
A context defines a reference point.

Fact:
A Fact is a combination of a concept from a taxonomy, with a value and a context.
For example value 1.5 with the concept EarningsPerShare from the taxonomy us-gaap/2018 and the context From 2018-12-31
to 2019-03-31 is a Fact.

Instance:
A instance is a collection of a facts. New instance documents are created for every new period.

Dimensions:
Some companies use dimensions to differentiate facts with the same context. For example if you want to show revenue over
the same time frame but for different continents.
"""


class XbrlParseException(Exception):
    """
    Generic Class representing a exception occurred while parsing xbrl
    """
    pass


class LinkbaseNotFoundException(XbrlParseException):
    """ Generic exception for imported linkbases that could not be fetched locally or remote """
    pass


class TaxonomyParseException(XbrlParseException):
    """
    Generic class for a exception thrown while parsing a taxonomy
    """
    pass


class TaxonomyNotFound(TaxonomyParseException):
    """
    Raised when the corresponding taxonomy from a namespace was not found.
    i.e the filer used the tag dei:DocumentEntityInformation but did not import the dei taxonomy in the schema file
    """

    def __init__(self, namespace) -> None:
        super().__init__(
            "The taxonomy with namespace {} could not be found. Please check if it is imported in the schema file".format(
                namespace))


class InstanceParseException(XbrlParseException):
    """
    Generic class for an exception thrown while parsing an xbrl instance file
    """
    pass


class ContextParseException(InstanceParseException):
    """
    Exception thrown when a Context could not be parsed
    """
    pass


__version__ = '2.2.17'
__author__ = 'Manuel Schmidt <hello@schmidt-manuel.de>'
__all__ = [
    XbrlParseException,
    TaxonomyParseException,
    TaxonomyNotFound,
    InstanceParseException,
    ContextParseException,
]
