#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import io
import re
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_namespace_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ) as fh:
        return fh.read()


setup(
    name='evision-lib',
    version='0.2.1',
    description='eVision Common Python Library',
    long_description='%s\n%s' % (
        re.compile('^.. start-badges.*^.. end-badges', re.M | re.S).sub('', read('README.rst')),
        re.sub(':[a-z]+:`~?(.*?)`', r'``\1``', read('CHANGELOG.rst'))
    ),
    long_description_content_type='text/x-rst',
    author='eVision.AI',
    author_email='lib@evision.ai',
    url='https://github.com/evision-ai/evision-lib',
    packages=find_namespace_packages('src', include=['evision.*'],
                                     exclude=['ez_setup', 'tests', 'tests.*']),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    license="GPLv3",
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Software Development :: Libraries :: Python Modules',
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    project_urls={
        'Documentation': 'https://evision-lib.readthedocs.io/',
        'Changelog': 'https://evision-lib.readthedocs.io/en/latest/changelog.html',
        'Issue Tracker': 'https://github.com/dectinc/evision-lib/issues',
    },
    keywords=[
        'evision', 'library', 'computer vision', 'rtsp'
    ],
    python_requires='!=2.*, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, !=3.5.*',
    install_requires=[
        'tornado>=5.0.0',
        'opencv-python',
        'numpy>=1.11.0',
        'fields',
        'pydantic>=1.0',
        'walrus'
    ],
    extras_require={
        'tornado': [
            'webargs>=5.5.1',
        ],
        'db': [
            'peewee>=3.0.0',
        ],
        'rst': [
            'docutils>=0.11',
        ],
        'extras': [
            'setproctitle',
        ]
    },
    setup_requires=[
        'pytest',
        'pytest-runner',
    ],
    entry_points={
    },
)
