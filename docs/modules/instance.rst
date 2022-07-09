instance
========

The Instance Document uses the concepts created in the taxonomy to tag the
numbers to be reported, giving them meaning and structure.
Thus, the instance document embodies the actual business report, for example,
the annual financial statement.

There are two different types of instance documents:
the classic XBRL instance document (XML) and the iXBRL instance document (HTML).
Both types are based on the same elements but are written in different file types.

The core elements of every Instance document are the Facts. A **fact** is a
number (150000) combined with a **context** (from Jan-Dec 2020 for company xyz),
a **unit** (USD) and tagged with a **concept** from the taxonomy (us-gaap_Revenue).
The Context defines the time frame and the company to which the fact belongs.


Parse functions
---------------

.. automodule:: xbrl.instance

    .. automethod:: xbrl.instance.parse_xbrl_url
    .. automethod:: xbrl.instance.parse_xbrl
    .. automethod:: xbrl.instance.parse_ixbrl_url
    .. automethod:: xbrl.instance.parse_ixbrl

Classes
--------------

.. autoclass:: xbrl.instance::XbrlParser
    :members:
    :inherited-members:

    .. automethod:: __init__


.. autoclass:: xbrl.instance::XbrlInstance
    :members:
    :inherited-members:

    .. automethod:: __init__

