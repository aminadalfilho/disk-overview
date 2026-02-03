from setuptools import find_packages, setup

setup(
    name="disk-overview",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["PyGObject>=3.42.0", "psutil>=5.9.0"],
    entry_points={"console_scripts": ["disk-overview=disk_overview.main:main"]},
)
