from mock import Mock
import sys
import types

module_name = 'arcpy'
bogus_module = types.ModuleType(module_name)
sys.modules[module_name] = bogus_module
bogus_module.foo = Mock(name=module_name+'.foo')
