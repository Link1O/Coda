# to build run: python setup.py build_ext --inplace

from setuptools import setup
from Cython.Build import cythonize
setup(
    name="ShardManagerModule",
    ext_modules=cythonize("sharding.pyx", language_level=3),
    zip_safe=False,
)