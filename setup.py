from setuptools import find_packages, setup

setup(
    name="disk-overview",
    version="0.2.0",
    description="Storage device visualization and management tool for Linux",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Disk Overview Team",
    author_email="",
    url="https://github.com/aminadal/disk-overview",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "disk_overview": [
            "../config/*.json",
            "../data/*.css",
            "../data/*.desktop",
            "../data/icons/*.png",
        ],
    },
    data_files=[
        ("share/applications", ["data/disk-overview.desktop"]),
        ("share/disk-overview/config", ["config/default_config.json"]),
        ("share/disk-overview/data", ["data/styles.css"]),
        ("share/disk-overview/data/icons", ["data/icons/hdd.png"]),
    ],
    install_requires=[
        "PyGObject>=3.42.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "tray": [],  # AppIndicator3 é dependência de sistema
    },
    entry_points={
        "console_scripts": [
            "disk-overview=disk_overview.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment :: File Managers",
        "Topic :: System :: Filesystems",
    ],
    python_requires=">=3.10",
)
