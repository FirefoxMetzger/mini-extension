from setuptools.extension import Extension
from setuptools.command.develop import develop


class CustomDevelop(develop):
    """Custom install procedure.

    When declaring a ``build_extension.py`` poetry switches to setuptools during
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
        # build archives (.lib) these are declared in the `libraries` kwarg of
        # setup(). Extensions may depend on these, so we have to build the libs
        # them first.
        self.run_command("build_clib")
        super().run()


custom_extension = Extension(
    "extension.hello_world",
    sources=["extension/hello_world.c"],
    define_macros=[("PY_SSIZE_T_CLEAN",)],
    # we need to declare the extenal dependencies
    include_dirs=["external_archive/include"],
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
            "libraries": [
                ("hello", {
                    "sources": ["external_archive/src/hello.c"]
                    # flags and dependencies of this library
                    # "include_dirs": ... 
                    # "libraries": ...
                    # "cflags": ...
                }),
            ],
            "ext_modules": [custom_extension],
            # hook into the build process to build our external sources before
            # we build and install the package.
            "cmdclass": {"develop": CustomDevelop},
        }
    )
