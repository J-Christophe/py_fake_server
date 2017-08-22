import codecs
import re

import os
from setuptools import (
    setup,
    find_packages,
)


def read(*parts):
    path = os.path.join(os.path.dirname(__file__), *parts)
    with codecs.open(path, encoding='utf-8') as fobj:
        return fobj.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


requires = [
    "WebTest==2.0.28",
    "falcon==1.2.0",
    "falcon-multipart==0.2.0",
]

tests_require = [
    "pytest==3.2.1",
    "requests==2.18.4"
]

setup(
    name="py_fake_server",
    version=find_version("py_fake_server", "__init__.py"),
    description="Make fake servers with pleasure!",
    url="https://github.com/Telichkin/py_fake_server",
    author="Roman Telichkin",
    author_email="roman@telichk.in",
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    install_requires=requires,
    tests_require=tests_require,
    setup_requires=["pytest-runner"],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
