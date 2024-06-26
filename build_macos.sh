#!/bin/zsh

ROOT=$PWD
BUILD_PATH="$ROOT/build/macos"
OUT_PATH="$ROOT/out/macos"

export CMAKE_OSX_ARCHITECTURES="x86_64;arm64"
export MACOSX_DEPLOYMENT_TARGET="10.15"

# Remove previous output files

rm -rf "$OUT_PATH"

# Build BoringSSL

rm -rf "$BUILD_PATH/boringssl"
mkdir -p "$BUILD_PATH/boringssl"
cd "$BUILD_PATH/boringssl"

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -DCMAKE_POSITION_INDEPENDENT_CODE=ON "$ROOT/boringssl"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build nghttp2

rm -rf "$BUILD_PATH/nghttp2"
mkdir -p "$BUILD_PATH/nghttp2"
cd "$BUILD_PATH/nghttp2"

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF \
    -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/nghttp2"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build ngtcp2

rm -rf "$BUILD_PATH/ngtcp2"
mkdir -p "$BUILD_PATH/ngtcp2"
cd "$BUILD_PATH/ngtcp2"

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -DBUILD_TESTING=OFF \
    -DENABLE_BORINGSSL=ON -DBORINGSSL_INCLUDE_DIR="$OUT_PATH/include" \
    -DBORINGSSL_LIBRARIES="$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a" \
    -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON "$ROOT/ngtcp2"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build nghttp3

rm -rf "$BUILD_PATH/nghttp3"
mkdir -p "$BUILD_PATH/nghttp3"
cd "$BUILD_PATH/nghttp3"

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF \
    -DBUILD_TESTING=OFF -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON "$ROOT/nghttp3"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build curl

rm -rf "$BUILD_PATH/curl"
mkdir -p "$BUILD_PATH/curl"
cd "$BUILD_PATH/curl"

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -DBUILD_CURL_EXE=OFF \
    -DCURL_DISABLE_LDAP=ON -DCURL_USE_OPENSSL=ON -DOPENSSL_INCLUDE_DIR="$OUT_PATH/include" \
    -DOPENSSL_CRYPTO_LIBRARY="$OUT_PATH/lib/libcrypto.a" -DOPENSSL_SSL_LIBRARY="$OUT_PATH/lib/libssl.a" \
    -DOPENSSL_LIBRARIES="$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a" \
    -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP2_LIBRARY="$OUT_PATH/lib/libnghttp2.a" \
    -DUSE_NGTCP2=ON -DNGTCP2_INCLUDE_DIR="$OUT_PATH/include" -DNGTCP2_LIBRARY="$OUT_PATH/lib/libngtcp2.a" \
    -Dngtcp2_crypto_boringssl_LIBRARY="$OUT_PATH/lib/libngtcp2_crypto_boringssl.a" \
    -DNGHTTP3_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP3_LIBRARY="$OUT_PATH/lib/libnghttp3.a" \
    -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/curl"
make -j$(sysctl -n hw.ncpu)
make install
make clean
