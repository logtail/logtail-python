# coding: utf-8
import os
from setuptools import setup


VERSION = '0.1.3'
ROOT_DIR = os.path.dirname(__file__)

REQUIREMENTS = [
    line.strip() for line in
    open(os.path.join(ROOT_DIR, 'requirements.txt')).readlines()
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='logtail-python',
    version=VERSION,
    packages=['logtail'],
    include_package_data=True,
    license='ISC',
    description='Logtail.com client library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/logtail/logtail-python',
    download_url='https://github.com/logtail/logtail-python/tarball/%s' % (VERSION),
    keywords=['api', 'logtail', 'logging', 'client'],
    install_requires=REQUIREMENTS,
    author='Logtail',
    author_email='hello@logtail.com',
    classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: ISC License (ISCL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
