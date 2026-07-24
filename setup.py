# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午2:31
# @Author  : fzf
# @FileName: setup.py
# @Software: PyCharm
from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
readme_md = this_directory / "README.md"
readme_rst = this_directory / "README.rst"
if readme_md.exists():
    long_description = readme_md.read_text(encoding="utf-8")
    long_description_content_type = "text/markdown"
elif readme_rst.exists():
    long_description = readme_rst.read_text(encoding="utf-8")
    long_description_content_type = "text/x-rst"
else:
    long_description = "DRF-style generic CRUD for FastAPI (Tortoise ORM / SQLAlchemy)"
    long_description_content_type = "text/plain"

setup(
    name="fast_generic_api",
    version="1.0.1",
    packages=find_packages(exclude=["venv", "venv.*", ".venv", ".venv.*", "fast_generic_api.example", "fast_generic_api.example.*"]),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.100",
        "tortoise-orm>=0.20",
        "pydantic>=2.0",
        "uvicorn>=0.20",
        "watchfiles",
    ],
    extras_require={
        "sqlalchemy": [
            "sqlalchemy[asyncio]>=2.0",
            "aiosqlite",
        ],
        "test": [
            "httpx",
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "sqlalchemy[asyncio]>=2.0",
            "aiosqlite",
        ],
    },
    tests_require=["pytest", "pytest-asyncio", "pytest-cov", "sqlalchemy[asyncio]>=2.0", "aiosqlite"],
    author="fzf",
    description="DRF-style generic CRUD for FastAPI (Tortoise ORM / SQLAlchemy)",
    long_description=long_description,
    long_description_content_type=long_description_content_type,
    url="https://github.com/fzf54122/fast_generic_api",
    classifiers=[
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
)

