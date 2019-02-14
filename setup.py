# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from monocle import VERSION

install_requires = [
    "multidict",
    "yarl",
    "aiohttp"
]

setup(name="tricle",
      version=VERSION,
      description="An async programming framework with a blocking look-alike syntax",
      author="Greg Hazel and Steven Hazel",
      author_email="sah@awesame.org",
      maintainer="Steven Hazel",
      maintainer_email="sah@awesame.org",
      url="http://github.com/saucelabs/tricle",
      packages=['monocle',
                'monocle.stack',
                'monocle.stack.network'],
      install_requires=install_requires,
      license='MIT'
      )
