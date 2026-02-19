# Networking Libs

Build curl (v8.18.0) with
- TLS (Schannel / Rustls v0.15.0, configurable)
- HTTP2 (nghttp2 v1.68.1)
- Zlib (v1.3.2) and zstd (v1.5.7) compression
- Async DNS (c-ares 2870f6b)

## Cloning

```
git clone --recurse-submodules -j$(nproc) https://github.com/geode-sdk/net_libs
```

## Build notes

The `build.py` script can build libcurl and other libraries for all platforms. To build for a specific platform:
```py
python build.py -p windows
```

The script has many options for building, for example choosing the TLS library or the DNS backend.

Using OpenSSL as the TLS backend requires it to be installed on the system.

Using Rustls (default on non-Windows) may require extra setup to cross-compile, besides just installing Rust and cargo-c:
```sh
# for android32
rustup target add armv7-linux-androideabi

# for android64
rustup target add aarch64-linux-android

# for macOS
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin

# for iOS
rustup target add aarch64-apple-ios
```

Compilation should work out of the box for the following combinations, given that all the required tools are installed such as iOS SDK, Android NDK, etc. (host -> target)
* Windows -> Windows, Android
* MacOS -> Android, MacOS, iOS
* Linux -> Android

Compiling for Windows on non-Windows platforms requires a cross-compilation toolchain. Pass the paths to `clang-msvc.cmake` and the splat directory:
```sh
TOOLS=~/.local/share/Geode/cross-tools/
python build.py -p windows --toolchain $TOOLS/clang-msvc-sdk/clang-msvc.cmake --splat $TOOLS/splat
```