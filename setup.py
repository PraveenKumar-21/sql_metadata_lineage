import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sql_metadata_lineage",
    version="0.0.1",
    author="Praveen Kumar B",
    author_email="bpraveenkumar21@gmail.com",
    description="Package to get SQL query metadata(first level lineage), column -> database.table.actual_column mapping along with table alias mapping(alias -> database.table)",
    keywords = ['SQL metadata', 'SQL parse metadata', 'Metadata lineage for SQL', 'SQL Lineage'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/PraveenKumar-21/sql_metadata_lineage",
    packages=setuptools.find_packages(),
    install_requires=[
        'sqlparse',
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)