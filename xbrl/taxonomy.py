"""
This module contains all classes and functions necessary for parsing Taxonomy schema files.
"""
import logging
import os
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import List
from urllib.parse import unquote

from xbrl import XbrlParseException, TaxonomyNotFound
from xbrl.cache import HttpCache
from xbrl.helper.uri_helper import resolve_uri, compare_uri, is_url
from xbrl.linkbase import Linkbase, ExtendedLink, LinkbaseType, parse_linkbase, parse_linkbase_url, Label

logger = logging.getLogger(__name__)

LINK_NS: str = "{http://www.xbrl.org/2003/linkbase}"
XLINK_NS: str = "{http://www.w3.org/1999/xlink}"
XDS_NS: str = "{http://www.w3.org/2001/XMLSchema}"
XBRLI_NS: str = "{http://www.xbrl.org/2003/instance}"

# dictionary containing all common prefixes and the corresponding namespaces.
NAME_SPACES: dict = {
    "xsd": "http://www.w3.org/2001/XMLSchema",
    "link": "http://www.xbrl.org/2003/linkbase",
    "xlink": "http://www.w3.org/1999/xlink",
    "xbrldt": "http://xbrl.org/2005/xbrldt"
}

ns_schema_map: dict = {
    "http://arelle.org/doc/2014-01-31": "http://arelle.org/2014/doc-2014-01-31.xsd",
    "http://fasb.org/dis/cecltmp01/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-cecltmp01-2019-01-31.xsd",
    "http://fasb.org/dis/cecltmp02/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-cecltmp02-2019-01-31.xsd",
    "http://fasb.org/dis/cecltmp03/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-cecltmp03-2019-01-31.xsd",
    "http://fasb.org/dis/cecltmp04/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-cecltmp04-2019-01-31.xsd",
    "http://fasb.org/dis/cecltmp05/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-cecltmp05-2019-01-31.xsd",
    "http://fasb.org/dis/fifvdtmp01/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-fifvdtmp01-2018-01-31.xsd",
    "http://fasb.org/dis/fifvdtmp01/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-fifvdtmp01-2019-01-31.xsd",
    "http://fasb.org/dis/fifvdtmp02/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-fifvdtmp02-2018-01-31.xsd",
    "http://fasb.org/dis/fifvdtmp02/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-fifvdtmp02-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp011/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp011-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp011/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp011-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp012/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp012-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp012/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp012-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp021/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp021-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp021/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp021-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp022/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp022-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp022/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp022-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp03/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp03-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp03/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp03-2019-01-31.xsd",
    "http://fasb.org/dis/idestmp04/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-idestmp04-2018-01-31.xsd",
    "http://fasb.org/dis/idestmp04/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-idestmp04-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp01/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp01-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp021/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp021-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp022/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp022-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp023/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp023-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp024/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp024-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp025/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp025-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp031/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp031-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp032/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp032-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp033/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp033-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp041/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp041-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp042/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp042-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp051/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp051-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp052/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp052-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp061/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp061-2019-01-31.xsd",
    "http://fasb.org/dis/insldtmp062/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-insldtmp062-2019-01-31.xsd",
    "http://fasb.org/dis/leasestmp01/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-leasestmp01-2017-01-31.xsd",
    "http://fasb.org/dis/leasestmp02/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-leasestmp02-2017-01-31.xsd",
    "http://fasb.org/dis/leasestmp03/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-leasestmp03-2017-01-31.xsd",
    "http://fasb.org/dis/leasestmp04/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-leasestmp04-2017-01-31.xsd",
    "http://fasb.org/dis/leasestmp05/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-leasestmp05-2017-01-31.xsd",
    "http://fasb.org/dis/leastmp01/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-leastmp01-2018-01-31.xsd",
    "http://fasb.org/dis/leastmp01/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-leastmp01-2019-01-31.xsd",
    "http://fasb.org/dis/leastmp02/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-leastmp02-2018-01-31.xsd",
    "http://fasb.org/dis/leastmp02/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-leastmp02-2019-01-31.xsd",
    "http://fasb.org/dis/leastmp03/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-leastmp03-2018-01-31.xsd",
    "http://fasb.org/dis/leastmp03/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-leastmp03-2019-01-31.xsd",
    "http://fasb.org/dis/leastmp04/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-leastmp04-2018-01-31.xsd",
    "http://fasb.org/dis/leastmp04/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-leastmp04-2019-01-31.xsd",
    "http://fasb.org/dis/leastmp05/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-leastmp05-2018-01-31.xsd",
    "http://fasb.org/dis/leastmp05/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-leastmp05-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp011/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp011-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp011/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp011-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp011/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp011-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp012/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp012-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp012/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp012-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp012/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp012-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp02/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp02-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp02/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp02-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp02/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp02-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp03/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp03-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp03/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp03-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp03/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp03-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp04/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp04-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp04/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp04-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp04/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp04-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp041/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp041-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp041/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp041-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp041/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp041-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp05/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp05-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp05/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp05-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp05/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp05-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp06/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp06-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp06/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp06-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp06/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp06-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp07/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp07-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp07/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp07-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp07/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp07-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp08/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp08-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp08/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp08-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp08/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp08-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp09/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp09-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp09/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp09-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp09/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp09-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp102/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp102-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp102/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp102-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp102/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp102-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp103/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp103-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp103/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp103-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp103/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp103-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp104/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp104-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp104/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp104-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp104/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp104-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp105/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp105-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp105/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp105-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp105/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp105-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp111/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp111-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp111/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp111-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp111/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp111-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp112/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp112-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp112/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp112-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp112/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp112-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp121/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp121-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp121/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp121-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp121/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp121-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp122/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp122-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp122/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp122-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp122/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp122-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp123/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp123-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp123/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp123-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp123/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp123-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp125/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp125-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp125/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp125-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp125/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp125-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp131/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp131-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp131/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp131-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp131/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp131-2019-01-31.xsd",
    "http://fasb.org/dis/rbtmp141/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rbtmp141-2017-01-31.xsd",
    "http://fasb.org/dis/rbtmp141/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rbtmp141-2018-01-31.xsd",
    "http://fasb.org/dis/rbtmp141/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rbtmp141-2019-01-31.xsd",
    "http://fasb.org/dis/rcctmp01/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rcctmp01-2017-01-31.xsd",
    "http://fasb.org/dis/rcctmp01/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rcctmp01-2018-01-31.xsd",
    "http://fasb.org/dis/rcctmp01/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rcctmp01-2019-01-31.xsd",
    "http://fasb.org/dis/rcctmp03/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rcctmp03-2017-01-31.xsd",
    "http://fasb.org/dis/rcctmp03/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rcctmp03-2018-01-31.xsd",
    "http://fasb.org/dis/rcctmp03/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rcctmp03-2019-01-31.xsd",
    "http://fasb.org/dis/rcctmp04/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rcctmp04-2017-01-31.xsd",
    "http://fasb.org/dis/rcctmp04/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rcctmp04-2018-01-31.xsd",
    "http://fasb.org/dis/rcctmp04/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rcctmp04-2019-01-31.xsd",
    "http://fasb.org/dis/rcctmp05/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/dis/us-gaap-dis-rcctmp05-2017-01-31.xsd",
    "http://fasb.org/dis/rcctmp05/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/dis/us-gaap-dis-rcctmp05-2018-01-31.xsd",
    "http://fasb.org/dis/rcctmp05/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/dis/us-gaap-dis-rcctmp05-2019-01-31.xsd",
    "http://fasb.org/srt/2018-01-31": "http://xbrl.fasb.org/srt/2018/elts/srt-2018-01-31.xsd",
    "http://fasb.org/srt/2019-01-31": "http://xbrl.fasb.org/srt/2019/elts/srt-2019-01-31.xsd",
    "http://fasb.org/srt/2020-01-31": "http://xbrl.fasb.org/srt/2020/elts/srt-2020-01-31.xsd",
    "http://fasb.org/srt/2021-01-31": "http://xbrl.fasb.org/srt/2021/elts/srt-2021-01-31.xsd",
    "http://fasb.org/srt/2022": "https://xbrl.fasb.org/srt/2022/elts/srt-2022.xsd",
    "http://fasb.org/srt/2023": "https://xbrl.fasb.org/srt/2023/elts/srt-2023.xsd",
    "http://fasb.org/srt-roles/2018-01-31": "http://xbrl.fasb.org/srt/2018/elts/srt-roles-2018-01-31.xsd",
    "http://fasb.org/srt-roles/2019-01-31": "http://xbrl.fasb.org/srt/2019/elts/srt-roles-2019-01-31.xsd",
    "http://fasb.org/srt-roles/2020-01-31": "http://xbrl.fasb.org/srt/2020/elts/srt-roles-2020-01-31.xsd",
    "http://fasb.org/srt-roles/2021-01-31": "http://xbrl.fasb.org/srt/2021/elts/srt-roles-2021-01-31.xsd",
    "http://fasb.org/srt-types/2018-01-31": "http://xbrl.fasb.org/srt/2018/elts/srt-types-2018-01-31.xsd",
    "http://fasb.org/srt-types/2019-01-31": "http://xbrl.fasb.org/srt/2019/elts/srt-types-2019-01-31.xsd",
    "http://fasb.org/srt-types/2020-01-31": "http://xbrl.fasb.org/srt/2020/elts/srt-types-2020-01-31.xsd",
    "http://fasb.org/srt-types/2021-01-31": "http://xbrl.fasb.org/srt/2021/elts/srt-types-2021-01-31.xsd",
    "http://fasb.org/us-gaap/2011-01-31": "http://xbrl.fasb.org/us-gaap/2011/elts/us-gaap-2011-01-31.xsd",
    "http://fasb.org/us-gaap/2012-01-31": "http://xbrl.fasb.org/us-gaap/2012/elts/us-gaap-2012-01-31.xsd",
    "http://fasb.org/us-gaap/2013-01-31": "http://xbrl.fasb.org/us-gaap/2013/elts/us-gaap-2013-01-31.xsd",
    "http://fasb.org/us-gaap/2014-01-31": "http://xbrl.fasb.org/us-gaap/2014/elts/us-gaap-2014-01-31.xsd",
    "http://fasb.org/us-gaap/2015-01-31": "http://xbrl.fasb.org/us-gaap/2015/elts/us-gaap-2015-01-31.xsd",
    "http://fasb.org/us-gaap/2016-01-31": "http://xbrl.fasb.org/us-gaap/2016/elts/us-gaap-2016-01-31.xsd",
    "http://fasb.org/us-gaap/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/elts/us-gaap-2017-01-31.xsd",
    "http://fasb.org/us-gaap/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/elts/us-gaap-2018-01-31.xsd",
    "http://fasb.org/us-gaap/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/elts/us-gaap-2019-01-31.xsd",
    "http://fasb.org/us-gaap/2020-01-31": "http://xbrl.fasb.org/us-gaap/2020/elts/us-gaap-2020-01-31.xsd",
    "http://fasb.org/us-gaap/2021-01-31": "http://xbrl.fasb.org/us-gaap/2021/elts/us-gaap-2021-01-31.xsd",
    "http://fasb.org/us-gaap/2022-01-31": "https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-2022.xsd",
    "http://fasb.org/us-gaap/2022": "https://xbrl.fasb.org/us-gaap/2022/elts/us-gaap-2022.xsd",
    "http://fasb.org/us-gaap/2023": "https://xbrl.fasb.org/us-gaap/2023/elts/us-gaap-2023.xsd",
    "http://fasb.org/us-roles/2011-01-31": "http://xbrl.fasb.org/us-gaap/2011/elts/us-roles-2011-01-31.xsd",
    "http://fasb.org/us-roles/2012-01-31": "http://xbrl.fasb.org/us-gaap/2012/elts/us-roles-2012-01-31.xsd",
    "http://fasb.org/us-roles/2013-01-31": "http://xbrl.fasb.org/us-gaap/2013/elts/us-roles-2013-01-31.xsd",
    "http://fasb.org/us-roles/2014-01-31": "http://xbrl.fasb.org/us-gaap/2014/elts/us-roles-2014-01-31.xsd",
    "http://fasb.org/us-roles/2015-01-31": "http://xbrl.fasb.org/us-gaap/2015/elts/us-roles-2015-01-31.xsd",
    "http://fasb.org/us-roles/2016-01-31": "http://xbrl.fasb.org/us-gaap/2016/elts/us-roles-2016-01-31.xsd",
    "http://fasb.org/us-roles/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/elts/us-roles-2017-01-31.xsd",
    "http://fasb.org/us-roles/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/elts/us-roles-2018-01-31.xsd",
    "http://fasb.org/us-roles/2019-01-31": "http://xbrl.fasb.org/us-gaap/2019/elts/us-roles-2019-01-31.xsd",
    "http://fasb.org/us-roles/2020-01-31": "http://xbrl.fasb.org/us-gaap/2020/elts/us-roles-2020-01-31.xsd",
    "http://fasb.org/us-roles/2021-01-31": "http://xbrl.fasb.org/us-gaap/2021/elts/us-roles-2021-01-31.xsd",
    "http://fasb.org/us-types/2011-01-31": "http://xbrl.fasb.org/us-gaap/2011/elts/us-types-2011-01-31.xsd",
    "http://fasb.org/us-types/2012-01-31": "http://xbrl.fasb.org/us-gaap/2012/elts/us-types-2012-01-31.xsd",
    "http://fasb.org/us-types/2013-01-31": "http://xbrl.fasb.org/us-gaap/2013/elts/us-types-2013-01-31.xsd",
    "http://fasb.org/us-types/2014-01-31": "http://xbrl.fasb.org/us-gaap/2014/elts/us-types-2014-01-31.xsd",
    "http://fasb.org/us-types/2015-01-31": "http://xbrl.fasb.org/us-gaap/2015/elts/us-types-2015-01-31.xsd",
    "http://fasb.org/us-types/2016-01-31": "http://xbrl.fasb.org/us-gaap/2016/elts/us-types-2016-01-31.xsd",
    "http://fasb.org/us-types/2017-01-31": "http://xbrl.fasb.org/us-gaap/2017/elts/us-types-2017-01-31.xsd",
    "http://fasb.org/us-types/2018-01-31": "http://xbrl.fasb.org/us-gaap/2018/elts/us-types-2018-01-31.xsd",
    "http://fasb.org/us-types/2019-01-31": "http://xbrl.fasb.org/us-gaap/2020/elts/us-types-2020-01-31.xsd",
    "http://fasb.org/us-types/2021-01-31": "http://xbrl.fasb.org/us-gaap/2021/elts/us-types-2021-01-31.xsd",
    "http://ici.org/rr/2006": "http://xbrl.ici.org/rr/2006/ici-rr.xsd",
    "http://www.esma.europa.eu/xbrl/esef/arcrole/wider-narrower": "http://www.xbrl.org/lrr/arcrole/esma-arcrole-2018-11-21.xsd",
    "http://www.w3.org/1999/xlink": "http://www.xbrl.org/2003/xlink-2003-12-31.xsd",
    "http://www.xbrl.org/2003/instance": "http://www.xbrl.org/2003/xbrl-instance-2003-12-31.xsd",
    "http://www.xbrl.org/2003/linkbase": "http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd",
    "http://www.xbrl.org/2003/XLink": "http://www.xbrl.org/2003/xl-2003-12-31.xsd",
    "http://www.xbrl.org/2004/ref": "http://www.xbrl.org/2004/ref-2004-08-10.xsd",
    "http://www.xbrl.org/2006/ref": "http://www.xbrl.org/2006/ref-2006-02-27.xsd",
    "http://www.xbrl.org/2009/arcrole/deprecated": "http://www.xbrl.org/lrr/arcrole/deprecated-2009-12-16.xsd",
    "http://www.xbrl.org/2009/arcrole/fact-explanatoryFact": "http://www.xbrl.org/lrr/arcrole/factExplanatory-2009-12-16.xsd",
    "http://www.xbrl.org/2009/role/deprecated": "http://www.xbrl.org/lrr/role/deprecated-2009-12-16.xsd",
    "http://www.xbrl.org/2009/role/negated": "http://www.xbrl.org/lrr/role/negated-2009-12-16.xsd",
    "http://www.xbrl.org/2009/role/net": "http://www.xbrl.org/lrr/role/net-2009-12-16.xsd",
    "http://www.xbrl.org/dtr/type/2020-01-21": "http://www.xbrl.org/dtr/type/2020-01-21/types.xsd",
    "http://www.xbrl.org/dtr/type/non-numeric": "http://www.xbrl.org/dtr/type/nonNumeric-2009-12-20.xsd",
    "http://www.xbrl.org/dtr/type/numeric": "http://www.xbrl.org/dtr/type/numeric-2009-12-16.xsd",
    "http://www.xbrl.org/us/fr/common/fste/2005-02-28": "http://www.xbrl.org/us/fr/common/fste/2005-02-28/usfr-fste-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/common/fstr/2005-02-28": "http://www.xbrl.org/us/fr/common/fstr/2005-02-28/usfr-fstr-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/common/ime/2005-06-28": "http://www.xbrl.org/us/fr/common/ime/2005-06-28/usfr-ime-2005-06-28.xsd",
    "http://www.xbrl.org/us/fr/common/pte/2005-02-28": "http://www.xbrl.org/us/fr/common/pte/2005-02-28/usfr-pte-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/common/ptr/2005-02-28": "http://www.xbrl.org/us/fr/common/ptr/2005-02-28/usfr-ptr-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/gaap/basi/2005-02-28": "http://www.xbrl.org/us/fr/gaap/basi/2005-02-28/us-gaap-basi-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/gaap/ci/2005-02-28": "http://www.xbrl.org/us/fr/gaap/ci/2005-02-28/us-gaap-ci-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/gaap/im/2005-06-28": "http://www.xbrl.org/us/fr/gaap/im/2005-06-28/us-gaap-im-2005-06-28.xsd",
    "http://www.xbrl.org/us/fr/gaap/ins/2005-02-28": "http://www.xbrl.org/us/fr/gaap/ins/2005-02-28/us-gaap-ins-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/rpt/ar/2005-02-28": "http://www.xbrl.org/us/fr/rpt/ar/2005-02-28/usfr-ar-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/rpt/mda/2005-02-28": "http://www.xbrl.org/us/fr/rpt/mda/2005-02-28/usfr-mda-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/rpt/mr/2005-02-28": "http://www.xbrl.org/us/fr/rpt/mr/2005-02-28/usfr-mr-2005-02-28.xsd",
    "http://www.xbrl.org/us/fr/rpt/seccert/2005-02-28": "http://www.xbrl.org/us/fr/rpt/seccert/2005-02-28/usfr-seccert-2005-02-28.xsd",
    "http://xbrl.ifrs.org/taxonomy/2013-09-09/ifrs": "http://xbrl.ifrs.org/taxonomy/2013-09-09/ifrs-cor_2013-09-09.xsd",
    "http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2014-03-05/full_ifrs/full_ifrs-cor_2014-03-05.xsd",
    "http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs-smes": "http://xbrl.ifrs.org/taxonomy/2014-03-05/ifrs_for_smes/ifrs_for_smes-cor_2014-03-05.xsd",
    "http://xbrl.ifrs.org/taxonomy/2015-03-11/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2015-03-11/full_ifrs/full_ifrs-cor_2015-03-11.xsd",
    "http://xbrl.ifrs.org/taxonomy/2016-03-31/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2016-03-31/full_ifrs/full_ifrs-cor_2016-03-31.xsd",
    "http://xbrl.ifrs.org/taxonomy/2017-03-09/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2017-03-09/full_ifrs/full_ifrs-cor_2017-03-09.xsd",
    "http://xbrl.ifrs.org/taxonomy/2018-03-16/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2018-03-16/full_ifrs/full_ifrs-cor_2018-03-16.xsd",
    "http://xbrl.ifrs.org/taxonomy/2019-03-27/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2019-03-27/full_ifrs/full_ifrs-cor_2019-03-27.xsd",
    "http://xbrl.ifrs.org/taxonomy/2020-03-16/ifrs-full": "http://xbrl.ifrs.org/taxonomy/2020-03-16/full_ifrs/full_ifrs-cor_2020-03-16.xsd",
    "http://xbrl.org/2005/xbrldt": "http://www.xbrl.org/2005/xbrldt-2005.xsd",
    "http://xbrl.org/2006/xbrldi": "http://www.xbrl.org/2006/xbrldi-2006.xsd",
    "http://xbrl.org/2023/calculation-1.1": "https://www.xbrl.org/2023/calculation-1.1.xsd",
    "http://xbrl.org/2014/extensible-enumerations": "http://www.xbrl.org/2014/extensible-enumerations.xsd",
    "http://xbrl.org/2020/extensible-enumerations-2.0": "http://www.xbrl.org/2020/extensible-enumerations-2.0.xsd",
    "http://xbrl.sec.gov/country/2011-01-31": "https://xbrl.sec.gov/country/2011/country-2011-01-31.xsd",
    "http://xbrl.sec.gov/country/2012-01-31": "https://xbrl.sec.gov/country/2012/country-2012-01-31.xsd",
    "http://xbrl.sec.gov/country/2013-01-31": "https://xbrl.sec.gov/country/2013/country-2013-01-31.xsd",
    "http://xbrl.sec.gov/country/2016-01-31": "https://xbrl.sec.gov/country/2016/country-2016-01-31.xsd",
    "http://xbrl.sec.gov/country/2017-01-31": "https://xbrl.sec.gov/country/2017/country-2017-01-31.xsd",
    "http://xbrl.sec.gov/country/2020-01-31": "https://xbrl.sec.gov/country/2020/country-2020-01-31.xsd",
    "http://xbrl.sec.gov/country/2021": "https://xbrl.sec.gov/country/2021/country-2021.xsd",
    "http://xbrl.sec.gov/currency/2011-01-31": "https://xbrl.sec.gov/currency/2011/currency-2011-01-31.xsd",
    "http://xbrl.sec.gov/currency/2012-01-31": "https://xbrl.sec.gov/currency/2012/currency-2012-01-31.xsd",
    "http://xbrl.sec.gov/currency/2014-01-31": "https://xbrl.sec.gov/currency/2014/currency-2014-01-31.xsd",
    "http://xbrl.sec.gov/currency/2016-01-31": "https://xbrl.sec.gov/currency/2016/currency-2016-01-31.xsd",
    "http://xbrl.sec.gov/currency/2017-01-31": "https://xbrl.sec.gov/currency/2017/currency-2017-01-31.xsd",
    "http://xbrl.sec.gov/currency/2019-01-31": "https://xbrl.sec.gov/currency/2019/currency-2019-01-31.xsd",
    "http://xbrl.sec.gov/currency/2020-01-31": "https://xbrl.sec.gov/currency/2020/currency-2020-01-31.xsd",
    "http://xbrl.sec.gov/currency/2021": "https://xbrl.sec.gov/currency/2021/currency-2021.xsd",
    "http://xbrl.sec.gov/currency/2022": "https://xbrl.sec.gov/currency/2022/currency-2022.xsd",
    "http://xbrl.sec.gov/dei/2011-01-31": "https://xbrl.sec.gov/dei/2011/dei-2011-01-31.xsd",
    "http://xbrl.sec.gov/dei/2012-01-31": "https://xbrl.sec.gov/dei/2012/dei-2012-01-31.xsd",
    "http://xbrl.sec.gov/dei/2013-01-31": "https://xbrl.sec.gov/dei/2013/dei-2013-01-31.xsd",
    "http://xbrl.sec.gov/dei/2014-01-31": "https://xbrl.sec.gov/dei/2014/dei-2014-01-31.xsd",
    "http://xbrl.sec.gov/dei/2018-01-31": "https://xbrl.sec.gov/dei/2018/dei-2018-01-31.xsd",
    "http://xbrl.sec.gov/dei/2019-01-31": "https://xbrl.sec.gov/dei/2019/dei-2019-01-31.xsd",
    "http://xbrl.sec.gov/dei/2020-01-31": "https://xbrl.sec.gov/dei/2020/dei-2020-01-31.xsd",
    "http://xbrl.sec.gov/dei/2021": "https://xbrl.sec.gov/dei/2021/dei-2021.xsd",
    "http://xbrl.sec.gov/dei/2022": "https://xbrl.sec.gov/dei/2022/dei-2022.xsd",
    "http://xbrl.sec.gov/dei/2023": "https://xbrl.sec.gov/dei/2023/dei-2023.xsd",
    "http://xbrl.sec.gov/dei/2021q4": "https://xbrl.sec.gov/dei/2021q4/dei-2021q4.xsd",
    "http://xbrl.sec.gov/dei-def/2021": "https://xbrl.sec.gov/dei/2021/dei-2021_def.xsd",
    "http://xbrl.sec.gov/dei-entire/2021": "https://xbrl.sec.gov/dei/2021/dei-entire-2021.xsd",
    "http://xbrl.sec.gov/dei-ent-std/2019-01-31": "https://xbrl.sec.gov/dei/2019/dei-ent-std-2019-01-31.xsd",
    "http://xbrl.sec.gov/dei-ent-std/2020-01-31": "https://xbrl.sec.gov/dei/2020/dei-ent-std-2020-01-31.xsd",
    "http://xbrl.sec.gov/dei-lab/2021": "https://xbrl.sec.gov/dei/2021/dei-2021_lab.xsd",
    "http://xbrl.sec.gov/dei-pre/2021": "https://xbrl.sec.gov/dei/2021/dei-2021_pre.xsd",
    "http://xbrl.sec.gov/dei-std/2019-01-31": "https://xbrl.sec.gov/dei/2019/dei-std-2019-01-31.xsd",
    "http://xbrl.sec.gov/dei-std/2020-01-31": "https://xbrl.sec.gov/dei/2020/dei-std-2020-01-31.xsd",
    "http://xbrl.sec.gov/exch/2011-01-31": "https://xbrl.sec.gov/exch/2011/exch-2011-01-31.xsd",
    "http://xbrl.sec.gov/exch/2012-01-31": "https://xbrl.sec.gov/exch/2012/exch-2012-01-31.xsd",
    "http://xbrl.sec.gov/exch/2013-01-31": "https://xbrl.sec.gov/exch/2013/exch-2013-01-31.xsd",
    "http://xbrl.sec.gov/exch/2014-01-31": "https://xbrl.sec.gov/exch/2014/exch-2014-01-31.xsd",
    "http://xbrl.sec.gov/exch/2015-01-31": "https://xbrl.sec.gov/exch/2015/exch-2015-01-31.xsd",
    "http://xbrl.sec.gov/exch/2016-01-31": "https://xbrl.sec.gov/exch/2016/exch-2016-01-31.xsd",
    "http://xbrl.sec.gov/exch/2017-01-31": "https://xbrl.sec.gov/exch/2017/exch-2017-01-31.xsd",
    "http://xbrl.sec.gov/exch/2018-01-31": "https://xbrl.sec.gov/exch/2018/exch-2018-01-31.xsd",
    "http://xbrl.sec.gov/exch/2019-01-31": "https://xbrl.sec.gov/exch/2019/exch-2019-01-31.xsd",
    "http://xbrl.sec.gov/exch/2020-01-31": "https://xbrl.sec.gov/exch/2020/exch-2020-01-31.xsd",
    "http://xbrl.sec.gov/exch/2021": "https://xbrl.sec.gov/exch/2021/exch-2021.xsd",
    "http://xbrl.sec.gov/exch/2022": "https://xbrl.sec.gov/exch/2022/exch-2022.xsd",
    "http://xbrl.sec.gov/exch/2023": "https://xbrl.sec.gov/exch/2023/exch-2023.xsd",
    "http://xbrl.sec.gov/exch-def/2021": "https://xbrl.sec.gov/exch/2021/exch-2021_def.xsd",
    "http://xbrl.sec.gov/exch-lab/2021": "https://xbrl.sec.gov/exch/2021/exch-2021_lab.xsd",
    "http://xbrl.sec.gov/exch-pre/2021": "https://xbrl.sec.gov/exch/2021/exch-2021_pre.xsd",
    "http://xbrl.sec.gov/invest/2011-01-31": "https://xbrl.sec.gov/invest/2011/invest-2011-01-31.xsd",
    "http://xbrl.sec.gov/invest/2012-01-31": "https://xbrl.sec.gov/invest/2012/invest-2012-01-31.xsd",
    "http://xbrl.sec.gov/invest/2013-01-31": "https://xbrl.sec.gov/invest/2013/invest-2013-01-31.xsd",
    "http://xbrl.sec.gov/naics/2011-01-31": "https://xbrl.sec.gov/naics/2011/naics-2011-01-31.xsd",
    "http://xbrl.sec.gov/naics/2017-01-31": "https://xbrl.sec.gov/naics/2017/naics-2017-01-31.xsd",
    "http://xbrl.sec.gov/naics/2021": "https://xbrl.sec.gov/naics/2021/naics-2021.xsd",
    "http://xbrl.sec.gov/naics/2022": "https://xbrl.sec.gov/naics/2022/naics-2022.xsd",
    "http://xbrl.sec.gov/naics/2023": "https://xbrl.sec.gov/naics/2023/naics-2023.xsd",
    "http://xbrl.sec.gov/rr/2010-02-28": "https://xbrl.sec.gov/rr/2010/rr-2010-02-28.xsd",
    "http://xbrl.sec.gov/rr/2012-01-31": "https://xbrl.sec.gov/rr/2012/rr-2012-01-31.xsd",
    "http://xbrl.sec.gov/rr/2018-01-31": "https://xbrl.sec.gov/rr/2018/rr-2018-01-31.xsd",
    "http://xbrl.sec.gov/rr/2021": "https://xbrl.sec.gov/rr/2021/rr-2021.xsd",
    "http://xbrl.sec.gov/rr-cal/2010-02-28": "https://xbrl.sec.gov/rr/2010/rr-cal-2010-02-28.xsd",
    "http://xbrl.sec.gov/rr-cal/2012-01-31": "https://xbrl.sec.gov/rr/2012/rr-cal-2012-01-31.xsd",
    "http://xbrl.sec.gov/rr-cal/2018-01-31": "https://xbrl.sec.gov/rr/2018/rr-cal-2018-01-31.xsd",
    "http://xbrl.sec.gov/rr-def/2010-02-28": "https://xbrl.sec.gov/rr/2010/rr-def-2010-02-28.xsd",
    "http://xbrl.sec.gov/rr-def/2012-01-31": "https://xbrl.sec.gov/rr/2012/rr-def-2012-01-31.xsd",
    "http://xbrl.sec.gov/rr-def/2018-01-31": "https://xbrl.sec.gov/rr/2018/rr-def-2018-01-31.xsd",
    "http://xbrl.sec.gov/rr-def/2021": "https://xbrl.sec.gov/rr/2021/rr-2021_def.xsd",
    "http://xbrl.sec.gov/rr-ent/2010-02-28": "https://xbrl.sec.gov/rr/2010/rr-ent-2010-02-28.xsd",
    "http://xbrl.sec.gov/rr-ent/2012-01-31": "https://xbrl.sec.gov/rr/2012/rr-ent-2012-01-31.xsd",
    "http://xbrl.sec.gov/rr-ent/2018-01-31": "https://xbrl.sec.gov/rr/2018/rr-ent-2018-01-31.xsd",
    "http://xbrl.sec.gov/rr-lab/2021": "https://xbrl.sec.gov/rr/2021/rr-2021_lab.xsd",
    "http://xbrl.sec.gov/rr-pre/2010-02-28": "https://xbrl.sec.gov/rr/2010/rr-pre-2010-02-28.xsd",
    "http://xbrl.sec.gov/rr-pre/2012-01-31": "https://xbrl.sec.gov/rr/2012/rr-pre-2012-01-31.xsd",
    "http://xbrl.sec.gov/rr-pre/2018-01-31": "https://xbrl.sec.gov/rr/2018/rr-pre-2018-01-31.xsd",
    "http://xbrl.sec.gov/rr-pre/2021": "https://xbrl.sec.gov/rr/2021/rr-2021_pre.xsd",
    "http://xbrl.sec.gov/sic/2011-01-31": "https://xbrl.sec.gov/sic/2011/sic-2011-01-31.xsd",
    "http://xbrl.sec.gov/sic/2020-01-31": "https://xbrl.sec.gov/sic/2020/sic-2020-01-31.xsd",
    "http://xbrl.sec.gov/sic/2021": "https://xbrl.sec.gov/sic/2021/sic-2021.xsd",
    "http://xbrl.sec.gov/stpr/2011-01-31": "https://xbrl.sec.gov/stpr/2011/stpr-2011-01-31.xsd",
    "http://xbrl.sec.gov/stpr/2018-01-31": "https://xbrl.sec.gov/stpr/2018/stpr-2018-01-31.xsd",
    "http://xbrl.sec.gov/stpr/2021": "https://xbrl.sec.gov/stpr/2021/stpr-2021.xsd",
    "http://xbrl.sec.gov/stpr/2022": "https://xbrl.sec.gov/stpr/2022/stpr-2022.xsd",
    "http://xbrl.us/ar/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/ar-2008-03-31.xsd",
    "http://xbrl.us/ar/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/ar-2009-01-31.xsd",
    "http://xbrl.us/country/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/country-2008-03-31.xsd",
    "http://xbrl.us/country/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/country-2009-01-31.xsd",
    "http://xbrl.us/currency/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/currency-2008-03-31.xsd",
    "http://xbrl.us/currency/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/currency-2009-01-31.xsd",
    "http://xbrl.us/dei/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/dei-2008-03-31.xsd",
    "http://xbrl.us/dei/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/dei-2009-01-31.xsd",
    "http://xbrl.us/dei-ent/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/dei-ent-2008-03-31.xsd",
    "http://xbrl.us/dei-std/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/dei-std-2008-03-31.xsd",
    "http://xbrl.us/dei-std/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/dei-std-2009-01-31.xsd",
    "http://xbrl.us/exch/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/exch-2008-03-31.xsd",
    "http://xbrl.us/exch/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/exch-2009-01-31.xsd",
    "http://xbrl.us/invest/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/invest-2009-01-31.xsd",
    "http://xbrl.us/mda/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/mda-2008-03-31.xsd",
    "http://xbrl.us/mda/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/mda-2009-01-31.xsd",
    "http://xbrl.us/mr/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/mr-2008-03-31.xsd",
    "http://xbrl.us/mr/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/mr-2009-01-31.xsd",
    "http://xbrl.us/naics/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/naics-2008-03-31.xsd",
    "http://xbrl.us/naics/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/naics-2009-01-31.xsd",
    "http://xbrl.us/rr/2008-12-31": "http://taxonomies.xbrl.us/rr/2008/rr-2008-12-31.xsd",
    "http://xbrl.us/rr-ent/2008-12-31": "http://taxonomies.xbrl.us/rr/2008/rr-ent-2008-12-31.xsd",
    "http://xbrl.us/rr-std/2008-12-31": "http://taxonomies.xbrl.us/rr/2008/rr-std-2008-12-31.xsd",
    "http://xbrl.us/seccert/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/seccert-2008-03-31.xsd",
    "http://xbrl.us/seccert/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/seccert-2009-01-31.xsd",
    "http://xbrl.us/sic/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/sic-2008-03-31.xsd",
    "http://xbrl.us/sic/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/sic-2009-01-31.xsd",
    "http://xbrl.us/soi/2008-11-30": "http://taxonomies.xbrl.us/soi/2008/soi-2008-11-30.xsd",
    "http://xbrl.us/stpr/2008-03-31": "http://xbrl.us/us-gaap/1.0/non-gaap/stpr-2008-03-31.xsd",
    "http://xbrl.us/stpr/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/non-gaap/stpr-2009-01-31.xsd",
    "http://xbrl.us/us-gaap/2008-03-31": "http://xbrl.us/us-gaap/1.0/elts/us-gaap-2008-03-31.xsd",
    "http://xbrl.us/us-gaap/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/elts/us-gaap-2009-01-31.xsd",
    "http://xbrl.us/us-gaap/negated/2008-03-31": "http://www.xbrl.org/lrr/role/negated-2008-03-31.xsd",
    "http://xbrl.us/us-roles/2008-03-31": "http://xbrl.us/us-gaap/1.0/elts/us-roles-2008-03-31.xsd",
    "http://xbrl.us/us-roles/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/elts/us-roles-2009-01-31.xsd",
    "http://xbrl.us/us-types/2008-03-31": "http://xbrl.us/us-gaap/1.0/elts/us-types-2008-03-31.xsd",
    "http://xbrl.us/us-types/2009-01-31": "http://taxonomies.xbrl.us/us-gaap/2009/elts/us-types-2009-01-31.xsd",
    'http://xbrl.sec.gov/rxp/2023': 'https://xbrl.sec.gov/rxp/2023/rxp-2023.xsd',
    'http://xbrl.sec.gov/snj/2023': 'https://xbrl.sec.gov/snj/2023/snj-2023.xsd',
    'http://xbrl.sec.gov/snj-def/2023': 'https://xbrl.sec.gov/snj/2023/snj-2023_def.xsd',
    'http://xbrl.sec.gov/country-def/2023': 'https://xbrl.sec.gov/country/2023/country-2023_def.xsd',
    'http://xbrl.sec.gov/oef/2023': 'https://xbrl.sec.gov/oef/2023/oef-2023.xsd',
    'http://xbrl.sec.gov/oef-rr/2023': 'https://xbrl.sec.gov/oef/2023/oef-rr-2023.xsd',
    'http://xbrl.sec.gov/oef-sr/2023': 'https://xbrl.sec.gov/oef/2023/oef-sr-2023.xsd',
    'http://xbrl.sec.gov/oef-lab/2023': 'https://xbrl.sec.gov/oef/2023/oef-2023_lab.xsd',
    'http://xbrl.sec.gov/oef-cal/2023': 'https://xbrl.sec.gov/oef/2023/oef-2023_cal.xsd',
    'https://xbrl.ifrs.org/taxonomy/2023-03-23/ifrs-full': 'https://xbrl.ifrs.org/taxonomy/2023-03-23/full_ifrs/full_ifrs-cor_2023-03-23.xsd',
    'http://xbrl.sec.gov/rr-sub/2023': 'https://xbrl.sec.gov/rr/2023/rr-sub-2023.xsd',
    'http://xbrl.sec.gov/rr-cal/2023': 'https://xbrl.sec.gov/rr/2023/rr-2023_cal.xsd',
    'http://xbrl.sec.gov/dei-sub/2023': 'https://xbrl.sec.gov/dei/2023/dei-sub-2023.xsd',
    'http://xbrl.sec.gov/dei-def/2023': 'https://xbrl.sec.gov/dei/2023/dei-2023_def.xsd',
    'http://xbrl.sec.gov/dei-lab/2023': 'https://xbrl.sec.gov/dei/2023/dei-2023_lab.xsd',
    'http://xbrl.sec.gov/dei-pre/2023': 'https://xbrl.sec.gov/dei/2023/dei-2023_pre.xsd',
    'http://xbrl.sec.gov/dei/2022q4': 'https://xbrl.sec.gov/dei/2022q4/dei-2022q4.xsd',
    'http://xbrl.sec.gov/dei-sub/2022q4': 'https://xbrl.sec.gov/dei/2022q4/dei-sub-2022q4.xsd',
    'http://xbrl.sec.gov/dei-def/2022q4': 'https://xbrl.sec.gov/dei/2022q4/dei-2022q4_def.xsd',
    'http://xbrl.sec.gov/dei-lab/2022q4': 'https://xbrl.sec.gov/dei/2022q4/dei-2022q4_lab.xsd',
    'http://xbrl.sec.gov/dei-pre/2022q4': 'https://xbrl.sec.gov/dei/2022q4/dei-2022q4_pre.xsd',
    'http://xbrl.sec.gov/ecd/2023': 'https://xbrl.sec.gov/ecd/2023/ecd-2023.xsd',
    'http://xbrl.sec.gov/ecd-sub/2023': 'https://xbrl.sec.gov/ecd/2023/ecd-sub-2023.xsd',
    'http://xbrl.sec.gov/ecd/2022q4': 'https://xbrl.sec.gov/ecd/2022q4/ecd-2022q4.xsd',
    'http://xbrl.sec.gov/ecd-sub/2022q4': 'https://xbrl.sec.gov/ecd/2022q4/ecd-sub-2022q4.xsd',
    'http://fasb.org/srt-sup/2022q3': 'https://xbrl.fasb.org/srt/2022q3/srt-sup-2022q3.xsd',
    'http://fasb.org/us-gaap-sup/2022q3': 'https://xbrl.fasb.org/us-gaap/2022q3/us-gaap-sup-2022q3.xsd',
    'http://xbrl.sec.gov/vip/2023': 'https://xbrl.sec.gov/vip/2023/vip-2023.xsd',
    'http://xbrl.sec.gov/vip-n3/2023': 'https://xbrl.sec.gov/vip/2023/vip-n3-2023.xsd',
    'http://xbrl.sec.gov/vip-n4/2023': 'https://xbrl.sec.gov/vip/2023/vip-n4-2023.xsd',
    'http://xbrl.sec.gov/vip-n6/2023': 'https://xbrl.sec.gov/vip/2023/vip-n6-2023.xsd',
    'http://xbrl.sec.gov/country/2023': 'https://xbrl.sec.gov/country/2023/country-2023.xsd',
    'http://xbrl.sec.gov/currency/2023': 'https://xbrl.sec.gov/currency/2023/currency-2023.xsd',
    'http://xbrl.sec.gov/vip/2022q2': 'https://xbrl.sec.gov/vip/2022q2/vip-2022q2.xsd',
    'http://xbrl.sec.gov/vip-n3/2022q2': 'https://xbrl.sec.gov/vip/2022q2/vip-n3-2022q2.xsd',
    'http://xbrl.sec.gov/vip-n4/2022q2': 'https://xbrl.sec.gov/vip/2022q2/vip-n4-2022q2.xsd',
    'http://xbrl.sec.gov/vip-n6/2022q2': 'https://xbrl.sec.gov/vip/2022q2/vip-n6-2022q2.xsd',
    'http://xbrl.sec.gov/country/2022': 'https://xbrl.sec.gov/country/2022/country-2022.xsd',
    'http://xbrl.sec.gov/sic/2022': 'https://xbrl.sec.gov/sic/2022/sic-2022.xsd',
    'https://xbrl.ifrs.org/taxonomy/2022-03-24/ifrs-full': 'https://xbrl.ifrs.org/taxonomy/2022-03-24/full_ifrs/full_ifrs-cor_2022-03-24.xsd',
    'http://xbrl.sec.gov/dei-lab/2022': 'https://xbrl.sec.gov/dei/2022/dei-2022_lab.xsd',
    'http://xbrl.sec.gov/dei-pre/2022': 'https://xbrl.sec.gov/dei/2022/dei-2022_pre.xsd',
    'http://xbrl.sec.gov/dei-def/2022': 'https://xbrl.sec.gov/dei/2022/dei-2022_def.xsd',
    'http://xbrl.sec.gov/sic/2023': 'https://xbrl.sec.gov/sic/2023/sic-2023.xsd',
    'http://xbrl.sec.gov/stpr/2023': 'https://xbrl.sec.gov/stpr/2023/stpr-2023.xsd',
    'http://fasb.org/us-types/2023': 'https://xbrl.fasb.org/us-gaap/2023/elts/us-types-2023.xsd',
    'http://fasb.org/us-roles/2023': 'https://xbrl.fasb.org/us-gaap/2023/elts/us-roles-2023.xsd',
    'http://fasb.org/srt-types/2023': 'https://xbrl.fasb.org/srt/2023/elts/srt-types-2023.xsd',
    'http://fasb.org/srt-roles/2023': 'https://xbrl.fasb.org/srt/2023/elts/srt-roles-2023.xsd',
    'http://xbrl.sec.gov/dei-sub/2022': 'https://xbrl.sec.gov/dei/2022/dei-sub-2022.xsd',
    'http://fasb.org/us-types/2022': 'https://xbrl.fasb.org/us-gaap/2022/elts/us-types-2022.xsd',
    'http://fasb.org/us-roles/2022': 'https://xbrl.fasb.org/us-gaap/2022/elts/us-roles-2022.xsd',
    'http://fasb.org/srt-types/2022': 'https://xbrl.fasb.org/srt/2022/elts/srt-types-2022.xsd',
    'http://fasb.org/srt-roles/2022': 'https://xbrl.fasb.org/srt/2022/elts/srt-roles-2022.xsd',
    'http://xbrl.sec.gov/cef/2023': 'https://xbrl.sec.gov/cef/2023/cef-2023.xsd',
    'http://xbrl.sec.gov/cef-pre/2023': 'https://xbrl.sec.gov/cef/2023/cef-2023_pre.xsd',
    'http://xbrl.sec.gov/cef/2022': 'https://xbrl.sec.gov/cef/2022/cef-2022.xsd',
    'http://xbrl.sec.gov/vip/2022': 'https://xbrl.sec.gov/vip/2022/vip-2022.xsd',
    'http://xbrl.sec.gov/vip-n3/2022': 'https://xbrl.sec.gov/vip/2022/vip-n3-2022.xsd',
    'http://xbrl.sec.gov/vip-n4/2022': 'https://xbrl.sec.gov/vip/2022/vip-n4-2022.xsd',
    'http://xbrl.sec.gov/vip-n6/2022': 'https://xbrl.sec.gov/vip/2022/vip-n6-2022.xsd',
    'http://xbrl.sec.gov/rr/2023': 'https://xbrl.sec.gov/rr/2023/rr-2023.xsd',
    'http://xbrl.sec.gov/rr-lab/2023': 'https://xbrl.sec.gov/rr/2023/rr-2023_lab.xsd',
    'http://xbrl.sec.gov/rr-pre/2023': 'https://xbrl.sec.gov/rr/2023/rr-2023_pre.xsd',
    'http://xbrl.sec.gov/rr-def/2023': 'https://xbrl.sec.gov/rr/2023/rr-2023_def.xsd',
    'http://xbrl.sec.gov/rr/2022': 'https://xbrl.sec.gov/rr/2022/rr-2022.xsd',
    'http://xbrl.sec.gov/rr-lab/2022': 'https://xbrl.sec.gov/rr/2022/rr-2022_lab.xsd',
    'http://xbrl.sec.gov/rr-pre/2022': 'https://xbrl.sec.gov/rr/2022/rr-2022_pre.xsd',
    'http://xbrl.sec.gov/rr-def/2022': 'https://xbrl.sec.gov/rr/2022/rr-2022_def.xsd',
    'http://www.xbrl.org/dtr/type/2022-03-31': 'https://www.xbrl.org/dtr/type/2022-03-31/types.xsd'
}


