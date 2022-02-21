"""
This module handles all fact transformations.

What are fact transformation rules?
In iXBRL filers are allowed to tag textual values like "one million" or "17th of January 2022". In XBRL those facts
would be represented in a normalized manner (1000000, 2022-01-17). To normalize the text values, the iXBRL specification
provides for so-called transformation rules. The transformation rule "zerodash" for example tells us that the tagged
char "-" has a normalized value of 0.

The transformation rules are collected in a so-called transformation rule registry. As of writing SEC Edgar supports
the following registries:

Name: XII Transformation Registry 3
Prefix: ixt
Namespace: http://www.xbrl.org/inlineXBRL/transformation/2015-02-26

Name: XII Transformation Registry 4
Prefix: ixt
Namespace: http://www.xbrl.org/inlineXBRL/transformation/2020-02-12

Name: SEC Specific Transformation Registry
Prefix: ixt-sec
Namespace: http://www.sec.gov/inlineXBRL/transformation/2015-08-31
"""
import re

from xbrl.transformations.text2num import text2num, replace_text_numbers


class TransformationException(Exception):
    """ Generic Exception thrown if an issue was encountered while transforming the fact value """

    def __init__(self, msg):
        Exception.__init__(self, msg)


class RegistryNotSupported(TransformationException):
    """ Exception thrown if the transformation registry is not supported """

    def __init__(self, namespace: str):
        TransformationException.__init__(self, f"The transformation registry {namespace} is currently not supported")


class InvalidTransformation(TransformationException):
    """ Exception thrown if the transformation format is not in the registry """

    def __init__(self, namespace: str, formatCode: str):
        msg = f'The transformation rule "{formatCode}" is not implemented in registry {namespace}'
        TransformationException.__init__(self, msg)


class TransformationNotImplemented(TransformationException):
    """ Exception thrown if the transformation is in the registry but not implemented in py-xbrl """

    def __init__(self, msg):
        TransformationException.__init__(self, msg)


def notImplemented(arg: str) -> str:
    raise TransformationNotImplemented(f"Could not normalize {arg} because the transformation rule is not implemented")


# region normalization maps
monthNorm = {
    'jan': '01',
    'feb': '02',
    'mar': '03',
    'apr': '04',
    'may': '05',
    'jun': '06',
    'jul': '07',
    'aug': '08',
    'sep': '09',
    'sept': '09',
    'oct': '10',
    'nov': '11',
    'dec': '12',
    'january': '01',
    'february': '02',
    'march': '03',
    'april': '04',
    'june': '06',
    'july': '07',
    'august': '08',
    'september': '09',
    'october': '10',
    'november': '11',
    'december': '12'
}

# exchange maps (https://www.sec.gov/info/edgar/specifications/edgarfm-vol2-v59.pdf page 203)
exchangeNorm = {
    'new york stock exchange': 'NYSE',
    'nasdaq global select market': 'NASDAQ',
    'nasdaq stock market': 'NASDAQ',
    'box exchange': 'BOX',
    'nasdaq bx': 'BX',
    'cboe c2 exchange': 'C2',
    'cboe exchange': 'CBOE',
    'chicago stock exchange': 'CHX',
    'cboe byx exchange': 'CboeBYX',
    'cboe bzx exchange': 'CboeBZX',
    'cboe edga exchange': 'CboeEDGA',
    'cboe edgx exchange': 'CboeEDGX',
    'nasdaq gemx': 'GEMX',
    'investors exchange': 'IEX',
    'nasdaq ise': 'ISE',
    'miami international securities exchange': 'MIAX',
    'nasdaq mrx': 'MRX',
    'nyse american': 'NYSEAMER',
    'nyse arca': 'NYSEArca',
    'nyse national': 'NYSENAT',
    'miax pearl': 'PEARL',
    'nasdaq phlx': 'Phlx',
}


def yearNorm(year: str) -> str:
    if len(year) == 4: return year
    if len(year) == 2: return '19' + year if int(year) > 55 else '20' + year
    raise TransformationException(f'Could not normalize "{year}" to a year')


# endregion normalization maps

# region ixt mappings


def dateDayMonth(arg: str) -> str:
    """ (D)D*(M)M -> --MM-DD """
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"--{seg[1].zfill(2)}-{seg[0].zfill(2)}"


