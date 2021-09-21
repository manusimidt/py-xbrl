import logging
import re
from time import strptime
from xbrl.helper.text2num import text2num, NumberException


class TransformationException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)


def transform_ixt(value: str, transform_format: str) -> str:
    """
    Takes a transformed value and returns a normalized value.
    The transformation rules are listed here:
    https://www.xbrl.org/Specification/inlineXBRL-transformationRegistry/REC-2015-02-26/inlineXBRL-transformationRegistry-REC-2015-02-26.html#d1e167

    In short: this function will perform the following normalizations:
    - Numbers: float value with a dot (.) as fraction separator. All thousands separators will be removed
    - Full Date: YYYY-DD-MM
    - Month-Day: --MM-DD
    - Year-Month: YYYY-MM
    - boolean: "true" or "false"
    :param value: the raw text value
    :param transform_format: the transformation format
    :return:
    """
    value = value.lower().strip().replace(u'\xa0', u' ')

    if transform_format == 'booleanfalse':
        # * -> false
        return 'false'

    elif transform_format == 'booleantrue':
        # * -> true
        return 'true'

    elif transform_format == 'zerodash':
        # - -> 0
        return '0'

    elif transform_format == 'nocontent':
        # any string -> ''
        return ''

    elif transform_format.startswith('date'):
        # replace dashes, dots etc. (Dec. 2021 -> Dec  2021)
        value = re.sub(r'[,\-\._/]', ' ', value)
        # remove unnecessary spaces (Dec  2021 -> Dec 2021)
        value = re.sub(r'\s{2,}', ' ', value)
        seg = value.split(' ')

        if transform_format == 'datedaymonth':
            # (D)D*(M)M -> --MM-DD
            return f"--{seg[1].zfill(2)}-{seg[0].zfill(2)}"

        elif transform_format == 'datedaymonthen':
            # (D)D*Mon(th) -> --MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]}', '%d %b') if len(seg[1]) == 3 \
                else strptime(f'{seg[0]} {seg[1]}', '%d %B')
            return f'--{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}'

        elif transform_format == 'datedaymonthyear':
            # (D)D*(M)M*(Y)Y(YY) -> YYYY-MM-DD
            return f"{seg[2].zfill(2)}-{seg[1].zfill(2)}-{seg[0].zfill(2)}"

        elif transform_format == 'datedaymonthyearen':
            # (D)D*Mon(th)*(Y)Y(YY) -> YYYY-MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%d %b %Y') if len(seg[1]) == 3 \
                else strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%d %B %Y')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}"

        elif transform_format == 'datemonthday':
            # (M)M*(D)D -> --MM-DD
            return f"--{seg[0].zfill(2)}-{seg[1].zfill(2)}"

        elif transform_format == 'datemonthdayen':
            # Mon(th)*(D)D -> --MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]}', '%b %d') if len(seg[0]) == 3 \
                else strptime(f'{seg[0]} {seg[1]}', '%B %d')
            return f'--{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}'

        elif transform_format == 'datemonthdayyear':
            # (M)M*(D)D*(Y)Y(YY) -> YYYY-MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%m %d %Y')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}"

        elif transform_format == 'datemonthdayyearen':
            # Mon(th)*(D)D*(Y)Y(YY) -> YYYY-MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%b %d %Y') if len(seg[0]) <= 3 \
                else strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%B %d %Y')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}"

        elif transform_format == 'dateyearmonthday':
            # (Y)Y(YY)*(M)M*(D)D -> YYYY-MM-DD
            parsed_date = strptime(f'{seg[0]} {seg[1]} {seg[2]}', '%Y %m %d')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}-{str(parsed_date.tm_mday).zfill(2)}"

        elif transform_format == 'datemonthyear':
            # (M)M*(Y)Y(YY) -> YYYY-MM
            return f"{seg[1]}-{seg[0].zfill(2)}"

        elif transform_format == 'datemonthyearen':
            # Mon(th)*(Y)Y(YY) -> YYYY-MM
            parsed_date = strptime(f'{seg[0]} {seg[1]}', '%B %Y')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}"

        elif transform_format == 'dateyearmonthen':
            # (Y)Y(YY)*Mon(th) -> YYYY-MM
            parsed_date = strptime(f'{seg[0]} {seg[1]}', '%Y %B')
            return f"{parsed_date.tm_year}-{str(parsed_date.tm_mon).zfill(2)}"

    elif transform_format.startswith('num'):
        if transform_format == 'numcommadecimal':
            # nnn*nnn*nnn,n -> nnnnnnnnn.n
            value = re.sub(r'(\s|-|\.)', '', value)
            return value.replace(',', '.')
        if transform_format == 'numdotdecimal':
            # nnn*nnn*nnn.n -> nnnnnnnnn.n
            return re.sub(r'(\s|-|,)', '', value)

    raise TransformationException('Unknown fact transformation {}'.format(transform_format))


def transform_ixt_sec(value: str, transform_format: str) -> str:
    """
    Transforms the value according to the SEC Transformation rules
    https://www.sec.gov/info/edgar/edgarfm-vol2-v50.pdf
    https://www.sec.gov/info/edgar/specifications/edgarfm-vol2-v51_d.pdf
    :param value:
    :param transform_format:
    :return:
    """

    value = value.lower().strip().replace(u'\xa0', u' ')

    # replace dashes, dots etc. (Dec. 2021 -> Dec  2021)
    value = re.sub(r'[,\-\._/]', ' ', value)
    # remove unnecessary spaces (Dec  2021 -> Dec 2021)
    value = re.sub(r'\s{2,}', ' ', value)

    if transform_format == 'numwordsen':
        if value == 'no' or value == 'none':
            return '0'
        else:
            value = value.replace(' and ', ' ')
            return str(text2num(value))
    elif transform_format == 'boolballotbox':
        if value == '☐':
            return 'false'
        else:
            return 'true'
    elif transform_format == 'durwordsen':
        value = replace_text_numbers(value)
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

    # raise TransformationException('Unknown fact transformation {}'.format(transform_format))
    logging.info(f"The transformation rule ixt-sec:{transform_format} is currently not supported by this parser. "
                 f"The value for the fact will not be transformed")
    return value


def replace_text_numbers(text: str) -> str:
    """
    Takes a string like "Five years two months" and replaces each number in the text with the corresponding numeral.
    => "5 years 2 months
    :param text:
    :return:
    """
    text = text.lower().strip().replace(u'\xa0', u' ')
    word_arr = text.split(' ')
    for x in range(len(word_arr)):
        try:
            word_arr[x] = str(text2num(word_arr[x]))
        except NumberException:
            continue
    return ' '.join(word_arr)
