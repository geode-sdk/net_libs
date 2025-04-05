#!/bin/zsh

# TODO: this script was copied from build_macos.sh and then some adjustments were done for ios
# it also does not build ngtcp2 or nghttp3, so the output libcurl will lack QUIC support unlike other platforms
# (sorry, i could not figure out why it wasn't compiling, but feel free to do it if you care enough :) )
# - dank

ROOT=$PWD
BUILD_PATH="$ROOT/build/ios"
OUT_PATH="$ROOT/out/ios"

COMMON_FLAGS=(
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="$OUT_PATH"
    -DCMAKE_SYSTEM_NAME=iOS
    -DCMAKE_OSX_SYSROOT=$(xcrun --sdk iphoneos --show-sdk-path)
    -DCMAKE_OSX_ARCHITECTURES="arm64"
    -DCMAKE_OSX_DEPLOYMENT_TARGET="14.0"
    -DCMAKE_IOS_INSTALL_COMBINED=YES
)

# Remove previous output files

rm -rf "$OUT_PATH"

# Build BoringSSL

rm -rf "$BUILD_PATH/boringssl"
mkdir -p "$BUILD_PATH/boringssl"
cd "$BUILD_PATH/boringssl"

cmake "${COMMON_FLAGS[@]}" -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_MACOSX_BUNDLE=NO "$ROOT/boringssl"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build nghttp2

rm -rf "$BUILD_PATH/nghttp2"
mkdir -p "$BUILD_PATH/nghttp2"
cd "$BUILD_PATH/nghttp2"

cmake -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON \
      "${COMMON_FLAGS[@]}"  "$ROOT/nghttp2"
make -j$(sysctl -n hw.ncpu)
make install
make clean

# Build curl

rm -rf "$BUILD_PATH/curl"
mkdir -p "$BUILD_PATH/curl"
cd "$BUILD_PATH/curl"

cmake "${COMMON_FLAGS[@]}" -DBUILD_CURL_EXE=OFF \
    -DCURL_DISABLE_LDAP=ON -DCURL_USE_OPENSSL=ON -DOPENSSL_INCLUDE_DIR="$OUT_PATH/include" \
    -DOPENSSL_CRYPTO_LIBRARY="$OUT_PATH/lib/libcrypto.a" -DOPENSSL_SSL_LIBRARY="$OUT_PATH/lib/libssl.a" \
    -DOPENSSL_LIBRARIES="$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a" \
    -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP2_LIBRARY="$OUT_PATH/lib/libnghttp2.a" \
    -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/curl"
make -j$(sysctl -n hw.ncpu)
make install
make clean
