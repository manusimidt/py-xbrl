Usage
=====

Installation
------------

To use py-xbrl, first install it using pip:

.. code-block:: console

   $ pip install py-xbrl


Caching
-------
Each instance document imports a Taxonomy. These Taxonomies can also inherit other taxonomies.
When `py-xbrl` parses an instance document it will automatically download all imported and
inherited taxonomies. This can lead to many files being downloaded! Submissions from the same
datasource usually use the same taxonomies. Therefore `py-xbrl` utilizes an HttpCache. **You must
specify a cache location** where all the xml files are stored before parsing them. Downloading and
parsing is automatically done by `py-xbrl` but cleaning the cache not.



.. code-block:: python

    from cache import HttpCache
    cache: HttpCache = HttpCache('./cache')



Locally vs Online
-----------------
`py-xbrl` is able to both parse both locally stored xbrl submissions
and xbrl submissions stored on a server. However if the submission
comes with a taxonomy extension it must be at the same location as
the instance file!

    Example:
    If you download the instance document `aapl-20210925.htm` from
    SEC EDGAR and parse it locally you must also download the
    taxonomy extension `aapl-20210925.xsd` and the linkbases
    `aapl-20210925_lab.xml` `aapl-20210925_pre.xml`. If you parse the
    submission online by just providing the link (https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm)
    `py-xbrl` will automatically download the taxonomy extension schema
    and the linkbases.
