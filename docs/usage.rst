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
When `py-xbrl` parses an instance document it will **automatically download** all imported and
inherited taxonomies. This can lead to many files being downloaded! Submissions from the same
datasource usually use the same taxonomies. Therefore `py-xbrl` utilizes an HttpCache. **You must
specify a cache location** where all the xml files are stored before parsing them. Downloading and
parsing is automatically done by `py-xbrl` but cleaning the cache not.



.. code-block:: python

    from cache import HttpCache
    cache: HttpCache = HttpCache('./cache')


Online
-------
Parsing submissions stored on a webserver is pretty easy. Just provide `py-xbrl` with the url
and `py-xbrl` will download all necessary files for you and store them into the cache.
Make sure to set the http headers correctly (Services like SEC EDGAR require it!).

.. code-block:: python

    import logging
    from xbrl.cache import HttpCache
    from xbrl.instance import XbrlParser, XbrlInstance
    # just to see which files are downloaded
    logging.basicConfig(level=logging.INFO)

    cache: HttpCache = HttpCache('./cache')
    cache.set_headers({'From': 'YOUR@EMAIL.com', 'User-Agent': 'py-xbrl/2.1.0'})
    parser = XbrlParser(cache)

    schema_url = "https://www.sec.gov/Archives/edgar/data/0000320193/000032019321000105/aapl-20210925.htm"
    inst: XbrlInstance = parser.parse_instance(schema_url)


Offline
-------------------------------------------------
If you want to parse submissions directly from your hard drive it is important you make sure
you also download any supporting xml-files! Often the instance file will reference them
by relative imports. If you parse a locally saved file, `py-xbrl` will search for this file
relative to the current directory where the instance document is stored. Alternatively you
can set the `instance_url` parameter.

    Example:
    If you download the instance document `aapl-20210925.htm` from
    SEC EDGAR and want to parse it locally you must also download the
    taxonomy extension `aapl-20210925.xsd` and the linkbases.
    Your folder structure should then look like the following:

    ::

        aapl-20210925
        ├── aapl-20210925.htm
        ├── aapl-20210925.xsd
        ├── aapl-20210925_cal.xml
        ├── aapl-20210925_def.xml
        ├── aapl-20210925_lab.xml
        └── aapl-20210925_pre.xml


.. code-block:: python

    import logging
    from xbrl.cache import HttpCache
    from xbrl.instance import XbrlParser, XbrlInstance
    # just to see which files are downloaded
    logging.basicConfig(level=logging.INFO)

    cache: HttpCache = HttpCache('./cache')
    parser = XbrlParser(cache)

    schema_path = "./cache/aapl-20210925/aapl-20210925.html"
    inst: XbrlInstance = parser.parse_instance(schema_path)

Json
----

You can convert the XBRL report directly to json by calling `.json()` on the `XbrlInstance`.
The json representation follows the
`2021 recommendation from XBRL international <https://www.xbrl.org/Specification/xbrl-json/REC-2021-10-13/xbrl-json-REC-2021-10-13.html>`_.


.. code-block:: python

   # print json to console
   print(inst.json())

   # save to file
   inst.json('./test.json')
