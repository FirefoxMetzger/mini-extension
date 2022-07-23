from setuptools.extension import Extension
from setuptools.command.develop import develop
from setuptools.command.build_clib import build_clib

from distutils.errors import DistutilsSetupError
from distutils import log
from setuptools.dep_util import newer_pairwise_group
import platform
from pathlib import Path


class CustomDevelop(develop):
    """Custom install procedure.

    .. note::

        This is only needed if your have "external source", i.e., if your
        extensions depend on an external C library that you wish to compile into
        a .lib or if you want to compile a .so/.dll for dynamic linking.

    When declaring a ``build.py`` poetry switches to setuptools during
    installation, i.e., it generates a temporary ``setup.py`` and then calls
    ``setup.py develop`` on it. Consequentially, we can hook into the develop
    command and customize the build to compile any source :)

    This class then is the hook that will compile the source when we cal
    ``poetry install``.

    """

    def run(self) -> None:
        # build archives (.lib) these are declared in the `libraries` kwarg of
        # setup(). Extensions may depend on these, so we have to build the libs
        # them first.
        self.run_command("build_clib")

        super().run()

        # when building shared libraries, we may wish to move them into the
        # package folder


class CustomBuildClib(build_clib):
    """Custom build instructions.

    .. note::

        This is only needed if you have "external source" that you want to
        compile into a **shared** library (.dll / .so). If you want to compile a
        statically linked library, use the ``libraries`` kwarg instead (see
        below for an example how to do that).

    This function adds the ability to compile shared libraries to build_clib.
    This is mostly analogous to building an archive (.lib / .a) except that we
    call the linker with different arguments.

    """

    user_options = build_clib.user_options + [('build-shared=', 's',
         "directory to place shared C/C++ libraries after linking."),]

    def initialize_options(self) -> None:
        self.build_shared = None
        super().initialize_options()

    def finalize_options(self) -> None:
        super().finalize_options()
        if self.build_shared is None:
            self.build_shared = self.build_clib

    def run(self) -> None:
        Path(self.build_shared).mkdir(exist_ok=True, parents=True)
        super().run()

    def build_libraries(self, libraries):
        # Note: this is a copy of build_clib except for the part marked below
        for (lib_name, build_info) in libraries:
            sources = build_info.get("sources")
            if sources is None or not isinstance(sources, (list, tuple)):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'sources' must be present and must be "
                    "a list of source filenames" % lib_name
                )
            sources = list(sources)

            log.info("building '%s' library", lib_name)

            # Make sure everything is the correct type.
            # obj_deps should be a dictionary of keys as sources
            # and a list/tuple of files that are its dependencies.
            obj_deps = build_info.get("obj_deps", dict())
            if not isinstance(obj_deps, dict):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'" % lib_name
                )
            dependencies = []

            # Get the global dependencies that are specified by the '' key.
            # These will go into every source's dependency list.
            global_deps = obj_deps.get("", list())
            if not isinstance(global_deps, (list, tuple)):
                raise DistutilsSetupError(
                    "in 'libraries' option (library '%s'), "
                    "'obj_deps' must be a dictionary of "
                    "type 'source: list'" % lib_name
                )

            # Build the list to be used by newer_pairwise_group
            # each source will be auto-added to its dependencies.
            for source in sources:
                src_deps = [source]
                src_deps.extend(global_deps)
                extra_deps = obj_deps.get(source, list())
                if not isinstance(extra_deps, (list, tuple)):
                    raise DistutilsSetupError(
                        "in 'libraries' option (library '%s'), "
                        "'obj_deps' must be a dictionary of "
                        "type 'source: list'" % lib_name
                    )
                src_deps.extend(extra_deps)
                dependencies.append(src_deps)

            expected_objects = self.compiler.object_filenames(
                sources,
                output_dir=self.build_temp,
            )

            if newer_pairwise_group(dependencies, expected_objects) != ([], []):
                # First, compile the source code to object files in the library
                # directory.  (This should probably change to putting object
                # files in a temporary build directory.)
                macros = build_info.get("macros")
                include_dirs = build_info.get("include_dirs")
                cflags = build_info.get("cflags")
                self.compiler.compile(
                    sources,
                    output_dir=self.build_temp,
                    macros=macros,
                    include_dirs=include_dirs,
                    extra_postargs=cflags,
                    debug=self.debug,
                )

            is_shared = build_info.get("shared", False)
            if is_shared:
                # This part is __NEW__. It checks for a flag called
                # "shared" and then compiles a shared library instead of an archive.

                if platform.system() == "Windows":
                    # On windows (MSVC) we need to tell the compiler to make a DLL
                    preargs = ["/DLL"]
                else:
                    preargs = []

                self.compiler.link_shared_lib(
                    expected_objects,
                    lib_name,
                    output_dir=self.build_shared,
                    debug=self.debug,
                    extra_preargs=preargs,
                )
            else:
                # Now "link" the object files together into a static library.
                # (On Unix at least, this isn't really linking -- it just
                # builds an archive.  Whatever.)
                self.compiler.create_static_lib(
                    expected_objects,
                    lib_name,
                    output_dir=self.build_clib,
                    debug=self.debug,
                )


internal_source = Extension(
    "mini_extension.internal",
    sources=["mini_extension/internal_source.c"],
    define_macros=[("PY_SSIZE_T_CLEAN",)],
)

external_lib = Extension(
    "mini_extension.external",
    sources=["mini_extension/external_source.c"],
    define_macros=[("PY_SSIZE_T_CLEAN",)],
    # dependencies
    include_dirs=["include/"],
    libraries=["hello"],  # see below
)


def build(setup_kwargs):
    """
    This is a callback for poetry used to hook in our extensions.
    """

    setup_kwargs.update(
        {
            # declare archives (.lib) to build. These will be linked to
            # statically by extensions, cython, ...
            # Note: you can also declare cflags, include_dirs, ... in the dict :)
            "libraries": [
                ("hello", {"sources": ["src/external_lib/hello.c"]}),
                (
                    "shared_hello",
                    {"sources": ["src/external_shared/hello.c"], "shared": True},
                ),
            ],
            "options": {
                "bdist_wheel": {
                    "universal": True
                }
            },
            # declare extensions (.pyd) to build. These can be imported and
            # called directly from python. Here, we build the following extensions'
            # - internal_source: Minimal Extension (no dependencies)
            # - external_c_source: Extension that depends on a .lib we build above
            "ext_modules": [internal_source, external_lib],
            # hook into the build process to build our external sources before
            # we build and install the package.
            "cmdclass": {"develop": CustomDevelop, "build_clib": CustomBuildClib},
        }
    )
