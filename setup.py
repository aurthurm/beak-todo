from setuptools import find_packages, setup

setup(
    name="felicity-todos",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.7.0",
        "colorama>=0.4.4",
        "tabulate>=0.8.9",
        "rich>=13.0.0",
        "python-dateutil>=2.8.2",
        "litellm>=1.0.0",
        "pydantic>=2.0.0",
        "tomli>=2.0.0; python_version < '3.11'",
        "tomli-w>=1.0.0",
    ],
    entry_points="""
        [console_scripts]
        t=src.main:app
    """,
    author="Felicity Todos Team",
    author_email="example@example.com",
    description="A CLI for managing todos with optional AI features",
    keywords="todo, cli, productivity, ai",
    url="https://github.com/example/felicity-todos",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
)
