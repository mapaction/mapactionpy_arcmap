import subprocess
from setuptools import setup, find_packages
from os import path, environ


def readme():
    here = path.abspath(path.dirname(__file__))
    with open(path.join(here, 'README.md')) as f:
        return f.read()


_base_version = '0.9'


def _get_version_number():
    travis_build = environ.get('TRAVIS_BUILD_NUMBER')
    travis_tag = environ.get('TRAVIS_TAG')

    if travis_build:
        if travis_tag:
            return travis_tag
        else:
            return '{}.dev{}'.format(_base_version, travis_build)
    else:
        try:
            ver = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
            return '{}+local.{}'.format(_base_version, ver.decode('ascii').strip())
        except Exception:
            return ''


setup(name='mapactionpy_arcmap',
      version=_get_version_number(),
      description='Used to drive ArcMap',
      long_description=readme(),
      long_description_content_type="text/markdown",
      url='http://github.com/mapaction/mapactionpy_arcmap',
      author='MapAction',
      author_email='github@mapaction.com',
      license='GPL3',
      packages=find_packages(),
      install_requires=[
          'argparse',
          'requests',
          'pycountry',
          'slugify',
          'jsonpickle',
          'Pillow',
          'python-resize-image'
      ],
      test_suite='unittest',
      tests_require=['unittest'],
      zip_safe=False,
      classifiers=[
          "Development Status :: 2 - Pre-Alpha",
          "Programming Language :: Python :: 2.7",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Operating System :: Microsoft :: Windows",
      ])
