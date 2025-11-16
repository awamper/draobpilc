#!/usr/bin/env python3
from setuptools import setup

# All configuration is now in pyproject.toml
setup(
    data_files=[
        ('share/applications', ['draobpilc/data/draobpilc.desktop', 'draobpilc/data/draobpilc-preferences.desktop']),
        ('share/icons/hicolor/scalable/apps', ['draobpilc/data/draobpilc.png']),
    ]
)