import io
import os
import re

from setuptools import find_packages
from setuptools import setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(text_type(r':[a-z]+:`~?(.*?)`'), text_type(r'``\1``'), fd.read())


setup(
    name="py-xbrl",
    version="2.2.17",
    url="https://github.com/manusimidt/xbrl_parser",
    license='GNU General Public License v3 (GPLv3)',
    author="Manuel Schmidt",
    author_email="hello@schmidt-manuel.de",

    description="Parser for parsing XBRL and iXBRL files (instance documents, taxonomy schemas, taxonomy linkbases).",
    long_description_content_type="text/markdown",
    long_description=read("README.md"),
    packages=find_packages(exclude=('tests', 'cache', 'workdir')),

    install_requires=[
        "requests",  # needed for fetching xml files from the internet
        "urllib3"  # needed for http retries
    ],

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
        'Natural Language :: English',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
        'Topic :: Text Processing :: Markup :: XML'
    ],
)
