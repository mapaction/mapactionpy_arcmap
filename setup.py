import subprocess
from setuptools import setup, find_packages
from os import path, environ

_base_version = '1.0.0'
root_dir = path.abspath(path.dirname(__file__))


def readme():
    with open(path.join(root_dir, 'README.md')) as f:
        return f.read()


def _get_version_number():
    travis_build = environ.get('TRAVIS_BUILD_NUMBER')
    travis_tag = environ.get('TRAVIS_TAG')

    if travis_build:
        if travis_tag:
            version = travis_tag
        else:
            version = '{}.dev{}'.format(_base_version, travis_build)

        with open(path.join(root_dir, 'VERSION'), 'w') as version_file:
            version_file.write(version.strip())
    else:
        try:
            ver = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
            version = '{}+local.{}'.format(_base_version, ver.decode('ascii').strip())
        except Exception:
            with open(path.join(root_dir, 'VERSION')) as version_file:
                version = version_file.read().strip()

    return version


# TODO: asmith
# install_requires should include `mapactionpy_controller`
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
          'mapactionpy_controller',
          'argparse',
          'slugify',
          'jsonpickle',
          'Pillow',
          'python-resize-image'
      ],
      test_suite='unittest',
      tests_require=['unittest'],
      zip_safe=False,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Programming Language :: Python :: 2.7",
          "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
          "Operating System :: Microsoft :: Windows",
      ])
