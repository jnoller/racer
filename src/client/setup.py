"""
Setup script for the Racer CLI client.
"""

from setuptools import setup, find_packages

setup(
    name="racerctl",
    version="0.1.0",
    author="Racer Team",
    author_email="team@racer.dev",
    description="CLI client for the Racer deployment system",
    long_description="CLI client for the Racer deployment system for conda-projects",
    long_description_content_type="text/markdown",
    url="https://github.com/racer/racer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        "console_scripts": [
            "racer=racer_cli:cli",
            "racerctl=racerctl:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
