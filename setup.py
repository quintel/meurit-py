from setuptools import find_packages, setup

# Add Ruby requirements or bin/setup kind of executable to this

setup(
    name='meurit',
    package_dir={'': 'src', 'vendor.rython': 'vendor'},
    packages=find_packages(where='src') + ['vendor.rython'],
)
