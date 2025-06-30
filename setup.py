from cx_Freeze import setup, Executable
import os

# For a full .app bundle, 'base' would be 'Win32GUI' on Windows and 'MacOSX' on Mac,
# but we are aiming to run from the command line first.
exe = Executable(
    script="hp4195a_reader.py",
    base=None, # Use None for a console-based app on Mac/Linux
)

options = {
    'build_exe': {
        'include_files': [
            os.path.join(os.path.dirname(__file__), 'logging.conf')
        ],
        'packages': ['PyQt5.QtWebEngineWidgets', 'numpy', 'matplotlib', 'markdown'],
    },
}

setup(
    name="hp4185a-reader",
    version="0.1",
    description="A basic program for connecting to and interfacing with a HP4195A Network/Spectrum Analyser.",
    options=options,
    executables=[exe]
)