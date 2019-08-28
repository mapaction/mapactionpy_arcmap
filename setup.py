from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()


setup(name='mapactionpy_arcmap',
      version='0.1',
      description='Used to drive ArcMap',
      url='http://github.com/mapaction/mapactionpy_arcmap',
      author='MapAction',
      author_email='github@mapaction.com',
      license='GPL3',
      packages=['mapactionpy_arcmap'],
          test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
