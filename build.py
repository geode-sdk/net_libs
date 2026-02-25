from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT
from enum import Enum, auto
import subprocess
import platform as pf
import traceback
import builtins
import argparse
import shutil
import time
import os

CURL_REPO = "https://github.com/curl/curl"
CURL_TAG = "rc-8_19_0-1"
CARES_REPO = "https://github.com/c-ares/c-ares"
CARES_TAG = "2870f6b"
NGHTTP2_REPO = "https://github.com/nghttp2/nghttp2"
NGHTTP2_TAG = "v1.68.0"
NGTCP2_REPO = "https://github.com/ngtcp2/ngtcp2"
NGTCP2_TAG = "v1.20.0"
NGHTTP3_REPO = "https://github.com/ngtcp2/nghttp3"
NGHTTP3_TAG = "v1.15.0"
ZSTD_REPO = "https://github.com/facebook/zstd"
ZSTD_TAG = "v1.5.7"
RUSTLS_REPO = "https://github.com/rustls/rustls-ffi"
RUSTLS_TAG = "v0.15.0"
ZLIB_REPO = "https://github.com/madler/zlib"
ZLIB_TAG = "v1.3.2"
OPENSSL_REPO = "https://github.com/openssl/openssl"
OPENSSL_TAG = "openssl-3.6.1"

ANDROID_SDK_VERSION = 23
MIN_IOS_VERSION = "14.0"
MIN_MACOS_VERSION = "11.0"
OPENSSL_CLANG = True

REPOS = [
    (CURL_REPO, CURL_TAG),
    (CARES_REPO, CARES_TAG),
    (NGHTTP2_REPO, NGHTTP2_TAG),
    (NGTCP2_REPO, NGTCP2_TAG),
    (NGHTTP3_REPO, NGHTTP3_TAG),
    (ZSTD_REPO, ZSTD_TAG),
    (RUSTLS_REPO, RUSTLS_TAG),
    (ZLIB_REPO, ZLIB_TAG),
    (OPENSSL_REPO, OPENSSL_TAG),
]

