from distutils.core import setup
import sys
import airbrake

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

setup(
    name='django-airbrake',
    version=airbrake.__version__,
    author='Bouke Haarsma',
    author_email='bouke@webatoom.nl',
    packages=[
        'airbrake',
    ],
    url='http://github.com/Bouke/django-airbrake',
    description='Airbrake exception logger for django',
    license='MIT',
    long_description=open('README.rst').read(),
    install_requires=[
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: System :: Logging',
    ],
    **extra
)
