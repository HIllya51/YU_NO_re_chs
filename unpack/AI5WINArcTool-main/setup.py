import sys
import cx_Freeze

base = None

if (sys.platform == 'win32'):
    base = "Win32GUI"


executables = [cx_Freeze.Executable("main.py",
                                    shortcut_name="SilkyArcTool",
                                    shortcut_dir="SilkyArcTool",
                                    #base="Win32GUI"
                                    )]

cx_Freeze.setup(
        name="AI5WINArcTool",
        version="2.2",
        description="Dual languaged (rus+eng) tool for packing and unpacking archives of Silky Engine.\n"
                    "Двуязычное средство (рус+англ) для распаковки и запаковки архивов Silky Engine.",
        options={"build_exe": {"packages": []}},
        executables=executables
)