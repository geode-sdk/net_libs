# Networking Libs

Build curl (8.18.0) with
- TLS (Schannel / Rustls, configurable)
- HTTP2 (nghttp2 1.68.1)

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

Using Rustls may require extra setup to cross-compile:
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
