from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("Coda.sharding", sources=["Coda/_core/sharding.pyx"]),
    Extension("Coda.utils.tools", sources=["Coda/utils/tools.pyx"]),
]

setup(
    ext_modules=cythonize(extensions, language_level=3),
)
