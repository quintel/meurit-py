from setuptools import find_packages, setup


setup(
    name='meurit',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
)
