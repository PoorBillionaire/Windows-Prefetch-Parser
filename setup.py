from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='windowsprefetch',
    version='1.0.5',
    description='A Python script to parse Windows Prefetch files',
    long_description=long_description,
    url='https://github.com/PoorBillionaire/Windows-Prefetch-Parser',
    author='Adam Witt',
    author_email='accidentalassist@gmail.com',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'Topic :: Security',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7'
    ],

    keywords='DFIR Prefetch Forensics Incident Response Microsoft Windows',
    packages=find_packages(),
    scripts=['windowsprefetch/prefetch.py'],
)
