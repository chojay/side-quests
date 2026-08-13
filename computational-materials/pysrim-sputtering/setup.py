"""
Setup script for pySRIM simulation package.
"""
from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="pysrim",
    version="0.1.0",
    author="pySRIM contributors",
    description="SRIM/TRIM sputtering simulations for optical thin films (ITO, TiO2, SiO2)",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.2.0",
            "pytest-cov>=3.0.0",
            "black>=21.0",
            "flake8>=3.9.0",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["config/*.yaml", "config/sweep_configs/*.yaml"],
    },
)
