from setuptools import setup, find_packages

from middlewarecheck import __version__ as version

name = "middlewarecheck"

setup(
    name = name,
    version = version,
    author = "Richard (Rick) Hawkins",
    author_email = "hurricanerix@gmail.com",
    description = "MiddlewareCheck",
    license = "Apache License, (2.0)",
    keywords = "openstack swift middleware",
    url = "https://github.com/hurricanerix/swift-middlewarecheck",
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Environment :: No Input/Output (Daemon)',
        ],
    install_requires=[],
    entry_points={
        'paste.filter_factory': [
            'middlewarecheck=middlewarecheck.middleware:filter_factory',
            ],
        },
    )
