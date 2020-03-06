import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="py3lite",
    version="0.1.0",
    author="Dr. Abiira Nathan",
    author_email="nabiira2by2@gmail.com",
    description="Light weight sqlite3 ORM for humans",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abiiranathan/py3lite",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[],
)
