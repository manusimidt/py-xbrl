cache
=====

This class handles a simple disk cache. It will download requested files and store them in folder specified by
the user. If the file is requested a second time this class will serve the file directly from the file system.
The path for caching is created out of the url of the file.
For example, the file with the URL
"https://www.sec.gov/Archives/edgar/data/320193/000032019318000100/aapl-20180630.xml"
will be stored in the disk cache in
„D:/cache/www.sec.gov/Archives/edgar/data/320193/000032019318000100/aapl-20180630.xml“
where "D:/cache" is the caching directory specified by the user.

The http cache can also delay requests. This is highly recommended if you download xbrl submissions in batch!
This class also provides a function for that :meth:`xbrl.cache.HttpCache.cache_edgar_enclosure`.

The SEC also emphasizes that you should try to keep the required server load on the EDGAR system as small as possible!
https://www.sec.gov/privacy.htm#security


Short note on enclosures:
-------------------------
The SEC provides zip folders that contain all xbrl related files for a given submission.
These files are i.e: Instance Document, Extension Taxonomy, Linkbases.
Due to the fact that the zip compression is very effective on xbrl submissions that naturally contain
repeating test, it is way more efficient to download the zip folder and extract it.
So if you want to do the SEC servers and your downloading time a favour, use this method for downloading
the submission :).
One way to get the zip enclosure url is through the Structured Disclosure RSS Feeds provided by the SEC:
https://www.sec.gov/structureddata/rss-feeds-submitted-filings


Parameters
----------

.. autoclass:: xbrl.cache::HttpCache
    :members:
    :inherited-members:

    .. automethod:: __init__

