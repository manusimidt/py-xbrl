[![PyPI](https://img.shields.io/pypi/v/py-xbrl)](https://pypi.org/project/py-xbrl/#history)
[![PyPI - Status](https://img.shields.io/pypi/status/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![GitHub](https://img.shields.io/github/license/manusimidt/xbrl_parser)](https://github.com/manusimidt/xbrl_parser/blob/main/LICENSE)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/py-xbrl)](https://pypi.org/project/py-xbrl/)
[![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/manusimidt/xbrl_parser)](https://github.com/m4nu3l99/xbrl_parser)

## XBRL-Parser

Py-xbrl is a python library that allows the user to easily parse XBRL-Documents. Py-xbrl is primarily build 
to parse Instance Documents (originally from the SEC) but can also be used to parse any type of XBRL 
Document as long as it follows the XBRL 2.1 Specification (2003)[^1] or the iXBRL 1.1 Specification(2013)[^2].

XBRL is a very information-rich markup language that can have highly complex structures. This library tries to capture
as much of the original information as possible. Py-xbrl will automatically download and parse all referenced XBRL-Files
like taxonomy schemas and linkbases. After parsing py-xbrl will organize all information in an object structure and 
return it to the user.

Please read the documentation for more information and examples!:
https://py-xbrl.readthedocs.io

[^1]: https://www.xbrl.org/Specification/XBRL-2.1/REC-2003-12-31/XBRL-2.1-REC-2003-12-31+corrected-errata-2013-02-20.html
[^2]: https://www.xbrl.org/specification/inlinexbrl-part1/rec-2013-11-18/inlinexbrl-part1-rec-2013-11-18.html

## Installation
Py-xbrl can be installed via PIP:
```bash
pip install py-xbrl
```
see the [documentation](https://py-xbrl.readthedocs.io/en/latest/) for more info.

## Questions
If you have questions regarding the library please post them into
the [GitHub discussion forum](https://github.com/manusimidt/py-xbrl/discussions).

## Contributing
I am always happy to receive contributions. You can either work on 
an already created issue or create a new pull request. You can also create a pull request
if you want to propose a change to the documentation on readthedocs.io. 
Please keep in mind that the goal of this library is to parse XBRL files correctly. Therefore, it is important
that the unit tests work on any pull request. Additionally, py-xbrl should still be able to parse all 
xbrl files correctly. It is best to create a discussion in the GitHub discussion board before creating the pull request 
to avoid that a lot of work is done, but the pull request is not merged in the end. 