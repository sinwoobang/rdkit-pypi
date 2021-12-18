from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as build_ext_orig
from sysconfig import get_paths
import os
from subprocess import check_call, call, run, PIPE
import subprocess
import sys
from sys import platform
import shutil
import re
from pathlib import Path

# get vcpkg path on Github
vcpkg_path = Path('C:/vcpkg')


def towin(pt: Path):
    """Returns a windows path from a Path object"""
    return str(pt).replace('\\', '/')

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

PLAT_TO_CMAKE = {
    "win32": "Win32",
    "win-amd64": "x64",
    "win-arm32": "ARM",
    "win-arm64": "ARM64",
}


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext_orig):
    def build_extension(self, ext):

        # Install boots for the correct python version
        # Need to replace "${CURRENT_INSTALLED_DIR}/include/python3.*" in the b2-options files
        
        b2_options = f"{os.environ['VCPKG_ROOT']}/ports/boost-python/b2-options.cmake"
        python_include_dir = Path(get_paths()["include"])
        python_lib_dir = Path(get_paths()["stdlib"])
        python_version = ".".join(map(str, sys.version_info[0:2]))
        
        # install correct boost-python version
        cmd = ["sed", "-i.bak"]
        cmd += [f'/file(GLOB python3_include_dir/c\    file(GLOB python3_include_dir "{towin(python_include_dir)}")']
        cmd += [b2_options]
        check_call(cmd)

        # replace version
        cmd = ["sed", "-i"]
        cmd += [f'/string(REGEX REPLACE/c\    set(python3_version "{python_version}")']
        cmd += [b2_options]
        check_call(cmd)

        python_libs = Path(get_paths()["data"]) / 'libs'

        
        cmd = ["sed", "-i"]
        cmd += [f"'s,${{CURRENT_INSTALLED_DIR}}/lib,{towin(python_libs)},g'"]
        # cmd += ["'s,.*${CURRENT_INSTALLED_DIR}/lib.*,    using python : ${python3_version} ;,g'"]
        cmd += [b2_options]
        check_call(cmd)

        # cmd = ["sed", "-i"]
        # # cmd += [f"'s,${{CURRENT_INSTALLED_DIR}}/lib,{towin(python_libs)},g'"]
        # cmd += ["'s,.*${CURRENT_INSTALLED_DIR}/debug.*,,g'"]
        # cmd += [b2_options]
        # check_call(cmd)


        check_call(f"cat {b2_options}".split())
        vcpkg_cmd = [f"{os.environ['VCPKG_ROOT']}/vcpkg", "install", "--recurse", "--clean-after-build", "--x-install-root", "D:\\a\\rdkit-pypi\\b\\vcpkg_installed" , "--triplet", "x64-windows"]
        check_call(vcpkg_cmd)
        check_call(f"mv {b2_options}.bak {b2_options}".split())
        

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # required for auto-detection & inclusion of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        # Install to `install` path
        install_path = Path(extdir) / 'install'

        # Set Python_EXECUTABLE instead if you use PYBIND11_FINDPYTHON
        # EXAMPLE_VERSION_INFO shows you how to pass a value into the C++ code
        # from Python.
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE={cfg}",  # not used on MSVC, but no harm
            f"-DCMAKE_INSTALL_PREFIX={install_path}",
        ]
        build_args = []
        # Adding CMake arguments set as environment variable
        # (needed e.g. to build for ARM OSx on conda-forge)
        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]

        # In this example, we pass in the version to C++. You might not need to.
        cmake_args += [f"-DEXAMPLE_VERSION_INFO={self.distribution.get_version()}"]

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            cmake_args += ["-GNinja"]
            # if not cmake_generator:
            #     try:
            #         import ninja  # noqa: F401

            #         cmake_args += ["-GNinja"]
            #     except ImportError:
            #         pass

        else:

            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, "parallel") and self.parallel:
                # CMake 3.12+ only.
                build_args += [f"-j{self.parallel}"]

        self.build_temp = 'build'
        
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # configure
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp
        )

        # build
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )

        # Install
        subprocess.check_call(
            ["cmake", "--install", "."] + build_args, cwd=self.build_temp
        )


setup(
    name="rdkit-pypi",
    version=f"2021.9.2.1",
    description="A collection of chemoinformatics and machine-learning software written in C++ and Python",
    author='Christopher Kuenneth',
    author_email='chris@kuenneth.dev',
    url="https://github.com/kuelumbus/rdkit-pypi",
    project_urls={
        "RDKit": "http://rdkit.org/",
        "RDKit on Github": "https://github.com/rdkit/rdkit",
    },
    license="BSD-3-Clause",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
          'numpy>=1.19',
      ],
    ext_modules=[CMakeExtension("rdkit-pypi", sourcedir='rdkit')],
    cmdclass={"build_ext": CMakeBuild},
    zip_safe=False,
)