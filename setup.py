from distutils.core import setup
from setuptools import find_packages

import airbrake

setup(
    name='django-airbrake',
    version=airbrake.__version__,
    author='Bouke Haarsma',
    author_email='bouke@haarsma.eu',
    packages=find_packages(exclude=('tests',)),
    url='http://github.com/Bouke/django-airbrake',
    description='Airbrake exception logger for Django',
    license='MIT',
    long_description=open('README.rst').read(),
    install_requires=['Django>=1.11'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Logging',
    ],
)
