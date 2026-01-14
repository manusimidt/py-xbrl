taxonomy
========
Since there is a large number of financial information with different
accounting systems (us-gaap, ifrs…), a common language framework must
be established prior to the data transfer. In the XBRL context, this
common language framework is called a Taxonomy. The taxonomy defines
a list of concepts that can then be used in the instance document to
tag certain numbers and ensures the integrity and syntactic correctness
of the data.
The taxonomy schema is the heart of the taxonomy and defines the
concepts of the taxonomy. The concepts will later be used by the
creator of a financial report to tag certain numbers.
A Taxonomy schema defines the reportable concepts and links the
linkbases to describe the relationships between the concepts.
Taxonomy schemas can import multiple different taxonomy schemas.

The current Taxonomy Schema can override the extended schemas in the following way:

1. Addition of new concepts:
New concepts are added in this TaxonomySchema to extend the concepts declared in the base Taxonomy schemas

2. Addition of resources:
The Label Linkbase of this taxonomy can add new labels to existing concepts from the base taxonomy

3. Overriding of relationships:
All Linkbases of this taxonomy can override i.e the order of concepts in a definition linkbase

4. Overriding of resources:
The Label Linkbase of this taxonomy can override the labels of the base taxonomy!

read more at: https://manusimidt.dev/2021-07/xbrl-explained


Parser Class
---------------
.. autoclass:: xbrl.instance::XbrlInstance
    :members:
    :inherited-members:

    .. automethod:: __init__


Parse functions
---------------

.. automodule:: xbrl.taxonomy


    .. automethod:: xbrl.taxonomy.parse_taxonomy_url
    .. automethod:: xbrl.taxonomy.parse_taxonomy

Other Classes
--------------

.. autoclass:: xbrl.taxonomy::Concept
    :members:

    .. automethod:: __init__

.. autoclass:: xbrl.taxonomy::TaxonomySchema
    :members:

    .. automethod:: __init__
