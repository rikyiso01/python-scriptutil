from setuptools import setup, find_packages  # type: ignore

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    author="Riccardo Isola",
    author_email="riky.isola@gmail.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    description="Utils to better use python as a scripting language",
    keywords=["script", "utils"],
    long_description=long_description,
    name="scriptutils",
    packages=find_packages(),
    version="0.1",
    project_urls={
        "Source": "https://github.com/RikyIsola/python-scriptutils",
        "Tracker": "https://github.com/RikyIsola/python-scriptutils/issues",
    },
    python_requires=">3.9",
    long_description_content_type="text/markdown",
)
