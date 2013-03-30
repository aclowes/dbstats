#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='dbstats',
    version='0.0.1',
    description='Database Statistics Reporting Tool',
    author='Alec Clowes',
    author_email='aclowes@gmail.com',
    url='http://www.github.com/aclowes/dbstats',
    license='MIT',
    packages=find_packages(exclude=('tests', 'dbstats_example')),
    package_data={
        'dbstats': ['dbstats/templates/*',
                    'dbstats/static/css/*',
                    'dbstats/static/img/*',
                    'dbstats/static/js/*'],
    },
    requires=[
        'pyzmq>=2.2',
        'pytz',
        'django>=1.4',
#        'django_bootstrap_forms',
        ],
    tests_require=[
        'south',
    ],
    test_suite='runtests.runtests',
    zip_safe=False, # because we're including media that Django needs
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database',
        'Topic :: System :: Monitoring',
    ],
)
