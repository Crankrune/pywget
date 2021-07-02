from setuptools import setup

setup(
    name="pywget",
    version="1.2.4",
    packages=["pywget"],
    install_requires=[
        "click>=8.0",
        "python-dateutil>=2.8",
        "requests>=2.25",
        "tqdm>=4.5",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["pywget=pywget:cli_pywget"]},
    # python_requires=">=3.8",
    # options={"bdist_wheel": {"python_tag": "py38"}},
    platforms=["win"],
)
