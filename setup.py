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


# class RDKit(Extension):
#     def __init__(self, name, **kwargs):
#         # don't invoke the original build_ext for this special extension
#         super().__init__(name, sources=[])
#         self.__dict__.update(kwargs)


# class BuildRDKit(build_ext_orig):
#     def run(self):
#         for ext in self.extensions:
#             # Build boot
#             # self.build_boost(ext)
#             # Then RDKit
#             self.build_rdkit(ext)
#             # Copy files so that a wheels package can be created
#             self.create_package(ext)
#         # invoke the creation of the wheels package
#         super().run()


#     def get_ext_filename(self, ext_name):
#         ext_path = ext_name.split('.')
#         return os.path.join(*ext_path)

#     def create_package(self, ext):
#         from distutils.file_util import copy_file
#         from shutil import copytree, rmtree

#         # copy RDKit
#         if platform == 'win32':
#             rdkit_root = Path(self.build_temp).absolute() / 'rdkit_install/' / 'Lib'
#             rdkit_pyfiles = rdkit_root / 'site-packages' / 'rdkit' 
#         else:
#             rdkit_root = Path(self.build_temp).absolute() / 'rdkit_install/' / 'lib'
#             rdkit_pyfiles = list(rdkit_root.glob('python*'))[0] / 'site-packages' / 'rdkit' 

#         # rdkit needs some files from the Data directory to run correctly 
#         # rdkit_data_path = Path(self.build_temp).absolute() / 'rdkit' / 'Data'
#         # Copy the installed Data directory. Some modules copy files to that directory during bulding rdkit
#         rdkit_data_path = Path(self.build_temp).absolute() / 'rdkit_install/' / 'share' / 'RDKit' /'Data'

#         # replace line with _share=... with _share = os.path.dirname(__file__) in RDPaths.py
#         rdpaths = rdkit_pyfiles / 'RDPaths.py'

#         # For linux
#         if platform == "linux" or platform == "linux2" or platform == 'win32':
#             # linux
#             call(["sed", "-i", "/_share =/c\_share = os.path.dirname(__file__)", str(rdpaths)])
#         elif platform == "darwin":
#             # OS X
#             call(["gsed", "-i", "/_share =/c\_share = os.path.dirname(__file__)", str(rdpaths)])

#         wheel_path = Path(self.get_ext_fullpath(ext.name)).absolute()
#         # remove if exists
#         if wheel_path.exists():
#             rmtree(str(wheel_path))

#         # copy rdkit files 
#         copytree(str(rdkit_pyfiles), str(wheel_path))

#         # copy the Data directory to the wheel path
#         copytree(str(rdkit_data_path), str(wheel_path / 'Data'))

#         # Copy *.so files to /usr/local/lib
#         # auditwheel finds the libs at /usr/local/lib
#         libs_rdkit_linux = Path(rdkit_root).glob('*.so*')
#         libs_rdkit_macos = Path(rdkit_root).glob('*dylib')
#         libs_rdkit = list(libs_rdkit_linux) + list(libs_rdkit_macos)

#         libs_boost = Path(self.build_temp).absolute() / 'boost_install' / 'lib'
#         libs_boost_linux = libs_boost.glob('*.so*')
#         libs_boost_mac = libs_boost.glob('*dylib')
#         libs_boost_tmp = list(libs_boost_linux) + list(libs_boost_mac)

#         if platform != 'win32':
#             [copy_file(i, '/usr/local/lib' ) for i in libs_rdkit]
#             [copy_file(i, '/usr/local/lib' ) for i in libs_boost_tmp]
#         else:
#             libs_rdkit_win = Path(rdkit_root).glob('*.dll')
#             libs_boost_win = libs_boost.glob('*.dll')
            
#             libs_vcpkg = list((vcpkg_path / 'installed' / 'x64-windows' / 'bin').glob('*.dll'))

#             [copy_file(i, 'C://libs' ) for i in libs_rdkit_win]
#             [copy_file(i, 'C://libs' ) for i in libs_boost_win]
#             [copy_file(i, 'C://libs' ) for i in libs_vcpkg]
    
#     def build_boost(self, ext):
#         """Build the Boost libraries"""
        
#         cwd = Path().absolute()
#         boost_build_path = Path(self.build_temp).absolute() / 'boost'
#         boost_build_path.mkdir(parents=True, exist_ok=True)

#         boost_install_path = Path(self.build_temp).absolute() / 'boost_install'
#         boost_install_path.mkdir(parents=True, exist_ok=True)

#         # Download and unpack Boost
#         os.chdir(str(boost_build_path))

#         if platform == "linux" or platform == "linux2":
#             boost_download_url = ext.boost_download_urls['linux']
#         elif platform == 'win32':
#             boost_download_url = ext.boost_download_urls['win']
#         elif platform == 'darwin':
#             boost_download_url = ext.boost_download_urls['mac']

