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


Online
------
Here is an example how to parse an XBRL Instance Document
directly from SEC EDGAR. Please set the HTTP headers to your
email as it is required by the SEC!


.. code-block:: python

    import logging
    from xbrl.cache import HttpCache
    from xbrl.instance import XbrlParser, XbrlInstance

    logging.basicConfig(level=logging.INFO)

    cache: HttpCache = HttpCache('./cache')
    cache.set_headers({'From': 'YOUR.NAME@COMPANY.com', 'User-Agent': 'py-xbrl/2.1.1'})
    parser = XbrlParser(cache)

    schema_url = "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm"
    inst: XbrlInstance = parser.parse_instance(schema_url)
    print(inst)

Locally
-------
When parsing locally it is really important that you have all
submission files stored locally, not only the Instance Document.
Submissions (10-K, 10-Q) from SEC EDGAR for example come with
their own taxonomy extension. To parse the following example your
folder would need to contain the following files:

::

    aapl-20210925
    ├── aapl-20210925.htm
    ├── aapl-20210925.xsd
    ├── aapl-20210925_cal.xml
    ├── aapl-20210925_def.xml
    ├── aapl-20210925_lab.xml
    └── aapl-20210925_pre.xml

If you have all submission files stored locally in the same folder
you can parse the submission py providing py-xbrl with the path
to the instance document.

.. code-block:: python

    import logging
    from xbrl.cache import HttpCache
    from xbrl.instance import XbrlParser, XbrlInstance

    logging.basicConfig(level=logging.INFO)

    cache: HttpCache = HttpCache('./cache')
    parser = XbrlParser(cache)

    schema_path = "./cache/aapl-20210925/aapl-20210925.htm"
    inst: XbrlInstance = parser.parse_instance_locally(schema_path)
    print(inst)



