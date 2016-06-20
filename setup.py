#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.install import install

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


class CustomInstall(install):
    def run(self):
        os.environ['HOME'] = '/tmp'

        subprocess.check_call(['npm', 'install'])
        subprocess.check_call([
            './node_modules/bower/bin/bower',
            'install',
            '--allow-root',
            '--config.interactive=false'
        ])
        subprocess.check_call(
            ['./node_modules/gulp/bin/gulp.js', 'build_static']
        )

        install.run(self)


setup(
    name='python-django-ci_status',
    version='0.0.1',
    packages=find_packages(exclude=['ci_dashboard.tests', 'ci_dashboard.tests.*']),
    package_data={
        'ci_dashboard': [
            'templates/*.html',
            'templates/ci_dashboard/*.html',
            'static/ci_dashboard/javascripts/*.min.js',
            'static/ci_dashboard/stylesheets/*.min.css',
        ]
    },
    cmdclass={'install': CustomInstall},
    license='Apache License 2.0',
    description='Web application for CI system health and status tracking.',
    long_description=README,
    url='https://review.fuel-infra.org/#/admin/projects/fuel-infra/packages/python-django-ci-status',  # noqa
    author='Aliaksandr Buhayeu',
    author_email='abuhayeu@mirantis.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Utilities',
        'Framework :: Django',
    ],
)
