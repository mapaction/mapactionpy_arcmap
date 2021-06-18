if not exist env27\Scripts\python.exe (cmd /c C:/py27arcgis106/ArcGIS10.6/python.exe -m virtualenv --system-site-packages env27)
:: if not exist env_no_arcpy\Scripts\python.exe (cmd /c C:/Python27/python.exe -m virtualenv env_no_arcpy)

for %%g in (env27) do (
.\%%g\Scripts\python.exe -m pip install --no-cache-dir --no-color -e ..\mapactionpy_controller
.\%%g\Scripts\python.exe -m pip install --no-color -e .
.\%%g\Scripts\python.exe -m pip install -r requirements-dev.txt
)
