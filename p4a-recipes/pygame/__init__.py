"""Custom pygame recipe that uses pygame 2.5.2 for Python 3.11+ compatibility.

Uses PyPI sdist which includes pre-generated Cython .c files,
avoiding the need for Cython at build time.
"""
from pythonforandroid.recipes.pygame import Pygame2Recipe as _OrigPygameRecipe


class Pygame2Recipe(_OrigPygameRecipe):
    version = '2.5.2'
    url = 'https://files.pythonhosted.org/packages/source/p/pygame/pygame-{version}.tar.gz'


recipe = Pygame2Recipe()