#         cmds = [
#             f'wget {boost_download_url} --no-check-certificate -q',
#             f'tar -xzf {Path(boost_download_url).name}',
#             ]

#         [check_call(c.split()) for c in cmds]

#         # Compile Boost
#         os.chdir(Path(boost_download_url).with_suffix('').with_suffix('').name)

#         # This fixes a bug in the boost configuration. Boost expects python include paths without "m"
#         cmds = [
#             # for linux
#             'ln -fs /opt/python/cp36-cp36m/include/python3.6m /opt/python/cp36-cp36m/include/python3.6',
#             'ln -fs /opt/python/cp37-cp37m/include/python3.7m /opt/python/cp37-cp37m/include/python3.7',
#             # same for MacOS
#             'ln -fs /Library/Frameworks/Python.framework/Versions/3.6/include/python3.6m /Library/Frameworks/Python.framework/Versions/3.6/include/python3.6',
#             'ln -fs /Library/Frameworks/Python.framework/Versions/3.7/include/python3.7m /Library/Frameworks/Python.framework/Versions/3.7/include/python3.7',
#             ]
#         # Ok to fail
#         [call(c.split()) for c in cmds]
         
   
#         # Change commands for windows
#         if sys.platform == 'win32':

#             cmds = [
#                 f'bootstrap.bat',
#             ]
#             [check_call(c.split()) for c in cmds]

#             # Compile for many python versions at the same time?
#             python_inc = Path(get_paths()["include"])
#             python_libs = Path(get_paths()["data"]) / 'libs'
#             python_exe = Path(get_paths()["data"]) / 'python.exe'
            
#             zlib_include = vcpkg_path / 'packages/zlib_x64-windows/include'
#             zlib_lib = vcpkg_path / 'packages/zlib_x64-windows/lib'

#             bzip2_include = vcpkg_path / 'packages/bzip2_x64-windows/include'
#             bzip2_lib = vcpkg_path / 'packages/bzip2_x64-windows/lib'
#             with open('project-config.jam', 'a') as fl:
#                 print(f'using python : {sys.version_info[0]}.{sys.version_info[1]} : {towin(python_exe)} : {towin(python_inc)} : {towin(python_libs)} ;', file=fl)
#                 print(f' ', file=fl)
#                 print(f'using zlib : 2 : <include>{towin(zlib_include)} <search>{towin(zlib_lib)} ;', file=fl)
#                 print(f' ', file=fl)
#                 print(f'using bzip2 : 1 : <include>{towin(bzip2_include)} <search>{towin(bzip2_lib)} ;', file=fl)
#                 print(f' ', file=fl)
            
#             cmds = [                
#                 f'./b2 address-model=64 architecture=x86 link=static link=shared threading=single threading=multi ' \
#                 f'variant=release -d0 --abbreviate-paths ' \
#                 f'--with-python --with-serialization --with-iostreams --with-system --with-regex --with-program_options ' \
#                 f'--prefix={boost_install_path} -j 20 install',
#             ]
#             [check_call(c.split()) for c in cmds]

#         else:
#             cmds = [
#             f'./bootstrap.sh --with-libraries=python,serialization,iostreams,system,regex --with-python={sys.executable} --with-python-root={Path(sys.executable).parent}/..',
#             f'./b2 install --prefix={boost_install_path} -j 20',
#             ]
#             [check_call(c.split()) for c in cmds]

            
#         check_call(['ls', towin(boost_install_path / 'lib')])

#         os.chdir(str(cwd))

#     def build_rdkit(self, ext):
#         """ Build RDKit """

#         cwd = Path().absolute()
#         rdkit_build_path = Path(self.build_temp).absolute() 
#         rdkit_build_path.mkdir(parents=True, exist_ok=True) 

#         boost_install_path = Path(self.build_temp).absolute() / 'boost_install'

#         rdkit_install_path = Path(self.build_temp).absolute() / 'rdkit_install'
#         rdkit_install_path.mkdir(parents=True, exist_ok=True)
        
#         # added as submodule
#         os.chdir(str('rdkit'))
        
#         # all includes are here
#         vcpkg_install_path = vcpkg_path / 'installed' / 'x64-windows' 
#         vcpkg_include_path = vcpkg_path / 'installed' / 'x64-windows' / 'include'
#         vcpkg_lib_path = vcpkg_path / 'installed' / 'x64-windows' / 'lib'

#         # Invoke cmake and compile RDKit
#         options = [ 
#             # Defines the paths to many include and libaray paths for windows
#             # Does not work for some reason??
#             # f"-DCMAKE_TOOLCHAIN_FILE=C:\\vcpkg\\scripts\\buildsystems\\vcpkg.cmake" if sys.platform == 'win32' else "",
#             # f"-DVCPKG_TARGET_TRIPLET=x64-windows-static" if sys.platform == 'win32' else "",