class Concept:
    """
    Class representing a Concept defined in the schema (xs:element)
    i.e:
    <xs:element id='us-gaap_Assets' name='Assets' nillable='true'
    substitutionGroup='xbrli:item' type='xbrli:monetaryItemType'
    xbrli:balance='debit' xbrli:periodType='instant' />
    """

    def __init__(self, xml_id: str, schema_url: str, name: str) -> None:
        """
        :param xml_id: Id of the concept in the xml
        :param schema_url: url of the schema in which the concept is defined
        :param name: name of the concept
        """
        self.xml_id: str = xml_id
        self.schema_url: str = schema_url
        self.name: str = name
        self.substitution_group: str or None = None
        self.concept_type: str or None = None
        self.abstract: bool or None = None
        self.nillable: bool or None = None
        self.period_type: str or None = None
        self.balance: str or None = None
        self.labels: [Label] = []

    def __str__(self) -> str:
        return self.name


class ExtendedLinkRole:
    """
    Class representing a ELR.
    A ELR is a set of relations representing a piece of the report (i.e. "1003000 - Statement - Consolidated Balance Sheets")
    ELR's a used to separate Relation linkbases into smaller logical chunks, so it is commonly referenced in the
    calculation, definition and presentation linkbases
    """

    def __init__(self, role_id: str, uri: str, definition: str) -> None:
        """

        :param role_id:
        :param uri:
        :param definition:
        """
        self.xml_id: str = role_id
        self.uri: str = uri
        self.definition: str = definition
        self.definition_link: ExtendedLink or None = None
        self.presentation_link: ExtendedLink or None = None
        self.calculation_link: ExtendedLink or None = None

    def __str__(self) -> str:
        return self.definition


