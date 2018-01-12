from setuptools import setup, find_packages

setup(
    name="vagrant_cloud_cli",
    version="1.0.0",
    description="A CLI for Vagrant Cloud",
    url="https://github.com/Phoenix09/vagrant-cloud-cli",
    author="Phoenix09",
    author_email="Phoenix09@users.noreply.github.com",
    packages=find_packages(exclude=["contrib", "docs", "tests"]),
    install_requires=["requests", "prettytable", "python-dateutil"],
    entry_points={
        "console_scripts": [
            "vagrant-cloud-cli=vagrant_cloud_cli:main",
        ],
    },
)