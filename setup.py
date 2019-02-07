"""
Build script for producing standalone executables for the python application using cx_freeze.
The output bundles together the python code, libraries and interpreter, along with the app's resources folder.
See https://cx-freeze.readthedocs.io/en/latest/distutils.html for documentation
"""

import sys
import shutil
from pathlib import Path
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it struggles with some parts of numpy.
build_exe_options = {'packages': ['numpy.core._methods',
                                  'numpy.lib.format',
                                  ],
                     'excludes': ['pytest',
                                  'pytest-cov',
                                  'pytest-qt',
                                  ],
                     'include_files':
                         [
                             'resources',
                             'Instrument.schema.json',
                         ],
                     }

unix_removable = ['lib/PySide2/Qt/lib/libQt5WebEngine.so.5',
                  'lib/PySide2/Qt/lib/libQt5WebEngineCore.so.5',
                  'lib/PySide2/Qt/lib/libQt5WebEngineWidgets.so.5',
                  'lib/PySide2/QtWidgets.abi3.so',
                  'lib/PySide2/libclang.so.6',
                  'lib/PySide2/Qt/resources/',
                  'lib/PySide2/Qt/translations/',
                  ]

win_removable = ['lib/PySide2/Qt5WebEngine.dll',
                 'lib/PySide2/Qt5WebEngineCore.dll',
                 'lib/PySide2/Qt5WebEngineWidgets.dll',
                 'lib/PySide2/QtWidgets.pyd',
                 'lib/PySide2/libclang.dll',
                 'lib/PySide2/resources/',
                 'lib/PySide2/translations/',
                 ]

# GUI applications require a different base on Windows (the default is for a console application).
if sys.platform == 'win32':
    base = 'Win32GUI'
    removable = win_removable
    extension = '.exe'
else:
    base = None
    removable = unix_removable
    extension = ''

setup(name='Nexus Constructor Test App',
      version='0.1',
      description='Technology test program for the nexus constructor',
      options={'build_exe': build_exe_options, 'bin_includes': ['libssl.so']},
      executables=[Executable('main.py', base=base, targetName='NexusConstructor' + extension)])

for file in removable:
    for build_dir in Path('.').glob('build/*'):
        full_path = build_dir / file
        if full_path.exists():
            if full_path.is_dir():
                print('Removing dir: ' + str(full_path))
                shutil.rmtree(str(full_path))
            else:
                print('Removing file: ' + str(full_path))
                full_path.unlink()
        else:
            print('Path: "' + str(full_path) + '" does not exist, and cannot be deleted')
