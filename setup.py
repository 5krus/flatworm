from setuptools import setup, find_packages
import codecs
import os

here = os.path.abspath(os.path.dirname(__file__))

with codecs.open(os.path.join(here, "README.md"), encoding="utf-8") as fh:
    long_description = "\n" + fh.read()

VERSION = '0.1.2'
DESCRIPTION = 'Tools designed for non-techy people who must write code.'
LONG_DESCRIPTION = 'A set of packages with eye-wateringly minimalistic user interfaces, but extremely powerful and performant backends.'

# Setting up
setup(
    name="flatworm",
    version=VERSION,
    author="Eryk Krusinski",
    author_email="<eryk@krus.co.uk>",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=['joblib', 'pandas', 'numpy', 'scikit-learn'],
    keywords=['python', 'machine learning', 'version control', 'minimalism'],
    classifiers=[
    ]
)
