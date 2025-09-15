from setuptools import setup, find_packages

setup(
    name="racerctl",
    version="0.1.0",
    description="Rapid deployment system for conda-projects - CLI tools",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "racer=racer_cli:cli",
            "racerctl=cli:cli",
        ],
    },
    install_requires=[
        "click==8.2.1",
        "requests==2.32.5",
        "docker==7.1.0",
        "gitpython==3.1.45",
        "pyyaml==6.0.2",
    ],
    python_requires=">=3.8",
)