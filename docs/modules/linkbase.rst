linkbase
========

Linkbases are individual XML files that bring structure to concepts
and link them to additional information. This information can be,
for example, user-friendly labels or references to authoritative
literature. The linkbases are imported in the taxonomy schema.
Linkbases can be divided into two main groups: Relation Linkbases
and Reference Linkbases. Relation Linkbases create hierarchical
relationships between multiple concepts. The interpretation of these
hierarchical relationships is defined by the type of linkbase.
Reference linkbases, on the other hand, add resources to concepts.

**Relation Linkbases:**

    **Calculation Linkbase:** The Calculation Linkbase defines simple
    arithmetic relationships between individual concepts. If the above example
    were a calculation linkbase, it would define the following equation:
    us-gaap_Assets = us-gaap_AssetsCurrent + us-gaap_AssetsNonCurrent.

    **Presentation Linkbase:** The presentation linkbase describes the order
    in which the concepts of the taxonomy should be arranged. The above
    example would subordinate the us-gaap_AssetsCurrent and
    us-gaap_AssetsNonCurrent concepts to the us-gaap_Assets concept.

    **Definition Linkbase:** The definition linkbase allows to create various
    other logical connections between concepts. For example, a link
    with the arcrole “essence-alias” can be used to emphasize that
    two concepts cover the same or very similar subject matter.

**Reference Linkbases:**

    **Label Linkbase:** The Label Linkbase links concepts with one or more
    reader-friendly labels. It is also possible to link labels in
    different languages.

    **Reference Linkbase:** The reference linkbase can be used to create
    links between concepts and documents outside of XBRL/XML.
    Most often, these external documents are laws or policies
    that govern the calculation, disclosure, or presentation
    of these concepts.




read more at: https://manusimidt.dev/2021-07/xbrl-explained

Parse functions
---------------

.. automodule:: xbrl.linkbase


    .. automethod:: xbrl.linkbase.parse_linkbase_url
    .. automethod:: xbrl.linkbase.parse_linkbase


Class
----------

.. autoclass:: xbrl.linkbase::Linkbase
    :members:

    .. automethod:: __init__