class Color:
    RED    = "\033[31m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    BLUE   = "\033[34m"
    MAGENTA= "\033[35m"
    CYAN   = "\033[36m"
    RESET  = "\033[0m"

def cprint(text, color):
    print(f"{color}{text}{Color.RESET}")

_orig_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _orig_print(*args, **kwargs)

def strpath(p: Path):
    return str(p.absolute()).replace("\\", "/")

class TlsBackend(Enum):
    OpenSSL = auto()
    SChannel = auto()
    Rustls = auto()

    @classmethod
    def from_str(cls, s: str) -> TlsBackend | None:
        match s.lower():
            case "none":
                return None
            case "openssl":
                return cls.OpenSSL
            case "schannel":
                return cls.SChannel
            case "rustls":
                return cls.Rustls
            case _:
                raise ValueError(f"Unsupported TLS backend: {s}")

class BuildException(Exception):
    pass

@dataclass
class BuildConfig:
    tls: TlsBackend | None = None
    use_ares: bool = True
    platform: str = ""
    profile: str = "Release"
    cmake_args: list[str] = field(default_factory=list)
    cmake_env: dict[str, str] = field(default_factory=dict)
    ndk_path: Path | None = None
    sysroot: Path | None = None
    generator: str = ""
    flatten_output: bool = False
    skip_lib_verify: bool = False
    lto: bool = False
    perl_path: Path | None = None
    rebuild_whitelist: set[str] = field(default_factory=set)
    output_path: Path = field(default_factory=Path)
    build_dir: Path = field(default_factory=Path)

    @classmethod
    def for_platform(cls, plat: str) -> BuildConfig:
        tls: TlsBackend | None = None
        args = []
        env = {}

        plat = plat.lower()
        match plat:
            case "windows":
                tls = TlsBackend.OpenSSL
            case "android32" | "android64":
                tls = TlsBackend.OpenSSL
                args.append(f"-DANDROID_ABI={'arm64-v8a' if plat == 'android64' else 'armeabi-v7a'}")
                args.append(f"-DANDROID_PLATFORM=android-{ANDROID_SDK_VERSION}")
                args.append("-Wno-dev") # very annoying cmake 3.10 deprecation warnings
            case "macos":
                tls = TlsBackend.OpenSSL
                args.append('-DCMAKE_OSX_ARCHITECTURES=x86_64;arm64')
                args.append(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={MIN_MACOS_VERSION}")
            case "ios":
                tls = TlsBackend.OpenSSL
                args.append('-DCMAKE_OSX_ARCHITECTURES=arm64')
                args.append(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={MIN_IOS_VERSION}")
                args.append("-DCMAKE_IOS_INSTALL_COMBINED=YES")
                args.append("-DCMAKE_SYSTEM_NAME=iOS")
            case _:
                raise ValueError(f"Unsupported platform: {plat}")

        ret = cls(tls, True, plat, "Release", args, env)
        ret.post_setup()
        return ret

    def post_setup(self):
        if self.platform == "ios":
            self.sysroot = self._find("sysroot")
            self.cmake_env["CC"] = self.find_cc()
            self.cmake_args.append(f"-DCMAKE_OSX_SYSROOT={self.sysroot}")

    def target_triple(self) -> str:
        match self.platform:
            case "windows":
                return "x86_64-pc-windows-msvc"
            case "android32":
                return "armv7-linux-androideabi"
            case "android64":
                return "aarch64-linux-android"
            case "ios":
                return "aarch64-apple-ios"
            case "macos":
                return "aarch64-apple-darwin"
            case _:
                raise ValueError(f"Unsupported platform: {self.platform}")

    @staticmethod
    def determine_platform() -> str:
        name = pf.system().lower()
        if name == "darwin":
            return "macos"
        elif name == "linux":
            return "android64"
        elif name == "windows":
            return "windows"
        else:
            raise ValueError(f"Unexpected host platform '{name}', explicitly pass the target platform using --platform")

    def should_build(self, package_name: str) -> bool:
        if self.rebuild_whitelist and package_name not in self.rebuild_whitelist:
            cprint(f"Skipping build for {package_name} since it's not in the whitelist (--only)", Color.YELLOW)
            return False
        return True

    def cross_compiling(self) -> bool:
        name = pf.system().lower()
        if name == "darwin":
            return self.platform != "macos"
        elif name == "windows":
            return self.platform != "windows"
        else:
            # all other are cross compilation
            return True

    def find_cc(self) -> str:
        return strpath(self._find("cc"))

    def find_cxx(self) -> str:
        return strpath(self._find("cxx"))

    def find_ar(self) -> str:
        return strpath(self._find("ar"))

    def find_ranlib(self) -> str:
        return strpath(self._find("ranlib"))

    def find_sysroot(self) -> str:
        return strpath(self._find("sysroot"))

    def _find(self, what: str) -> Path:
        if "android" in self.platform:
            assert self.ndk_path
            toolchain = find_android_toolchain(self.ndk_path)
            bin = toolchain / "bin"

            if what == "ar" or what == "ranlib":
                return bin / f"llvm-{what}"

            triple = self.target_triple()
            llvmtriple = triple.replace("armv7", "armv7a")

            suffix = "" if what == "cc" else "++"
            return toolchain / "bin" / f"{llvmtriple}{ANDROID_SDK_VERSION}-clang{suffix}"
        elif self.platform == "ios" or self.platform == "macos":
            xcrun = shutil.which("xcrun") or "xcrun"
            sdk = "iphoneos" if self.platform == "ios" else "macosx"

            if what == "sysroot":
                return Path(subprocess.check_output([xcrun, "--sdk", sdk, "--show-sdk-path"], text=True).strip())
            else:
                whatmap = {
                    "cc": "clang",
                    "cxx": "clang++",
                }
                return Path(subprocess.check_output([xcrun, "--sdk", sdk, "-f", whatmap.get(what, what)], text=True).strip())
        elif self.platform == "windows":
            whatmap = {
                "cc": "clang-cl",
                "cxx": "clang-cl",
                "ar": "llvm-lib",
                "ranlib": "llvm-lib",
            }
            what = whatmap.get(what, what)
            return Path(shutil.which(what) or what)

        # default, unknown
        cprint(f"Could not find tool '{what}' for platform '{self.platform}', falling back to path-based resolution", Color.YELLOW)
        return Path(shutil.which(what) or what)


def clone_package(repo: str, tag: str, path: Path):
    p = Popen(["git", "clone", "--no-checkout", repo, str(path)], stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise BuildException(f"Failed to clone {repo} at tag {tag}:\n{stdout.decode()}\n{stderr.decode()}")

def verify_package(repo: str, tag: str, path: Path):
    if not path.exists() or not (path / ".git").exists():
        cprint(f"Cloning {repo} ({tag})...", Color.CYAN)
        clone_package(repo, tag, path)

    # fetch & update to the right version
    Popen(["git", "fetch"], cwd=path, stdout=PIPE, stderr=PIPE).wait()
    p = Popen(["git", "checkout", tag], cwd=path, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        raise BuildException(f"Failed to checkout {repo} at tag {tag}:\n{stdout.decode()}\n{stderr.decode()}")

def verify_packages(parent: Path, config: BuildConfig):
    for (repo, tag) in REPOS:
        name = repo.rpartition("/")[-1]
        is_enabled = True
        match name:
            case "rustls-ffi":
                is_enabled = config.tls == TlsBackend.Rustls
            case "c-ares":
                is_enabled = config.use_ares
            case "openssl":
                is_enabled = config.tls == TlsBackend.OpenSSL

        if not is_enabled:
            continue

        path = parent / name
        if not config.skip_lib_verify:
            verify_package(repo, tag, path)

def find_android_toolchain(ndk_root: Path) -> Path:
    toolchains = list((ndk_root / "toolchains").glob("llvm/prebuilt/*"))
    if not toolchains:
        raise BuildException(f"No Android toolchains found in {ndk_root / 'toolchains/llvm/prebuilt'}!")

    if len(toolchains) > 1:
        cprint(f"Warning: Multiple Android toolchains found in {ndk_root / 'toolchains/llvm/prebuilt'}! Using the first one: {toolchains[0]}", Color.YELLOW)

    return toolchains[0]

def find_vcvars() -> Path:
    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    if not vswhere.exists():
        raise BuildException("vswhere.exe not found, is Visual Studio installed?")

    result = subprocess.run(
        [str(vswhere), "-latest", "-property", "installationPath"],
        capture_output=True, text=True, check=True
    )
    path = Path(result.stdout.strip())
    vcvars = path / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not vcvars.exists():
        raise BuildException(f"vcvars64.bat not found at expected location {vcvars}!")

    return vcvars

def merge_macos_libraries(arm64_path: Path, x64_path: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not arm64_path.exists() or not x64_path.exists():
        raise BuildException(f"Cannot merge macOS libraries, one of the architectures failed to build! arm64: {arm64_path.exists()}, x64: {x64_path.exists()}")

    lipo = shutil.which("lipo") or "lipo"
    r = Popen([lipo, "-create", "-output", str(out_path), str(x64_path), str(arm64_path)], stderr=STDOUT).wait()
    if r != 0:
        raise BuildException(f"Failed to create universal binary with lipo for {out_path}!")

def build_rustls(path: Path, install_dir: Path, config: BuildConfig):
    if not config.should_build("rustls"):
        return

    # check if cargo is installed
    cargo = shutil.which("cargo")
    if not cargo:
        raise BuildException("Cargo is not installed or not found in PATH!")

    # check if cargo-c is installed
    p = Popen([cargo, "capi"], stdout=PIPE, stderr=PIPE).wait()
    if p != 0:
        raise BuildException("cargo-c is not installed! Please install it with `cargo install cargo-c`")

    args = [
        cargo, "capi", "install",
        "--library-type", "staticlib",
        "--no-default-features",
        "--features=ring"
    ]
    if config.profile != "Debug":
        args.append("--release")

    env = os.environ.copy()
    env.update(config.cmake_env)
    if "android" in config.platform:
        assert config.ndk_path and config.ndk_path.exists(), "NDK path must be specified and exist for Android builds!"

        triple = config.target_triple()
        env["CC"] = config.find_cc()
        env["CXX"] = config.find_cxx()
        env["AR"] = config.find_ar()
        env["CARGO_TARGET_" + triple.upper().replace("-", "_") + "_LINKER"] = env["CC"]

    if config.platform == "macos":
        tmp_arm64 = install_dir / "tmp-rustls-arm64"
        tmp_x64 = install_dir / "tmp-rustls-x64"
        if tmp_arm64.exists():
            shutil.rmtree(tmp_arm64)
        if tmp_x64.exists():
            shutil.rmtree(tmp_x64)

        x64args = args + ["--target", "x86_64-apple-darwin", "--prefix", tmp_x64]
        arm64args = args + ["--target", "aarch64-apple-darwin", "--prefix", tmp_arm64]

        print(' '.join(map(str, x64args)))
        r = Popen(x64args, cwd=path, stderr=STDOUT, env=env).wait()
        if r != 0:
            raise BuildException(f"Failed to build rustls for macOS (x64)!")
        print(' '.join(map(str, arm64args)))
        r = Popen(arm64args, cwd=path, stderr=STDOUT, env=env).wait()
        if r != 0:
            raise BuildException(f"Failed to build rustls for macOS (arm64)!")

        # create a universal binary
        x64lib = tmp_x64 / "lib" / "librustls.a"
        arm64lib = tmp_arm64 / "lib" / "librustls.a"
        outlib = install_dir / "lib" / "librustls.a"
        merge_macos_libraries(arm64lib, x64lib, outlib)

        # copy the include dir
        shutil.copytree(tmp_x64 / "include", install_dir / "include", dirs_exist_ok=True)

        # delete the tmp dirs
        shutil.rmtree(tmp_arm64)
        shutil.rmtree(tmp_x64)

    else:
        args.extend((
            "--target", config.target_triple(),
            "--prefix", str(install_dir),
        ))
        print(' '.join(args))
        r = Popen(args, cwd=path, stderr=STDOUT, env=env).wait()
        if r != 0:
            raise BuildException(f"Failed to build rustls!")

        libpath = install_dir / "lib" / ("librustls.a" if config.platform != "windows" else "rustls.lib")
        if not libpath.exists():
            raise BuildException(f"Failed to find built rustls library at {libpath}!")

def build_openssl_one(path: Path, install_dir: Path, platform: str, config: BuildConfig):
    make = shutil.which("make") or "make"

    # run make distclean before builds, otherwise some issues may arise
    if platform != "windows":
        cleanargs = [make, "distclean"]
        print(' '.join(cleanargs))
        subprocess.run(cleanargs, cwd=path, stderr=STDOUT, check=False)

    # pain begins here..
    env = os.environ.copy()
    env.update(config.cmake_env)

    cflags = []
    args = [str(path / "Configure")]
    mapping = {
        "android32": "android-arm",
        "android64": "android-arm64",
        "windows": "VC-WIN64A",
        "ios": "ios64-cross",
        "macos-x64": "darwin64-x86_64-cc",
        "macos-arm64": "darwin64-arm64-cc",
    }
    args.append(mapping[platform])
    args.append(f"--prefix={install_dir}")
    args.append(f"--openssldir={install_dir}/ssl")

    # dont build things we will not use
    args.append("no-shared")
    args.append("no-docs")
    args.append("no-tests")
    args.append("no-apps")
    args.append("no-module")
    args.append("no-engine")
    args.append("no-async")
    args.append("no-makedepend")
    args.append("no-deprecated")

    args.append("no-ssl3")
    args.append("no-comp")
    args.append("no-idea")
    args.append("no-md2")
    args.append("no-rc4")
    args.append("no-rc2")
    args.append("no-fips")
    args.append("no-srp")
    # required for android, otherwise we get
    # relocation R_AARCH64_ADR_PREL_PG_HI21 cannot be used against symbol 'ssl_undefined_function'; recompile with -fPIC
    args.append("enable-pic")

    if "android" in platform:
        assert config.ndk_path
        env["ANDROID_NDK_ROOT"] = str(config.ndk_path)
        toolchain = find_android_toolchain(config.ndk_path)
        env["PATH"] = str(toolchain / "bin") + os.pathsep + env.get("PATH", "")
        args.append(f"-D__ANDROID_API__={ANDROID_SDK_VERSION}")
        cflags.append("-Wno-macro-redefined")

    elif platform == "windows":
        perl = config.perl_path
        if not perl:
            raise BuildException("Perl is required to build OpenSSL on Windows but was not found in PATH or passed via --perl-path!")

        args.insert(0, str(perl))
        perl_dir = str(perl.parent)
        env["PATH"] = perl_dir + os.pathsep + env.get("PATH", "")

        if OPENSSL_CLANG:
            env["CC"] = "clang-cl"
            env["CXX"] = "clang-cl"
            env["AR"] = "llvm-lib"
            env["LD"] = "clang-cl"
            # clang-cl does not create a .pdb file, so let's make a dummy file so the build doesn't fail
            (path / "ossl_static.pdb").touch()

    elif platform == "ios":
        cflags.extend(f"-isysroot {config.sysroot} -arch arm64 -mios-version-min={MIN_IOS_VERSION}".split())
        env["LDFLAGS"] = f"-isysroot {config.sysroot} -arch arm64 -mios-version-min={MIN_IOS_VERSION}"
    elif "macos" in platform:
        args.append(f"-mmacosx-version-min={MIN_MACOS_VERSION}")

    if config.lto:
        cflags.append("-flto=thin")

    env["CFLAGS"] = env.get("CFLAGS", "") + " " + " ".join(cflags)

    # configure
    print(' '.join(args))
    r = Popen(args, cwd=path, env=env, stderr=STDOUT).wait()
    if r != 0:
        raise BuildException(f"Failed to configure OpenSSL!")

    if platform == "windows":
        # thought it would be that simple?
        vcvars_path = find_vcvars()
        wrapper = config.build_dir / "build_openssl.bat"
        wrapper.write_text(f"""
@echo off
call "{vcvars_path}" >nul
if errorlevel 1 exit /b %errorlevel%

nmake
if errorlevel 1 exit /b %errorlevel%

nmake install_sw
exit /b %errorlevel%
""")
        subprocess.run(["cmd.exe", "/c", str(wrapper)], cwd=path, env=env, check=True)

        # delete the dummy pdb file
        if OPENSSL_CLANG:
            pdb_path = (install_dir / "lib" / "ossl_static.pdb")
            pdb_path.unlink(True)
    else:
        nproc = os.cpu_count() or 1
        build_args = [make, f"-j{nproc}"]

        print(' '.join(build_args))
        r = Popen(build_args, cwd=path, env=env, stderr=STDOUT).wait()
        if r != 0:
            raise BuildException(f"Failed to build OpenSSL!")
        Popen([make, "install_sw"], cwd=path, env=env, stderr=STDOUT).wait()

def build_openssl(path: Path, install_dir: Path, config: BuildConfig):
    if not config.should_build("openssl"):
        return

    if config.platform != "macos":
        return build_openssl_one(path, install_dir, config.platform, config)

    # build both arm64 and x64 and create a universal binary
    tmp_arm64 = install_dir / "tmp-ossl-arm64"
    tmp_x64 = install_dir / "tmp-ossl-x64"
    if tmp_arm64.exists():
        shutil.rmtree(tmp_arm64)
    if tmp_x64.exists():
        shutil.rmtree(tmp_x64)

    build_openssl_one(path, tmp_x64, "macos-x64", config)
    build_openssl_one(path, tmp_arm64, "macos-arm64", config)

    crypto_x64 = tmp_x64 / "lib" / "libcrypto.a"
    crypto_arm64 = tmp_arm64 / "lib" / "libcrypto.a"
    crypto_out = install_dir / "lib" / "libcrypto.a"
    merge_macos_libraries(crypto_arm64, crypto_x64, crypto_out)

    ssl_x64 = tmp_x64 / "lib" / "libssl.a"
    ssl_arm64 = tmp_arm64 / "lib" / "libssl.a"
    ssl_out = install_dir / "lib" / "libssl.a"
    merge_macos_libraries(ssl_arm64, ssl_x64, ssl_out)

    # copy the include dir
    shutil.copytree(tmp_x64 / "include", install_dir / "include", dirs_exist_ok=True)

    # delete the tmp dirs
    shutil.rmtree(tmp_arm64)
    shutil.rmtree(tmp_x64)

def build_one(path: Path, install_dir: Path, config: BuildConfig, extra_args: list[str] | None = None):
    lib_name = install_dir.name
    if not config.should_build(lib_name):
        return

    build_dir = path / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

    cmake_args = config.cmake_args + (extra_args if extra_args else [])
    cmake_args.append(f"-DCMAKE_INSTALL_PREFIX={install_dir}")
    cmake_args.append(f"-DCMAKE_BUILD_TYPE={config.profile}")

    if config.lto:
        cmake_args.append("-DCMAKE_CXX_FLAGS=-flto=thin")
        cmake_args.append("-DCMAKE_C_FLAGS=-flto=thin")
        cmake_args.append(f"-DCMAKE_AR={config.find_ar()}")
        cmake_args.append(f"-DCMAKE_RANLIB={config.find_ranlib()}")

    if config.platform == "windows":
        # use clang-cl
        cmake_args.append(f"-DCMAKE_C_COMPILER={config.find_cc()}")
        cmake_args.append(f"-DCMAKE_CXX_COMPILER={config.find_cxx()}")
        cmake_args.append(f"-DCMAKE_LINKER=lld-link")

    if config.generator:
        cmake_args.extend(("-G", config.generator))
    cmake_args.extend(("-S", str(path)))
    cmake_args.extend(("-B", str(build_dir)))

    cmake = shutil.which("cmake") or "cmake"
    env = os.environ.copy()
    env.update(config.cmake_env)

    cprint(f"Configuring {lib_name}..", Color.BLUE)
    print(f"{cmake} {' '.join(cmake_args)}")
    r = Popen(
        [cmake] + cmake_args,
        env=env,
        stderr=STDOUT
    ).wait()
    if r != 0:
        raise BuildException(f"CMake configuration failed for {lib_name}!")

    # build
    cprint(f"Building {lib_name}..", Color.BLUE)
    build_args = [cmake, "--build", str(build_dir), "--target", "install", "--config", config.profile, "--parallel"]
    print(' '.join(build_args))
    r = Popen(
        build_args,
        env=env,
        stderr=STDOUT
    ).wait()
    if r != 0:
        raise BuildException(f"Build failed for {lib_name}!")

def build(config: BuildConfig):
    tls_str = config.tls.name if config.tls else "none"
    gen_str = config.generator or "default"
    cprint(
        f"Building for {config.platform} (TLS: {tls_str}, generator: {gen_str}, profile: {config.profile})",
        Color.GREEN
    )

    src_dir = config.build_dir / "sources"
    out_dir = config.output_path
    if out_dir.exists() and not config.rebuild_whitelist:
        # remove the out dir if we rebuild all packages
        shutil.rmtree(out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Verifying or installing packages...")
    verify_packages(src_dir, config)

    curl_args = []
    def add_linked_library(name: str, path: Path, libname: str | None = None):
        if libname is None:
            if config.platform == "windows":
                libname = f"{name}.lib"
            else:
                libname = f"lib{name}.a"

        inc_path = path / 'include'
        lib_path = path / 'lib' / libname
        if not inc_path.exists():
            raise BuildException(f"Include directory for {name} not found at {inc_path}!")
        if not lib_path.exists():
            raise BuildException(f"Library file for {name} not found at {lib_path}!")

        curl_args.append(f"-D{name.upper()}_INCLUDE_DIR={inc_path}")
        curl_args.append(f"-D{name.upper()}_LIBRARY={lib_path}")

    def add_linked_library_openssl(path: Path):
        # verify existence
        inc_path = path / 'include'
        if not inc_path.exists():
            raise BuildException(f"Include directory for openssl not found at {inc_path}!")

        libs_path = path / 'lib'
        for component in ("ssl", "crypto"):
            if config.platform == "windows":
                libname = f"lib{component}.lib"
            else:
                libname = f"lib{component}.a"

            lib_path = libs_path / libname

            if not lib_path.exists():
                raise BuildException(f"Library file for {component} (openssl) not found at {lib_path}!")

        curl_args.append(f"-DOPENSSL_ROOT_DIR={path}")
        if config.cross_compiling():
            # :p
            curl_args.extend(("-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=BOTH", "-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=BOTH"))

    # build the tls library
    if config.tls != TlsBackend.OpenSSL:
        curl_args.append("-DCURL_USE_OPENSSL=OFF")

    if config.tls is None:
        curl_args.append("-DCURL_ENABLE_SSL=OFF")
    else:
        curl_args.append("-DCURL_ENABLE_SSL=ON")

    match config.tls:
        case TlsBackend.Rustls:
            build_rustls(src_dir / "rustls-ffi", out_dir / "rustls", config)
            curl_args.append("-DCURL_USE_RUSTLS=ON")
            curl_args.append("-DHAVE_RUSTLS_SUPPORTED_HPKE=ON")
            add_linked_library("rustls", out_dir / "rustls")

        case TlsBackend.SChannel:
            curl_args.append("-DCURL_USE_SCHANNEL=ON")

        case TlsBackend.OpenSSL:
            build_openssl(src_dir / "openssl", out_dir / "openssl", config)
            curl_args.append("-DCURL_USE_OPENSSL=ON")
            add_linked_library_openssl(out_dir / "openssl")

    # patch c-ares to not use deprecated ucrt functions
    if config.platform == "windows":
        ares_cmake = src_dir / "c-ares" / "CMakeLists.txt"
        cmake_text = ares_cmake.read_text()
        for func in ("strcasecmp", "strcmpi", "strdup", "stricmp", "strncasecmp", "strncmpi", "strnicmp"):
            cmake_text = cmake_text.replace(
                f"CHECK_SYMBOL_EXISTS ({func}",
                f"CHECK_SYMBOL_EXISTS (__invalid_func_{func}"
            )
        ares_cmake.write_text(cmake_text)

    # build c-ares
    if config.use_ares:
        build_one(src_dir / "c-ares", out_dir / "c-ares", config, [
            "-DCARES_STATIC=ON",
            "-DCARES_SHARED=OFF",
            "-DCARES_BUILD_TESTS=OFF",
            "-DCARES_BUILD_TOOLS=OFF",
        ])
        curl_args.append("-DENABLE_ARES=ON")
        add_linked_library("cares", out_dir / "c-ares")

        # remove man pages and docs from build
        share = out_dir / "c-ares" / "share"
        if share.exists():
            shutil.rmtree(share)

    # build zstd
    build_one(src_dir / "zstd" / "build" / "cmake", out_dir / "zstd", config, [
        "-DZSTD_BUILD_SHARED=OFF",
        "-DZSTD_BUILD_STATIC=ON",
        "-DZSTD_BUILD_PROGRAMS=OFF",
        "-DZSTD_BUILD_TESTS=OFF",
        "-DZSTD_BUILD_CONTRIB=OFF",
        "-DZSTD_MULTITHREAD_SUPPORT=OFF",
        "-DZSTD_LEGACY_SUPPORT=OFF",
    ])
    curl_args.append("-DCURL_ZSTD=ON")
    add_linked_library("zstd", out_dir / "zstd", "zstd_static.lib" if config.platform == "windows" else "libzstd.a")

    # patch zlib to not use deprecated ucrt functions
    gzgutsfile = src_dir / "zlib" / "gzguts.h"
    gzguts = gzgutsfile.read_text()
    if "# define open _open" not in gzguts:
        gzguts = gzguts + "\n#if defined(_WIN32)\n" \
            "# define open _open\n" \
            "# define read _read\n" \
            "# define write _write\n" \
            "# define close _close\n" \
            "#endif\n"
    gzgutsfile.write_text(gzguts)

    # build zlib
    build_one(src_dir / "zlib", out_dir / "zlib", config, [
        "-DZLIB_BUILD_TESTING=OFF",
        "-DZLIB_BUILD_SHARED=OFF",
        "-DZLIB_BUILD_STATIC=ON",
    ])
    curl_args.append("-DCURL_ZLIB=ON")
    add_linked_library("zlib", out_dir / "zlib", "zs.lib" if config.platform == "windows" else "libz.a")

    # build nghttp2
    build_one(src_dir / "nghttp2", out_dir / "nghttp2", config, [
        "-DENABLE_LIB_ONLY=ON",
        "-DENABLE_EXAMPLES=OFF",
        "-DBUILD_TESTING=OFF",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_STATIC_LIBS=ON"
    ])
    curl_args.append("-DUSE_NGHTTP2=ON")
    add_linked_library("nghttp2", out_dir / "nghttp2")

    # this is a tiny fix because curl tries to link nghttp2 dynamically :(
    verfile = out_dir / "nghttp2" / "include" / "nghttp2" / "nghttp2ver.h"
    verfiletext = verfile.read_text()
    if "#define NGHTTP2_STATICLIB 1" not in verfiletext:
        verfiletext = verfiletext.replace(
            "#endif", "#define NGHTTP2_STATICLIB 1\n\n#endif"
        )
    verfile.write_text(verfiletext)

    # build curl
    build_one(src_dir / "curl", out_dir / "curl", config, curl_args + [
        "-DCURL_DISABLE_FTP=ON",
        "-DCURL_DISABLE_TELNET=ON",
        "-DCURL_DISABLE_LDAP=ON",
        "-DCURL_DISABLE_DICT=ON",
        "-DCURL_DISABLE_TFTP=ON",
        "-DCURL_DISABLE_GOPHER=ON",
        "-DCURL_DISABLE_POP3=ON",
        "-DCURL_DISABLE_IMAP=ON",
        "-DCURL_DISABLE_SMB=ON",
        "-DCURL_DISABLE_SMTP=ON",
        "-DCURL_DISABLE_IPFS=ON",
        "-DCURL_DISABLE_RTSP=ON",
        "-DCURL_DISABLE_MQTT=ON",
        "-DCURL_DISABLE_NTLM=ON",
        "-DCURL_DISABLE_SRP=ON",
        "-DCURL_DISABLE_WEBSOCKETS=ON",
        "-DCURL_DISABLE_KERBEROS_AUTH=ON",
        "-DCURL_DISABLE_NEGOTIATE_AUTH=ON",
        "-DCURL_DISABLE_AWS=ON",
        "-DCURL_DISABLE_PROGRESS_METER=ON",
        "-DCURL_WINDOWS_SSPI=OFF",
        "-DCURL_USE_LIBSSH2=OFF",
        "-DCURL_USE_LIBSSH=OFF",
        "-DCURL_USE_LIBPSL=OFF",
        "-DCURL_BROTLI=OFF",
        "-DUSE_APPLE_IDN=OFF",
        "-DUSE_WIN32_IDN=OFF",
        "-DUSE_LIBIDN2=OFF",
        "-DBUILD_CURL_EXE=OFF",
        "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_STATIC_LIBS=ON",
        "-DBUILD_LIBCURL_DOCS=OFF",
        "-DBUILD_MISC_DOCS=OFF",
        "-DENABLE_CURL_MANUAL=OFF",
    ])

    # flatten the output
    if config.flatten_output:
        cprint("Flattening output directory..", Color.BLUE)

        include_dir = config.output_path / "include"
        include_dir.mkdir(exist_ok=True)

        ext = "*.lib" if config.platform == "windows" else "*.a"
        for path in config.output_path.glob(f"**/{ext}"):
            shutil.copy(path, config.output_path / path.name)
        for path in config.output_path.glob("**/*.pdb"):
            shutil.copy(path, config.output_path / path.name)

        for entry in list(config.output_path.iterdir()):
            if not entry.is_dir() or entry.name == "include":
                continue
            inc = entry / "include"
            if not inc.exists() or not inc.is_dir():
                continue

            for path in inc.rglob('*'):
                if not path.is_file():
                    continue
                rel_path = path.relative_to(inc)
                dest_path = include_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest_path)

        for d in list(config.output_path.iterdir()):
            if d.name != "include" and d.is_dir():
                shutil.rmtree(d)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build net_libs for the given platform")
    parser.add_argument('-p', "--platform", type=str, default="", help="The platform to build for")
    parser.add_argument("--tls", type=str, default="", help="The TLS backend to build with")
    parser.add_argument("--debug", action="store_true", help="Whether to build in debug mode")
    parser.add_argument('-o', "--output", type=Path, default=Path.cwd() / "out", help="The output directory for the built libraries")
    parser.add_argument("--build-dir", type=Path, default=Path.cwd() / "build", help="The intermediate build directory")
    parser.add_argument("--ndk-path", type=str, default="", help="The intermediate build directory")
    parser.add_argument("--generator", type=str, default="", help="The CMake generator to use (e.g. Ninja, Visual Studio 16 2019, etc.)")
    parser.add_argument("--clean", action="store_true", help="Whether to rebuild & reclone from scratch")
    parser.add_argument("--toolchain", type=str, required=False, help="The CMake toolchain file to use (for cross-compilation)")
    parser.add_argument("--splat", type=str, required=False, help="Splat dir for cross-compiling to Windows, if passed, configures other cross-compilation things as well")
    parser.add_argument("--flat-output", action="store_true", help="Only keep the output library files and curl includes at the end")
    parser.add_argument("--lto", action="store_true", help="Whether to enable LTO")
    parser.add_argument("--only", type=str, default="", help="Only rebuild the given packages, comma separated")
    parser.add_argument("--skip-lib-verify", action="store_true", help="Skip verification of git repos")
    parser.add_argument("--perl-path", type=Path, required=False, help="The path to the Perl executable (if not in PATH)")

    args = parser.parse_args()
    if not args.platform:
        platform = BuildConfig.determine_platform()
    else:
        platform = args.platform.lower()

    if args.clean:
        assert args.output != Path("/"), "Refusing to delete root directory!"
        assert args.build_dir != Path("/"), "Refusing to delete root directory!"

        if args.output.exists():
            shutil.rmtree(args.output)
        if args.build_dir.exists():
            shutil.rmtree(args.build_dir)

    # create config
    config = BuildConfig.for_platform(platform)

    if args.tls:
        config.tls = TlsBackend.from_str(args.tls)
    config.output_path = (args.output / platform).absolute()
    config.build_dir = args.build_dir.absolute()
    config.profile = "Debug" if args.debug else "Release"
    config.flatten_output = args.flat_output
    config.lto = args.lto
    config.rebuild_whitelist = set(args.only.split(",")) if args.only else set()
    config.skip_lib_verify = args.skip_lib_verify
    config.perl_path = args.perl_path or Path(shutil.which("perl") or "perl")
    if args.generator:
        config.generator = args.generator
    else:
        # default to Ninja if available, otherwise let cmake decide
        if shutil.which("ninja"):
            config.generator = "Ninja"

    if args.splat:
        config.cmake_args.append(f"-DSPLAT_DIR={args.splat}")
        config.cmake_args.append(f"-DHOST_ARCH=x64")

        symlinks_dir = os.getenv("_winsdk_lib_symlinks_dir", os.getenv("winsdk_lib_symlinks_dir", str(config.build_dir / "winsdk-symlinks")))
        config.cmake_env["_winsdk_lib_symlinks_dir"] = symlinks_dir
        cprint(f"Using symlinks dir for Windows SDK libraries: {symlinks_dir}", Color.BLUE)

    # manually specified toolchain
    if args.toolchain:
        config.cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={args.toolchain}")

    # Android NDK and toolchain setup
    if "android" in platform:
        ndk = args.ndk_path
        if not ndk:
            ndk = os.getenv("ANDROID_NDK_HOME", "")
        if not ndk:
            ndk = os.getenv("ANDROID_NDK_ROOT", "")
        if not ndk:
            cprint("Error: Android NDK path not specified. Use --ndk-path or set ANDROID_NDK_HOME/ANDROID_NDK_ROOT environment variable.", Color.RED)
            exit(1)

        config.ndk_path = Path(ndk)

        # don't override toolchain if explicitly passed
        if not args.toolchain:
            config.cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={ndk}/build/cmake/android.toolchain.cmake")

    # do the actual build
    try:
        start = time.perf_counter()
        build(config)
        taken = time.perf_counter() - start
        cprint(f"Build succeeded for {config.platform} in {taken:.2f} seconds!", Color.GREEN)
    except BuildException as e:
        cprint(f"Build failed for {config.platform}!", Color.RED)
        cprint(str(e), Color.RED)
        exit(1)
    except Exception as e:
        cprint(f"Build failed for {config.platform} with an unexpected error!", Color.RED)
        traceback.print_exc()
        exit(1)
