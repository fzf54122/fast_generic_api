# -*- coding: utf-8 -*-
# @Time    : 2025/12/8 下午12:31
# @Author  : fzf
# @FileName: __init__.py
# @Software: PyCharm
r"""
Fast Generic API — FastAPI 版 DRF 风格通用 CRUD 框架。

支持 Tortoise ORM（默认）与 SQLAlchemy 2.x async（可选）。
"""

__title__ = "fast_generic_api"
__version__ = "0.2.0"
__author__ = "fzf"
__license__ = "MIT"
__copyright__ = "Copyright 2025 fzf"

VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = "iso-8859-1"

# Default datetime input and output formats
ISO_8601 = "iso-8601"
