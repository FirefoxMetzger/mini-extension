from setuptools.command.develop import develop
from setuptools.command.build_clib import build_clib

from distutils.errors import DistutilsSetupError
from distutils import log
from setuptools.dep_util import newer_pairwise_group
import platform
from pathlib import Path
import shutil


class CustomDevelop(develop):
    """Custom install procedure.

    When declaring a ``build.py`` poetry switches to setuptools during
    installation, i.e., it generates a temporary ``setup.py`` and then calls
    ``setup.py develop`` on it when you call ``poetry install``.
    Consequentially, we can hook into the develop command and customize the
    build to compile our source :) Note that this is only needed for the
    ``develop`` command, because the ``build`` command (``poetry build``)
    already includes ``build_clib``.

    This class then is the hook that will compile the source when we call
    ``poetry install``.

    """

    def run(self) -> None:
        # build the external C code before packaging
        self.run_command("build_clib")
        super().run()


class CustomBuildClib(build_clib):
    """Custom build instructions.

    This function adds the ability to compile shared libraries to build_clib. It
    is mostly analogous to building an archive (.lib/.a) except that we call
    ``compiler.link_shared_lib`` instead of ``compiler.create_static_lib`` in
    the end.

    To differentiate, the command adds the ``shared`` flag to the ``libraries``
    definition. This is ``False`` by default (i.e., build an archive), but
    builds a dynamically linked library (.dll/.so) if set to ``True``. See the
    setup kwargs below for an example.

    On Windows, this also adds the ``/DLL`` flag, which is needed to create a
    library (DLL) instad of an executable (EXE).

    """

    user_options = build_clib.user_options + [('shared-location=', 's',
         "copy the shared C/C++ libraries here after linking."),]

    def initialize_options(self) -> None:
        self.shared_location = None
        super().initialize_options()

    def run(self) -> None:
        super().run()

        # after building, copy the shared libraries into the given folder if needed.
        # this is useful if you need to have the libraries in a specific folder because
        # you are accessing them, e.g. by using ctypes, and you want them in a specific
        # folder when packaging.
        if self.shared_location is not None and self.libraries is not None:
            out_dir = Path(self.shared_location)
            out_dir.mkdir(exist_ok=True, parents=True)
            build_dir = Path(self.build_clib)
            for (lib_name, build_info) in self.libraries:
                if not build_info.get("shared", False):
                    continue

                file_name = self.compiler.library_filename(lib_name, lib_type="shared")

                shutil.copy(
                    str(build_dir / file_name),
                    str(out_dir / file_name)
                )

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
                    output_dir=self.build_clib,
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


def build(setup_kwargs):
    """
    This is a callback for poetry used to hook in our extensions.
    """

    setup_kwargs.update({
        # declare shared libraries (.dll/.so) to build. These can be linked
        # into extensions or cython code, but also accessed by ctypes or cffi
        "libraries": [
            (
                "shared_hello",
                {
                    "sources": ["external_library/src/hello.c"],
                    "shared": True,
                    # "cflags": ...
                    # "include_dir": ...
                    # "libraries": ...
                },
            ),
        ],
        # configure the build_clib command to place the shared library into
        # extension/lib. This is purely my convention, so feel free to
        # adjust this as needed.
        "options": {
            "build_clib": {
                "shared_location": "extension/lib"
            }
        },
        # hook into the build process to run our modifications from above
        "cmdclass": {"develop": CustomDevelop, "build_clib": CustomBuildClib},
    })