def dateDayMonthEN(arg: str) -> str:
    # (D)D*Mon(th) -> --MM-DD
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"--{monthNorm[seg[1]]}-{seg[0].zfill(2)}"


def dateDayMonthYear(arg: str) -> str:
    # (D)D*(M)M*(Y)Y(YY) -> YYYY-MM-DD
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"{yearNorm(seg[2])}-{seg[1].zfill(2)}-{seg[0].zfill(2)}"


def dateDayMonthYearEN(arg: str) -> str:
    # (D)D*Mon(th)*(Y)Y(YY) -> YYYY-MM-DD
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"{yearNorm(seg[2])}-{monthNorm[seg[1]]}-{seg[0].zfill(2)}"


def dateMonthDay(arg: str) -> str:
    # (M)M*(D)D -> --MM-DD
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"--{seg[0].zfill(2)}-{seg[1].zfill(2)}"


def dateMonthDayEN(arg: str) -> str:
    # Mon(th)*(D)D -> --MM-DD
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"--{monthNorm[seg[0]]}-{seg[1].zfill(2)}"


def dateMonthDayYear(arg: str) -> str:
    # (M)M*(D)D*(Y)Y(YY) -> YYYY-MM-DD
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"{yearNorm(seg[2])}-{seg[0].zfill(2)}-{seg[1].zfill(2)}"


def dateMonthDayYearEN(arg: str) -> str:
    # Mon(th)*(D)D*(Y)Y(YY) -> YYYY-MM-DD
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"{yearNorm(seg[2])}-{monthNorm[seg[0]]}-{seg[1].zfill(2)}"


def dateMonthYear(arg: str) -> str:
    # (M)M*(Y)Y(YY) -> YYYY-MM
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"{yearNorm(seg[1])}-{seg[0].zfill(2)}"


def dateMonthYearEN(arg: str) -> str:
    # Mon(th)*(Y)Y(YY) -> YYYY-MM
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"{yearNorm(seg[1])}-{monthNorm[seg[0]]}"


def dateYearMonthDay(arg: str) -> str:
    # (Y)Y(YY)*(M)M*(D)D -> YYYY-MM-DD
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"{yearNorm(seg[0])}-{seg[1].zfill(2)}-{seg[2].zfill(2)}"


def dateYearMonth(arg: str) -> str:
    # (Y)Y(YY)*(M)M
    seg = re.split(r'[^\d]+', arg)  # split at any char sequence that is not a digit
    return f"{yearNorm(seg[0])}-{seg[1].zfill(2)}"


def dateYearMonthEN(arg: str) -> str:
    # (Y)Y(YY)*Mon(th) -> YYYY-MM
    seg = re.split(r'[^\d\w]+', arg)  # split at any char that is not a digit nor a word
    return f"{yearNorm(seg[0])}-{monthNorm[seg[1]]}"


def numCommaDecimal(arg: str) -> str:
    # nnn*nnn*nnn,n -> nnnnnnnnn.n
    arg = re.sub(r'[^\d,]+', '', arg)  # remove all chars that are not a digit and not a comma
    return arg.replace(',', '.')


def numDotDecimal(arg: str) -> str:
    # nnn*nnn*nnn.n -> nnnnnnnnn.n
    return re.sub(r'[^\d.]+', '', arg)  # remove all chars that are not a digit and not a dot


# endregion ixt mappings

# region ixt-sec mappings

def durWordSen(arg: str) -> str:
    value = replace_text_numbers(arg)
    years, months, days = 0, 0, 0
    words: [str] = value.split(' ')
    for x in range(len(words) - 1):
        if not words[x].isnumeric():
            continue
        if 'year' in words[x + 1]:
            years = int(words[x])
        elif 'month' in words[x + 1]:
            months = int(words[x])
        elif 'day' in words[x + 1]:
            days = int(words[x])
    return f'P{years}Y{months}M{days}D'


def numWordSen(arg: str) -> str:
    if arg == 'no' or arg == 'none':
        return '0'
    else:
        arg = arg.replace(' and ', ' ')
        return str(text2num(arg))


def ballotBox(arg: str) -> str:
    if arg == '&#9744;' or arg == '☐':
        return 'false'
    elif arg == '&#9745;' or arg == '☑' or arg == '&#9746;' or arg == '☒':
        return 'true'
    else:
        raise TransformationException("Invalid input for ballotBox transformation rule")


