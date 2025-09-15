from setuptools import setup, find_packages

setup(
    name="racerctl",
    version="0.1.0",
    description="Rapid deployment system for conda-projects",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "racer=client.racer_cli:cli",
            "racerctl=client.cli:cli",
        ],
    },
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        "click==8.2.1",
        "requests==2.32.5",
        "docker==7.1.0",
        "gitpython==3.1.45",
        "pyyaml==6.0.2",
        "sqlalchemy==2.0.23",
        "alembic==1.13.1",
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
    ],
    python_requires=">=3.8",
)
