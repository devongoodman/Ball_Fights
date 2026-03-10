"""Custom pygame recipe that patches longintrepr.h for Python 3.11+"""
import os
import glob
from pythonforandroid.recipes.pygame import Pygame2Recipe as _OrigPygameRecipe


class Pygame2Recipe(_OrigPygameRecipe):
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Patch all .c files that include longintrepr.h
        # In Python 3.11+, longintrepr.h was moved to cpython/longintrepr.h
        build_dir = self.get_build_dir(arch.arch)
        for root, dirs, files in os.walk(build_dir):
            for f in files:
                if f.endswith('.c') or f.endswith('.h'):
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                            content = fh.read()
                    except Exception:
                        continue
                    if '#include "longintrepr.h"' in content:
                        new_content = content.replace(
                            '#include "longintrepr.h"',
                            '#if PY_VERSION_HEX >= 0x030b00a1\n'
                            '#include "cpython/longintrepr.h"\n'
                            '#else\n'
                            '#include "longintrepr.h"\n'
                            '#endif'
                        )
                        with open(filepath, 'w') as fh:
                            fh.write(new_content)
                        print(f"Patched longintrepr.h in {filepath}")


recipe = Pygame2Recipe()
