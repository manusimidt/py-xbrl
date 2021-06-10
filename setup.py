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
    version="2.0.2",
    url="https://github.com/manusimidt/xbrl_parser",
    license='GNU General Public License v3 (GPLv3)',
    author="Manuel Schmidt",
    author_email="hello@schmidt-manuel.de",

    description="Parser for parsing XBRL and iXBRL files (instance documents, taxonomy schemas, taxonomy linkbases).",
    long_description_content_type="text/markdown",
    long_description=read("README.md"),
    packages=find_packages(exclude=('tests', 'cache', 'workdir')),

    install_requires=["requests", "urllib3"],

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Natural Language :: English',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Text Processing :: Markup',
        'Topic :: Text Processing :: Markup :: XML'
    ],
)
