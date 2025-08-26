import codecs
import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

setup(
    name="thsdk",
    version="1.5.6",
    description="THSDK",
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=["thsdk"],
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[],
    keywords=['thsdk'],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    package_data={
        'thsdk': ['*', 'examples/*', "libs/darwin/*", "libs/linux/*", "libs/windows/*"],
    },
)