def exchnameen(arg: str) -> str:
    name = arg.lower().strip()
    # remove any commas, points, e.t.c and "inc" or "llc"
    name = re.sub(r'[^\w\s\d]|inc|llc|the', '', name.strip().lower())
    # remove multiple spaces ("  ")
    name = re.sub('r {2,}', ' ', name.strip())
    if name.upper() in exchangeNorm.values():
        return name.upper()
    try:
        return exchangeNorm[name]
    except KeyError:
        raise TransformationException(f'Unknown exchange "{name}"')


# endregion ixt-sec mappings

ixt3 = {
    'booleanfalse': lambda arg: 'false',
    'booleantrue': lambda arg: 'true',
    'calindaymonthyear': notImplemented,
    'datedaymonth': dateDayMonth,
    'datedaymonthdk': notImplemented,
    'datedaymonthen': dateDayMonthEN,
    'datedaymonthyear': dateDayMonthYear,
    'datedaymonthyeardk': notImplemented,
    'datedaymonthyearen': dateDayMonthYearEN,
    'datedaymonthyearin': notImplemented,
    'dateerayearmonthdayjp': notImplemented,
    'dateerayearmonthjp': notImplemented,
    'datemonthday': dateMonthDay,
    'datemonthdayen': dateMonthDayEN,
    'datemonthdayyear': dateMonthDayYear,
    'datemonthdayyearen': dateMonthDayYearEN,
    'datemonthyear': dateMonthYear,
    'datemonthyeardk': notImplemented,
    'datemonthyearen': dateMonthYearEN,
    'datemonthyearin': notImplemented,
    'dateyearmonthday': dateYearMonthDay,
    'dateyearmonthdaycjk': notImplemented,
    'dateyearmonthcjk': notImplemented,
    'dateyearmonthen': dateYearMonthEN,
    'nocontent': lambda arg: '',
    'numcommadecimal': numCommaDecimal,
    'numdotdecimal': numDotDecimal,
    'numdotdecimalin': notImplemented,
    'numunitdecimal': notImplemented,
    'numunitdecimalin': notImplemented,
    'zerodash': lambda arg: '0'
}

