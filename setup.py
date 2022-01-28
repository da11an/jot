from setuptools import setup, find_packages
from pathlib import Path

requirements = []

__version__ = "0.0.0"


setup(
    name="jot",
    version=__version__,
    packages=find_packages(),
    license="GNU GPL 3.0",
    author="Dallan Prince",
    author_email="dallan.prince@gmail.com",
    url="https://github.com/da11an/jot",
    install_requires=requirements,
    python_requires=">=3.6, <4",
    description="Command line task management",
    include_package_data=True,
    entry_points={
        "console_scripts": ["jot=jot:main"]
    },
)
