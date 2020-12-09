if not exist env27\Scripts\python.exe (cmd /c C:/py27arcgis106/ArcGIS10.6/python.exe -m virtualenv --system-site-packages env27)

.\env27\Scripts\python.exe -m pip install --no-color -e D:\code\github\mapactionpy_controller
.\env27\Scripts\python.exe -m pip install --no-color -e .
.\env27\Scripts\python.exe -m pip install -r requirements-dev.txt
