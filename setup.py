from setuptools import setup, find_packages

setup(
    name="drinks_storage",
    packages=find_packages(),
    scripts=['bin/drinks_storage_mqtt'],
)
