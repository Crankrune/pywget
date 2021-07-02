from sys import platform
from setuptools import find_packages, setup

setup(
    name="pywget",
    version="1.2.2",
    packages=["pywget"],
    # package_data={"scrapers": ["superscraper/scrapers/*.scraper"]},
    install_requires=["click", "python-dateutil", "pytz", "regex", "requests", "tqdm"],
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["pywget=pywget:cli_pywget"]},
    python_requires=">=3.9",
    options={"bdist_wheel": {"python_tag": "py39"}},
    platforms=["win"],
)