ixt4 = {
    'date-day-month': dateDayMonth,
    'date-day-month-year': dateDayMonthYear,
    'date-day-monthname-bg': notImplemented,
    'date-day-monthname-cs': notImplemented,
    'date-day-monthname-da': notImplemented,
    'date-day-monthname-de': notImplemented,
    'date-day-monthname-el': notImplemented,
    'date-day-monthname-en': dateDayMonthEN,
    'date-day-monthname-es': notImplemented,
    'date-day-monthname-et': notImplemented,
    'date-day-monthname-fi': notImplemented,
    'date-day-monthname-fr': notImplemented,
    'date-day-monthname-hr': notImplemented,
    'date-day-monthname-it': notImplemented,
    'date-day-monthname-lv': notImplemented,
    'date-day-monthname-nl': notImplemented,
    'date-day-monthname-no': notImplemented,
    'date-day-monthname-pl': notImplemented,
    'date-day-monthname-pt': notImplemented,
    'date-day-monthname-ro': notImplemented,
    'date-day-monthname-sk': notImplemented,
    'date-day-monthname-sl': notImplemented,
    'date-day-monthname-sv': notImplemented,
    'date-day-monthname-year-bg': notImplemented,
    'date-day-monthname-year-cs': notImplemented,
    'date-day-monthname-year-da': notImplemented,
    'date-day-monthname-year-de': notImplemented,
    'date-day-monthname-year-el': notImplemented,
    'date-day-monthname-year-en': dateDayMonthYearEN,
    'date-day-monthname-year-es': notImplemented,
    'date-day-monthname-year-et': notImplemented,
    'date-day-monthname-year-fi': notImplemented,
    'date-day-monthname-year-fr': notImplemented,
    'date-day-monthname-year-hi': notImplemented,
    'date-day-monthname-year-hr': notImplemented,
    'date-day-monthname-year-it': notImplemented,
    'date-day-monthname-year-nl': notImplemented,
    'date-day-monthname-year-no': notImplemented,
    'date-day-monthname-year-pl': notImplemented,
    'date-day-monthname-year-pt': notImplemented,
    'date-day-monthname-year-ro': notImplemented,
    'date-day-monthname-year-sk': notImplemented,
    'date-day-monthname-year-sl': notImplemented,
    'date-day-monthname-year-sv': notImplemented,
    'date-day-monthroman': notImplemented,
    'date-day-monthroman-year': notImplemented,
    'date-ind-day-monthname-year-hi': notImplemented,
    'date-jpn-era-year-month': notImplemented,
    'date-jpn-era-year-month-day': notImplemented,
    'date-month-day': dateMonthDay,
    'date-month-day-year': dateMonthDayYear,
    'date-month-year': dateMonthYear,
    'date-monthname-day-en': dateMonthDayEN,
    'date-monthname-day-hu': notImplemented,
    'date-monthname-day-lt': notImplemented,
    'date-monthname-day-year-en': dateMonthDayYearEN,
    'date-monthname-year-bg': notImplemented,
    'date-monthname-year-cs': notImplemented,
    'date-monthname-year-da': notImplemented,
    'date-monthname-year-de': notImplemented,
    'date-monthname-year-el': notImplemented,
    'date-monthname-year-en': notImplemented,
    'date-monthname-year-es': notImplemented,
    'date-monthname-year-et': notImplemented,
    'date-monthname-year-fi': notImplemented,
    'date-monthname-year-fr': notImplemented,
    'date-monthname-year-hi': notImplemented,
    'date-monthname-year-hr': notImplemented,
    'date-monthname-year-it': notImplemented,
    'date-monthname-year-nl': notImplemented,
    'date-monthname-year-no': notImplemented,
    'date-monthname-year-pl': notImplemented,
    'date-monthname-year-pt': notImplemented,
    'date-monthname-year-ro': notImplemented,
    'date-monthname-year-sk': notImplemented,
    'date-monthname-year-sl': notImplemented,
    'date-monthname-year-sv': notImplemented,
    'date-monthroman-year': notImplemented,
    'date-year-day-monthname-lv': notImplemented,
    'date-year-month': dateYearMonth,
    'date-year-month-day': dateYearMonthDay,
    'date-year-monthname-day-hu': notImplemented,
    'date-year-monthname-day-lt': notImplemented,
    'date-year-monthname-en': dateYearMonthEN,
    'date-year-monthname-hu': notImplemented,
    'date-year-monthname-lt': notImplemented,
    'date-year-monthname-lv': notImplemented,
    'fixed-empty': lambda arg: '',
    'fixed-false': lambda arg: 'false',
    'fixed-true': lambda arg: 'true',
    'fixed-zero': lambda arg: '0',
    'num-comma-decimal': numCommaDecimal,
    'num-dot-decimal': numDotDecimal,
    'num-unit-decimal': notImplemented,
}

# As defined in https://www.sec.gov/info/edgar/specifications/edgarfm-vol2-v59.pdf
ixt_sec = {
    'duryear': notImplemented,
    'durmonth': notImplemented,
    'durweek': notImplemented,
    'durday': notImplemented,
    'durhour': notImplemented,
    'durwordsen': durWordSen,
    'numwordsen': numWordSen,
    'datequarterend': notImplemented,
    'boolballotbox': ballotBox,
    'exchnameen': exchnameen,
    'stateprovnameen': notImplemented,
    'countrynameen': notImplemented,
    'edgarprovcountryen': notImplemented,
    'entityfilercategoryen': notImplemented,
}


def normalize(namespace: str, formatCode: str, value: str) -> str:
    value = value.strip().lower()

    try:
        if namespace == 'http://www.xbrl.org/inlineXBRL/transformation/2015-02-26':
            return ixt3[formatCode](value)
        elif namespace == 'http://www.xbrl.org/inlineXBRL/transformation/2020-02-12':
            return ixt4[formatCode](value)
        elif namespace == 'http://www.sec.gov/inlineXBRL/transformation/2015-08-31':
            return ixt_sec[formatCode](value)
        else:
            raise RegistryNotSupported(namespace)
    except KeyError:
        raise InvalidTransformation(namespace, formatCode)
    except TransformationNotImplemented:
        msg = f'The transformation "{formatCode}" rule of registry {namespace} is currently not implemented in py-xbrl'
        raise TransformationNotImplemented(msg)


if __name__ == '__main__':
    print(normalize(
        'http://www.sec.gov/inlineXBRL/transformation/2015-08-31',
        'numwordsen',
        'one million and two'
    ))