#             f'-DPYTHON_EXECUTABLE={sys.executable}',
#             f'-DPYTHON_INCLUDE_DIR={get_paths()["include"]}',

#             # RDKIT build flags
#             f"-DRDK_BUILD_INCHI_SUPPORT=ON",
#             f"-DRDK_BUILD_AVALON_SUPPORT=ON",
#             f"-DRDK_BUILD_PYTHON_WRAPPERS=ON",
#             f"-DRDK_BUILD_YAEHMOP_SUPPORT=ON",
#             f"-DRDK_INSTALL_INTREE=OFF",

#             # Boost              
#             f"-DBOOST_ROOT={boost_install_path}",
#             f"-DBoost_NO_SYSTEM_PATHS=ON",
#             f"-DBoost_DEBUG=OFF",        

#             # Does not work (this is fixed in future rdkit versions I believe)
#             f"-DRDK_INSTALL_STATIC_LIBS=OFF" if sys.platform == 'win32' else "",

#             # ##### for windows 
#             # cairo
#             f"-DRDK_BUILD_CAIRO_SUPPORT=ON",
#             f"-DCAIRO_INCLUDE_DIR={towin(vcpkg_include_path)}" if sys.platform == 'win32' else "",
#             f"-DCAIRO_LIBRARY_DIR={towin(vcpkg_lib_path)}" if sys.platform == 'win32' else "",
            
#             # zlib
#             f"-DZLIB_ROOT={towin(vcpkg_install_path)}" if sys.platform == 'win32' else "",

#             # freetype
#             f"-DFREETYPE_INCLUDE_DIRS={towin(vcpkg_include_path)}" if sys.platform == 'win32' else "",
#             f"-DFREETYPE_LIBRARY={towin(vcpkg_lib_path / 'freetype.lib')}" if sys.platform == 'win32' else "",

#             # eigen3
#             f"-DEIGEN3_INCLUDE_DIR={towin(vcpkg_include_path)}" if sys.platform == 'win32' else "",

#             # instruct to build x64
#             "-Ax64" if sys.platform == 'win32' else "",

#             # Mac needs these flags to compile 
#             f"-DCMAKE_C_FLAGS=-Wno-implicit-function-declaration" if sys.platform == 'darwin' else "", 
#             f"-DCMAKE_CXX_FLAGS=-Wno-implicit-function-declaration" if sys.platform == 'darwin' else "", 

#             # build stuff
#             f"-DCMAKE_INSTALL_PREFIX={rdkit_install_path}",
#             f"-DCMAKE_BUILD_TYPE=Release",
#         ]
        
#         cmds = [
#             f"cmake -S . -B build {' '.join(options)} ",
#             f"cmake --build build -j 10 --config Release",
#             f"cmake --install build"
#         ]    
#         [check_call(c.split()) for c in cmds]
#         os.chdir(str(cwd))

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
        
        # b2_options = f"{os.environ['VCPKG_ROOT']}/ports/boost-python/b2-options.cmake"
        # call(["sed", "-i", f'/file(GLOB python3_include_dir/c\file(GLOB python3_include_dir {get_paths()["include"]})', b2_options])

        # Call vcpkg remove and install
        # check_call(f"{os.environ['VCPKG_ROOT']}/vcpkg install".split())
        run(["ls", "-lsrta"], capture_output=True)
        check_call(f"mv vcpkg.json vcpkg_back.json".split())
        check_call(f"mv vcpkg_with_boost.json vcpkg.json".split())
        check_call(f"{os.environ['VCPKG_ROOT']}/vcpkg install".split())
        check_call(f"mv vcpkg.json vcpkg_with_boost.json ".split())
        check_call(f"mv vcpkg_back.json vcpkg.json".split())
        check_call(f"{os.environ['VCPKG_ROOT']}/vcpkg install".split())


        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # required for auto-detection & inclusion of auxiliary "native" libs
        if not extdir.endswith(os.path.sep):
            extdir += os.path.sep

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = "Debug" if debug else "Release"

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        # Set Python_EXECUTABLE instead if you use PYBIND11_FINDPYTHON
        # EXAMPLE_VERSION_INFO shows you how to pass a value into the C++ code
        # from Python.
        cmake_args = [
            f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={extdir}",
            f"-DPYTHON_EXECUTABLE={sys.executable}",
            f"-DCMAKE_BUILD_TYPE={cfg}",  # not used on MSVC, but no harm
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
            if not cmake_generator:
                try:
                    import ninja  # noqa: F401

                    cmake_args += ["-GNinja"]
                except ImportError:
                    pass

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

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
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