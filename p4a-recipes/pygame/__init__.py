"""Custom pygame recipe that uses pygame 2.5.2 for Python 3.11+ compatibility."""
from pythonforandroid.recipes.pygame import Pygame2Recipe as _OrigPygameRecipe


class Pygame2Recipe(_OrigPygameRecipe):
    version = '2.5.2'
    url = 'https://github.com/pygame/pygame/archive/refs/tags/{version}.tar.gz'


recipe = Pygame2Recipe()
