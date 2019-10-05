from setuptools import setup, find_packages

setup(
    name="ScarpAPI",
    version="1",
    packages = find_packages(),
    entry_points={'scrapy': ['settings = scrapy_car.settings']}
)

