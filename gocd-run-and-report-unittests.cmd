pushd mapy-arcmap
"../env/Scripts/python.exe" -m coverage run --include="./*" -m xmlrunner discover mapactionpy_arcmap/tests -o "../junit-reports"
"../env/Scripts/python.exe" -m coveralls
popd
