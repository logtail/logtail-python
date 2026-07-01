# coding: utf-8
import os
from setuptools import setup


VERSION = '0.4.0'
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
    description='Better Stack client library',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/logtail/logtail-python',
    download_url='https://github.com/logtail/logtail-python/tarball/%s' % (VERSION),
    keywords=['api', 'logtail', 'logging', 'client'],
    install_requires=REQUIREMENTS,
    python_requires='>=3.10',
    author='Logtail',
    author_email='hello@logtail.com',
    classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: ISC License (ISCL)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Programming Language :: Python :: 3.12',
          'Programming Language :: Python :: 3.13',
          'Programming Language :: Python :: 3.14',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
