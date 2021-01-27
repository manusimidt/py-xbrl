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
    name="xbrl_parser",
    version="0.0.1",
    url="https://github.com/manusimidt/xbrl_parser",
    license='MIT',
    author="Manuel Schmidt",
    author_email="hello@schmidt-manuel.de",

    description="This parser can parse XBRL documents",
    long_description=read("README.md"),
    packages=find_packages(exclude=('tests',)),

    install_requires=["requests", ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