class TaxonomySchema:
    """
    Class represents a Generic Taxonomy Schema. Since this parser is optimized for EDGAR submission's,
    it will only differentiate between the Extending Taxonomy (the taxonomy that comes with the filing) and
    multiple base Taxonomies (i.e dei, us-gaap, exch, naics, sic ...).
    This parser will not parse all Schemas and imports, only what is necessary.
    """

    def __init__(self, schema_url: str, namespace: str):
        """
        The imports array stores an array of all Schemas that are imported.


        :param schema_url:
        :param namespace:
        """
        self.imports: List[TaxonomySchema] = []
        self.link_roles: List[ExtendedLinkRole] = []
        self.lab_linkbases: List[Linkbase] = []
        self.def_linkbases: List[Linkbase] = []
        self.cal_linkbases: List[Linkbase] = []
        self.pre_linkbases: List[Linkbase] = []

        self.schema_url = schema_url
        self.namespace = namespace
        # store the concepts in a dictionary with the concept_id as key
        self.concepts: dict = {}
        # The linkbases reference concepts by their id, the instance file by name.
        # In order to get O(1) in both cases, create a dictionary where the id of a concept can be looked up,
        # based on the name
        self.name_id_map: dict = {}

    def __str__(self) -> str:
        return self.namespace

    def get_taxonomy(self, url: str):
        """
        Returns the taxonomy with the given namespace (if it is the current taxonomy, or if it is imported)
        If the taxonomy cannot be found, the function will return None
        :param url: can either be the namespace or the schema url
        :return: either a TaxonomySchema obj or None
        """
        if compare_uri(self.namespace, url) or compare_uri(self.schema_url, url):
            return self

        for imported_tax in self.imports:
            result = imported_tax.get_taxonomy(url)
            if result is not None:
                return result
        return None

    def get_schema_urls(self) -> []:
        """
        Returns an array of all taxonomy urls that are used by this taxonomy
        Also includes the schema url of this taxonomy
        :return:
        """
        urls: [] = [self.schema_url]
        for imported_tax in self.imports:
            urls += imported_tax.get_schema_urls()
        return list(set(urls))


