import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="topican",
    version="0.0.11",
    author="Richard Smith",
    author_email="randkego@gmail.com",
    description="Topic analyser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/topican",
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=(
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)