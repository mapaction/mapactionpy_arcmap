:: Py 2.7
.\env27\Scripts\python.exe -m autopep8 --in-place --max-line-length=120 --recursive . --exclude ./env*
.\env27\Scripts\python.exe -m flake8 --extend-exclude ./env*
.\env27\Scripts\python.exe -m coverage run -m unittest discover -v .\mapactionpy_arcmap/tests 

.\env27\Scripts\python.exe -m coverage html --include="./*" --omit="env*"
