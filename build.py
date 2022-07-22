from distutils.extension import Extension


internal_source = Extension(
    "mini_extension.internal",
    sources=["mini_extension/internal_source.c"],
    define_macros=[("PY_SSIZE_T_CLEAN",)],
)

external_c_source = Extension(
    "mini_extension.external",
    sources=["mini_extension/external_source.c"],
    define_macros=[("PY_SSIZE_T_CLEAN",)],
    
    # dependencies
    include_dirs=["external_c_source/include"],
    libraries=["hello"]  # see below
)


def build(setup_kwargs):
    """
    This is a callback for poetry used to hook in our extensions.
    """

    setup_kwargs.update(
        {
            # building extensions 
            # (callable from python directly)
            "ext_modules": [
                internal_source, 
                external_c_source
            ],

            # building static libraries (.lib)
            # (these can be linked to by extensions, cython code, ...)
            "libraries": [('hello', {'sources': ['external_c_source/hello.c']})],
        }
    )
