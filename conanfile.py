# Created by Mohamed Ghita on 2019-06-30.
# Copyright (c) 2019 Radalytica a.s. All rights reserved.

from conans import ConanFile, CMake, tools
import shutil
import os.path


class CeresSolverConan(ConanFile):
    name = "ceres-solver"
    version = "1.14.0"
    license = "BSD"
    author = "Mohamed G.A. Ghita (mohamed.ghita@radalytica.com)"
    url = "https://github.com/mohamedghita/conan-ceres-solver"
    description = "conan.io package for ceres-solver https://github.com/ceres-solver/ceres-solver/"
    topics = ("ceres-solver", "optimization", "solver")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        "build_tests": [True, False],
        "build_examples": [True, False]
    }
    default_options = {
        "shared": False,
        "build_tests": False,
        "build_examples": False,
        "gflags:nothreads": False
    }
    requires = "eigen/3.3.7@conan/stable", "glog/0.3.5@bincrafters/stable", "gflags/2.2.1@bincrafters/stable"
    build_requires = "cmake_installer/[>=3.14.4]@conan/stable"
    generators = "cmake"

    def source(self):
        extension = ".zip" if tools.os_info.is_windows else ".tar.gz"
        url = "https://github.com/ceres-solver/ceres-solver/archive/%s%s" % (self.version, extension)
        tools.get(url)
        shutil.move("ceres-solver-%s" % self.version, "ceres-solver")

        # policy CMP0025 solves https://cmake.org/pipermail/cmake/2018-March/067284.html
        tools.replace_in_file("ceres-solver/CMakeLists.txt", "cmake_policy(VERSION 2.8)",
                              "cmake_policy(VERSION 2.8)\n"
                              "cmake_policy(SET CMP0025 NEW)\n")

        tools.replace_in_file("ceres-solver/CMakeLists.txt", "project(Ceres C CXX)",
                              "project(Ceres C CXX)\n"
                              "include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)\n"
                              "conan_basic_setup()\n")

        if tools.os_info.is_macos: # find_package(Threads REQUIRED) fails in macos for not finding pthread.h
            tools.replace_in_file("ceres-solver/CMakeLists.txt", "find_package(Threads REQUIRED)",
                                  'set(CMAKE_THREAD_LIBS_INIT "-lpthread")\n'
                                  'set(CMAKE_HAVE_THREADS_LIBRARY 1)\n'
                                  'set(CMAKE_USE_WIN32_THREADS_INIT 0)\n'
                                  'set(CMAKE_USE_PTHREADS_INIT 1)\n'
                                  'set(THREADS_PREFER_PTHREAD_FLAG ON)')

        if self.settings.compiler.cppstd == "17":
            # std::random_shuffle is removed from c++17
            # https://github.com/ceres-solver/ceres-solver/issues/373
            tools.replace_in_file("ceres-solver/internal/ceres/schur_eliminator_impl.h",
                                  "random_shuffle(chunks_.begin(), chunks_.end())", "")

    def _configure_cmake(self, package_folder=None):
        cmake_defs = {}
        cmake_defs["BUILD_TESTING"] = self.options.build_tests
        cmake_defs["BUILD_EXAMPLES"] = self.options.build_examples
        cmake_defs["LAPACK"] = "OFF"
        cmake_defs["SUITESPARSE"] = "OFF"  # license issue; can't use GPL license
        cmake_defs["CXSPARSE"] = "OFF"
        cmake_defs["EIGENSPARSE"] = "ON"
        cmake_defs["CXX11"] = "ON"
        cmake_defs["CXX11_THREADS"] = "ON"
        cmake_defs["BUILD_SHARED_LIBS"] = self.options.shared
        cmake_defs["CMAKE_POSITION_INDEPENDENT_CODE"] = "ON"
        cmake_defs["GFLAGS_NAMESPACE"] = "gflags"
        if package_folder:
            cmake_defs["CMAKE_INSTALL_PREFIX"] = package_folder

        cmake = CMake(self)
        cmake.verbose = False
        cmake.configure(defs=cmake_defs, source_folder=os.path.join(self.build_folder, "ceres-solver"))
        return cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()
        if self.options.build_tests:
            cmake.test()

    def package_info(self):
        self.cpp_info.includedirs = ['include']  # Ordered list of include paths
        self.cpp_info.libs = ["ceres" if self.settings.build_type != "Debug" else "ceres-debug"]
        self.cpp_info.libdirs = ['lib']  # Directories where libraries can be found

    def imports(self):
        self.copy("license*", dst="licenses", folder=True, ignore_case=True)

    def package(self):
        cmake = self._configure_cmake(package_folder=self.package_folder)
        cmake.install()
        # licenses
        self.copy("license*", dst="licenses", keep_path=True)
