from pythonforandroid.recipe import CppCompiledComponentsPythonRecipe


class PygameCeRecipe(CppCompiledComponentsPythonRecipe):
    version = "2.5.6"
    url = "https://github.com/pygame-community/pygame-ce/archive/refs/tags/{version}.tar.gz"
    name = "pygame-ce"
    site_packages_name = "pygame"
    depends = ["sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf", "setuptools", "jpeg", "png"]
    call_hostpython_via_targetpython = False

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["USE_SDL2"] = "1"
        env["PYGAME_ANDROID"] = "1"
        sdl_includes = []
        for dep in ["sdl2", "sdl2_image", "sdl2_mixer", "sdl2_ttf"]:
            recipe = self.get_recipe(dep, self.ctx)
            sdl_includes.append(recipe.get_build_dir(arch.arch))
        env["PYGAME_EXTRA_BASE"] = ":".join(sdl_includes)
        env["LDFLAGS"] = env.get("LDFLAGS", "") + " -lSDL2 -lSDL2_image -lSDL2_mixer -lSDL2_ttf"
        return env


recipe = PygameCeRecipe()
