#!/usr/bin/env python
# emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See LICENSE file distributed along with the dandischema package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Build helper."""

import sys

from setuptools import setup

if sys.version_info < (3,):
    raise RuntimeError(
        "dandischema's setup.py requires python 3 or later. "
        "You are using %s" % sys.version
    )

# Give setuptools a hint to complain if it's too old a version
# Should match pyproject.toml
SETUP_REQUIRES = ["setuptools >= 42.0.0", "versioningit ~= 0.1.0"]
# This enables setuptools to install wheel on-the-fly
SETUP_REQUIRES += ["wheel"] if "bdist_wheel" in sys.argv else []

if __name__ == "__main__":
    setup(name="dandischema", setup_requires=SETUP_REQUIRES)
