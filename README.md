# Networking Libs

Build curl with
- TLS (BoringSSL)
- HTTP2 (nghttp2)
- HTTP3 (ngtcp2, nghttp3)

## Cloning

```
git clone --recurse-submodules -j$(nproc) https://github.com/geode-sdk/net_libs
```

## Build notes

### Windows build

The powershell script must be launched from a VS dev command line.

### Patching curl

BoringSSL links to `libc++` when compiling for android, macOS. `CMakeFiles.txt` from curl must be modified to allow tests to pass.

1. `project(CURL C)` -> `project(CURL C CXX)`
2. Add `include(CheckCXXSymbolExists)`
3. Locate `openssl_check_symbol_exists` and change `check_symbol_exists` to `check_cxx_symbol_exists` at the end
