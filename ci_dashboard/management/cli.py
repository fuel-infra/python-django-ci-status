#!/usr/bin/env python

# This file is slightly modified copy of manage.py used by entry_points in setuptools
# entry_points = {
#     'console_scripts': [
#         'ci-status=ci_dashboard.management.cli'
#     ]
# }
import sys


def main():
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
