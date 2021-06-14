## XBRL-Parser

[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![PyPI](https://img.shields.io/pypi/v/py-xbrl)](https://pypi.org/project/py-xbrl/#history)
[![PyPI - Status](https://img.shields.io/pypi/status/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![GitHub](https://img.shields.io/github/license/manusimidt/xbrl_parser)](https://github.com/manusimidt/xbrl_parser/blob/main/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/manusimidt/xbrl_parser)](https://github.com/m4nu3l99/xbrl_parser)


> #### DISCLAIMER
> This xbrl-parser is currently in a beta phase. Each new release can introduce breaking changes.
>
> Also keep in mind that downloading and parsing large amounts of XBRL Submissions can result in huge amounts of traffic!
> The parser not only has to download the instance document itself, but all taxonomy schemas and linkbases that are related
> to this submission! Before using the parser, check the usage policy of the data source operator!
>
> ❗ Feedback: Feel free to ask me any questions, suggestions and ideas in the [discussions form](https://github.com/manusimidt/xbrl_parser/discussions) or contact me directly

### Installation
```shell
pip install py-xbrl
```

The XBRL Parser consists of three modules:

- linkbase: This module parses calculation, definition, presentation and label linkbases
- taxonomy: This module parses taxonomy schemas
- instance: This module parses the instance document itself

This quick readme will only explain how to parse an instance document since this is probably the most common use case.

### Http Cache

This parser requires a place to store files that are related with the xbrl instance document. This folder has to be
defined before parsing submissions. Instance documents usually import many huge standard taxonomies. Submissions from
the SEC for example import the US-GAAP Taxonomy. To prevent downloading these standard taxonomies for every submission a
cache is required even if you already have downloaded the instance documents onto your pc.

### Parse locally saved submissions

#### XBRL:

```python
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance

logging.basicConfig(level=logging.INFO)
cache: HttpCache = HttpCache('./cache')
# Replace the dummy header with your information!! 
# services like SEC EDGAR require you to disclose information about your bot! (https://www.sec.gov/privacy.htm#security)
cache.set_headers({'From': 'your.name@company.com', 'User-Agent': 'Tool/Version (Website)'})
xbrlParser = XbrlParser(cache)

xbrl_path = './data/TSLA/2018_Q1/tsla-20180331.xml'
inst: XbrlInstance = xbrlParser.parse_instance_locally(xbrl_path)
```

#### inline XBRL:

```python
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance

logging.basicConfig(level=logging.INFO)
cache: HttpCache = HttpCache('./cache')
# Replace the dummy header with your information!! 
# services like SEC EDGAR require you to disclose information about your bot! (https://www.sec.gov/privacy.htm#security)
cache.set_headers({'From': 'your.name@company.com', 'User-Agent': 'Tool/Version (Website)'})
xbrlParser = XbrlParser(cache)

ixbrl_path: str = './data/AAPL/2020_FY/aapl-20201226.htm'
inst: XbrlInstance = xbrlParser.parse_instance_locally(ixbrl_path)
```

### Parse remotely saved submissions

#### XBRL:

```python
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlInstance, XbrlParser

logging.basicConfig(level=logging.INFO)
cache: HttpCache = HttpCache('./cache')
# Replace the dummy header with your information!! 
# services like SEC EDGAR require you to disclose information about your bot! (https://www.sec.gov/privacy.htm#security)
cache.set_headers({'From': 'your.name@company.com', 'User-Agent': 'Tool/Version (Website)'})
xbrlParser = XbrlParser(cache)

xbrl_url = 'https://www.sec.gov/Archives/edgar/data/789019/000156459017014900/msft-20170630.xml'
inst: XbrlInstance = xbrlParser.parse_instance(xbrl_url)
```

#### inline XBRL:

```python
import logging
from xbrl.cache import HttpCache
from xbrl.instance import XbrlParser, XbrlInstance

logging.basicConfig(level=logging.INFO)
cache: HttpCache = HttpCache('./cache')
# Replace the dummy header with your information!! 
# services like SEC EDGAR require you to disclose information about your bot! (https://www.sec.gov/privacy.htm#security)
cache.set_headers({'From': 'your.name@company.com', 'User-Agent': 'Tool/Version (Website)'})
xbrlParser = XbrlParser(cache)

ixbrl_url = 'https://www.sec.gov/Archives/edgar/data/0000789019/000156459021002316/msft-10q_20201231.htm'
inst: XbrlInstance = xbrlParser.parse_instance(ixbrl_url)
```

#### Extra configuration:
You can modify the downloading default configuration params adding this simple line of code:
```python
cache.set_connection_params(delay=500, retries=5, backoff_factor=0.8, logs=True)
```
where each of the parameters is explained here:
* _delay_: number of millisecons to wait between successfull requests
* _retries_: number of times to retry a request in case it fails
* _backoff_factor_: Factor used to measure time to sleep between failed requests with the formula: `{backoff factor} * (2 ** ({number of total retries} - 1))`
* _logs_: Boolean to show logs (default True)

### How to use the XbrlInstance object
The data of every submission that is parsed with one of the four functions of this parser will be stored into
the XbrlInstance object. This way you no longer have to deal with the differentiation between XBRL and inline XBRL.
The following code gives an example how you could store certain facts into a dataframe:

```python
# now extracting some selected facts
extracted_data: [dict] = []
selected_facts: [str] = ['Assets', 'Liabilities', 'StockholdersEquity']
for fact in inst.facts:
    # use some kind of filter, otherwise your dataframe will have maaaaannnyyy columns (one for every concept)
    if fact.concept.name not in selected_facts: continue
    # only select non-dimensional data for now
    if len(fact.context.segments) > 0: continue
    extracted_data.append({'date': fact.context.instant_date, 'concept': fact.concept.name, 'value': fact.value})

df: pd.DataFrame = pd.DataFrame(data=extracted_data)
df.drop_duplicates(inplace=True)
#pivot the dataframe so that the concept name is now the column
pivot_df: pd.DataFrame() = df.pivot(index='date', columns='concept')
print(pivot_df)
```

This will create the following dataframe:

| |Assets|Liabilities|ShareholdersEquity|
| ------------- |-------------:| -----:|-----:|
| 2017-09-30 | 2.656125e+11| 2.164832e+11 | 1.340470e+11 |
| 2018-09-29 | 3.126446e+11| 2.646132e+11 | 1.071470e+11 |
| 2019-09-28 | 3.385160e+11| 2.480280e+11 | 9.048800e+11 |
| 2020-09-26 | 3.238880e+11| 2.585490e+11 | 6.533900e+11 |

This is only an example. You could also store the Facts in a database or somewhere else.
Feel free to experiment with it.
Here is an overview over the different classes a XbrlInstance object contains:
![alt text](./docs/img/parser_class_diagram.png "Class Diagram")

