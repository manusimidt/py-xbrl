"""
Module containing functions for creating and resolving uri's
"""


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
    # this is just for convenience, if the dir_url is not a link to a directory but to a file in a directory.
    if '.' in dir_uri.split('/')[-1]:
        # remove the last part, because it is the file_name with extension
        dir_uri = '/'.join(dir_uri.split('/')[0:-1])
    if not dir_uri.endswith('/'):
        dir_uri += '/'

    if relative_uri.startswith('/'):
        relative_uri = relative_uri[1:]
    if relative_uri.startswith('./'):
        relative_uri = relative_uri[2:]

    absolute_uri = dir_uri + relative_uri
    path_parts = absolute_uri.split('/')
    for x in range(0, absolute_uri.count('/..')):
        # loop over the path_parts array and remove the path_part, that has a '..' after it
        for y in range(0, len(path_parts) - 1):
            if path_parts[y + 1] == '..':
                del path_parts[y]  # delete the path part affected by the '/../'
                del path_parts[y]  # delete the '/../' itself
                break
    return '/'.join(path_parts)


