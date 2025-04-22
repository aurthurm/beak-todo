from setuptools import setup, find_packages

setup(
    name="felicity-todos",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "typer>=0.7.0",
        "colorama>=0.4.4",
        "tabulate>=0.8.9",
        "rich>=13.0.0",
        "python-dateutil>=2.8.2",
    ],
    entry_points="""
        [console_scripts]
        t=src.main:app
    """,
    author="Felicity Todos Team",
    author_email="example@example.com",
    description="A simple CLI for managing todos",
    keywords="todo, cli, productivity",
    url="https://github.com/example/felicity-todos",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)