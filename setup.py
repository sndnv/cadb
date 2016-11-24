"""Simple C++ build automation tool.

See:
https://github.com/sndnv/cadb
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='cadb',
    version='1.0.0',
    description='Simple C++ build automation tool',
    long_description=long_description,
    url='https://github.com/sndnv/cadb',
    author='https://github.com/sndnv',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools'
    ],
    keywords='cpp c++ build compile automation',
    packages=find_packages(),
    entry_points={
        'console_scripts': ['cadb=cadb.__main__:main']
    }
)
