"""
Module containing functions for creating and resolving uri's
"""
import os
import re

# precompiled for speed https://stackoverflow.com/questions/1276764/stripping-everything-but-alphanumeric-chars-from-a-string-in-python
pattern = re.compile('[\W]+')

def resolve_uri(dir_uri: str, relative_uri: str) -> str:
    """
    Returns a complete absolute uri.
    i.e
    dir_uri is 'http://abc.org/a/b/c'
    relative_uri: '/../lab.xml'
        the function would resolve the absolute uri to: http://abc.org/a/c/lab.xml

    if the relative_uri is already absolute, the function will just return the relative_url
    @param dir_uri:
    @param relative_uri:
    @return:
    """
    if relative_uri.startswith('http'):
        return relative_uri

    # remove redundant characters in the relative uri
    if relative_uri.startswith('/'): relative_uri = relative_uri[1:]
    if relative_uri.startswith('./'): relative_uri = relative_uri[2:]

    if not dir_uri.startswith('http'):
        # check if the dir_uri was really a path to a directory or a file
        if '.' in dir_uri.split(os.sep)[-1]:
            return os.path.normpath(os.path.dirname(dir_uri) + os.sep + relative_uri)
        else:
            return os.path.normpath(dir_uri + os.sep + relative_uri)

    # === From here on we only process urls ===
    # remove the file name if the dir_uri was the url to a file
    if '.' in dir_uri.split('/')[-1]: dir_uri = '/'.join(dir_uri.split('/')[0:-1])
    if not dir_uri.endswith('/'):
        dir_uri += '/'

    absolute_uri = dir_uri + relative_uri
    if not dir_uri.startswith('http'):
        # make sure the path is correct
        absolute_uri = os.path.normpath(absolute_uri)

    url_parts = absolute_uri.split('/')
    for x in range(0, absolute_uri.count('/..')):
        # loop over the url_parts array and remove the path_part, that has a '..' after it
        for y in range(0, len(url_parts) - 1):
            if url_parts[y + 1] == '..':
                del url_parts[y]  # delete the path part affected by the '/../'
                del url_parts[y]  # delete the '/../' itself
                break

    return '/'.join(url_parts)

def normalise_uri(uri: str) -> str:
    """ drop protocol from uri, and any non a-z chars for easy comparison """
    return pattern.sub('', uri.split('://')[-1])

def normalise_uri_dict(dict_in: dict) -> dict:
    for k,v in dict_in.copy().items():
        dict_in[normalise_uri(k)] = dict_in.pop(k)
    return dict_in

def compare_uri(uri1: str, uri2: str) -> bool:
    """
    Compares two uri's and returns true if they are considered equal and false if not.
    Examples:
        - uri1: http://abc.de/2020, uri2: https://abc.de/2020 -> True
        - uri1: ./abc.de/2020, uri2: abc.de\\2020 -> True
        - uri1: /abc.de/2020, uri2: /abc/2020 -> False
    :param uri1:
    :param uri2:
    :return:
    """
    return normalise_uri(uri1) == normalise_uri(uri2)
