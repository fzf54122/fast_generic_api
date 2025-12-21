#!/bin/bash


# 上传到 PyPI
python setup.py sdist bdist_wheel

twine upload dist/*
