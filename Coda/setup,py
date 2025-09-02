# to build run: python setup.py build_ext --inplace

from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "sharding",
        sources=["_core/sharding.pyx"]
    ),
    Extension(
        "tools", 
        sources=["utils/tools.pyx"]
    )
]

setup(
    ext_modules=cythonize(extensions, language_level=3),
    zip_safe=False,
)