def parse_common_taxonomy(cache: HttpCache, namespace: str) -> TaxonomySchema or None:
    """
    Parses a taxonomy by namespace. This is only possible for certain well known taxonomies, as we need the schema_url for
    parsing it.
    Some xbrl documents from the sec use namespaces without defining a schema url for those namespaces, so this function
    might come in handy
    :param cache:
    :param namespace: namespace of the taxonomy
    :return:
    """

    if namespace in ns_schema_map:
        return parse_taxonomy_url(ns_schema_map[namespace], cache)
    return None


@lru_cache(maxsize=60)
def parse_taxonomy_url(schema_url: str, cache: HttpCache) -> TaxonomySchema:
    """
    Parses a taxonomy schema file from the internet

    :param schema_url: full link to the taxonomy schema
    :param cache: :class:`xbrl.cache.HttpCache` instance
    :return: parsed :class:`xbrl.taxonomy.TaxonomySchema` object
    """
    if not is_url(schema_url): raise XbrlParseException('This function only parses remotely saved taxonomies. '
                                                        'Please use parse_taxonomy to parse local taxonomy schemas')
    schema_path: str = cache.cache_file(schema_url)
    return parse_taxonomy(schema_path, cache, schema_url)


def parse_taxonomy(schema_path: str, cache: HttpCache, schema_url: str or None = None) -> TaxonomySchema:
    """
    Parses a taxonomy schema file.

    :param schema_path: url to the schema (on the internet)
    :param cache: :class:`xbrl.cache.HttpCache` instance
    :param schema_url: if this url is set, the script will try to fetch additionally imported files such as linkbases or
        imported schemas from the remote location. If this url is None, the script will try to find those resources locally.
    :return: parsed :class:`xbrl.taxonomy.TaxonomySchema` object
    """
    schema_path = str(schema_path)
    if is_url(schema_path): raise XbrlParseException('This function only parses locally saved taxonomies. '
                                                     'Please use parse_taxonomy_url to parse remote taxonomy schemas')
    if not os.path.exists(schema_path):
        raise TaxonomyNotFound(f"Could not find taxonomy schema at {schema_path}")

    # Get the local absolute path to the schema file (and download it if it is not yet cached)
    root: ET.Element = ET.parse(schema_path).getroot()
    # get the target namespace of the taxonomy
    target_ns = root.attrib['targetNamespace']
    taxonomy: TaxonomySchema = TaxonomySchema(schema_url if schema_url else schema_path, target_ns)

    import_elements: List[ET.Element] = root.findall('xsd:import', NAME_SPACES)

    for import_element in import_elements:
        import_uri = import_element.attrib['schemaLocation'].strip()

        # Skip empty imports
        if import_uri == "":
            continue

        # sometimes the import schema location is relative. i.e schemaLocation="xbrl-linkbase-2003-12-31.xsd"
        if is_url(import_uri):
            # fetch the schema file from remote
            taxonomy.imports.append(parse_taxonomy_url(import_uri, cache))
        elif schema_url:
            # fetch the schema file from remote by reconstructing the full url
            import_url = resolve_uri(schema_url, import_uri)
            taxonomy.imports.append(parse_taxonomy_url(import_url, cache))
        else:
            # We have to try to fetch the linkbase locally because no full url can be constructed
            import_path = resolve_uri(schema_path, import_uri)
            taxonomy.imports.append(parse_taxonomy(import_path, cache))

    role_type_elements: List[ET.Element] = root.findall('xsd:annotation/xsd:appinfo/link:roleType', NAME_SPACES)
    # parse ELR's
    for elr in role_type_elements:
        elr_definition = elr.find(LINK_NS + 'definition')
        if elr_definition is None or elr_definition.text is None: continue
        taxonomy.link_roles.append(
            ExtendedLinkRole(elr.attrib['id'], elr.attrib['roleURI'], elr_definition.text.strip()))

    # find all elements that are defined in the schema
    for element in root.findall(XDS_NS + 'element'):
        # if a concept has no id, it can not be referenced by a linkbase, so just ignore it
        if 'id' not in element.attrib or 'name' not in element.attrib:
            continue
        el_id: str = element.attrib['id']
        el_name: str = element.attrib['name']

        concept = Concept(el_id, schema_url, el_name)
        concept.type = element.attrib['type'] if 'type' in element.attrib else False
        concept.nillable = bool(element.attrib['nillable']) if 'nillable' in element.attrib else False
        concept.abstract = bool(element.attrib['abstract']) if 'abstract' in element.attrib else False
        type_attr_name = XBRLI_NS + 'periodType'
        concept.period_type = element.attrib[type_attr_name] if type_attr_name in element.attrib else None
        balance_attr_name = XBRLI_NS + 'balance'
        concept.balance = element.attrib[balance_attr_name] if balance_attr_name in element.attrib else None
        # remove the prefix from the substitutionGroup (i.e xbrli:item -> item)
        concept.substitution_group = \
            element.attrib['substitutionGroup'].split(':')[-1] if 'substitutionGroup' in element.attrib else None

        taxonomy.concepts[concept.xml_id] = concept
        taxonomy.name_id_map[concept.name] = concept.xml_id

    linkbase_ref_elements: List[ET.Element] = root.findall('xsd:annotation/xsd:appinfo/link:linkbaseRef', NAME_SPACES)
    for linkbase_ref in linkbase_ref_elements:
        linkbase_uri = linkbase_ref.attrib[XLINK_NS + 'href']
        role = linkbase_ref.attrib[XLINK_NS + 'role'] if XLINK_NS + 'role' in linkbase_ref.attrib else None
        linkbase_type = LinkbaseType.get_type_from_role(role) if role is not None else LinkbaseType.guess_linkbase_role(
            linkbase_uri)

        # check if the linkbase url is relative
        if is_url(linkbase_uri):
            # fetch the linkbase from remote
            linkbase: Linkbase = parse_linkbase_url(linkbase_uri, linkbase_type, cache)
        elif schema_url:
            # fetch the linkbase from remote by reconstructing the full URL
            linkbase_url = resolve_uri(schema_url, linkbase_uri)
            linkbase: Linkbase = parse_linkbase_url(linkbase_url, linkbase_type, cache)
        else:
            # We have to try to fetch the linkbase locally because no full url can be constructed
            linkbase_path = resolve_uri(schema_path, linkbase_uri)
            linkbase: Linkbase = parse_linkbase(linkbase_path, linkbase_type)

        # add the linkbase to the taxonomy
        if linkbase_type == LinkbaseType.DEFINITION:
            taxonomy.def_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.CALCULATION:
            taxonomy.cal_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.PRESENTATION:
            taxonomy.pre_linkbases.append(linkbase)
        elif linkbase_type == LinkbaseType.LABEL:
            taxonomy.lab_linkbases.append(linkbase)

    # loop over the ELR's of the schema and assign the extended links from the linkbases
    for elr in taxonomy.link_roles:
        for extended_def_links in [def_linkbase.extended_links for def_linkbase in taxonomy.def_linkbases]:
            for extended_def_link in extended_def_links:
                if extended_def_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.definition_link = extended_def_link
                    break
        for extended_pre_links in [pre_linkbase.extended_links for pre_linkbase in taxonomy.pre_linkbases]:
            for extended_pre_link in extended_pre_links:
                if extended_pre_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.presentation_link = extended_pre_link
                    break
        for extended_cal_links in [cal_linkbase.extended_links for cal_linkbase in taxonomy.cal_linkbases]:
            for extended_cal_link in extended_cal_links:
                if extended_cal_link.elr_id.split('#')[1] == elr.xml_id:
                    elr.calculation_link = extended_cal_link
                    break

    for label_linkbase in taxonomy.lab_linkbases:
        for extended_link in label_linkbase.extended_links:
            for root_locator in extended_link.root_locators:
                # find the taxonomy the locator is referring to
                schema_url, concept_id = unquote(root_locator.href).split('#')
                c_taxonomy: TaxonomySchema = taxonomy.get_taxonomy(schema_url)
                if c_taxonomy is None:
                    if schema_url in ns_schema_map.values():
                        c_taxonomy = parse_taxonomy_url(schema_url, cache)
                        taxonomy.imports.append(c_taxonomy)
                    else:
                        continue
                concept: Concept = c_taxonomy.concepts[concept_id]
                concept.labels = []
                for label_arc in root_locator.children:
                    for label in label_arc.labels:
                        concept.labels.append(label)

    return taxonomy
