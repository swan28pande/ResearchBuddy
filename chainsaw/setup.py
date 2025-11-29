from setuptools import setup, find_packages

setup(
    name="chainsaw",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0"
    ],
    python_requires=">=3.10"
)
