#!/bin/bash

ROOT=$PWD
SDK_VER=23
ABI="arm64-v8a"
BUILD_PATH="$ROOT/build/android64"
OUT_PATH="$ROOT/out/android64"

build_library() {
    local module_name=$1
    local extra_cmake_flags=$2

    echo "Building $module_name..."
    
    rm -rf "$BUILD_PATH/$module_name"
    mkdir -p "$BUILD_PATH/$module_name"
    cd "$BUILD_PATH/$module_name"

    cmake -DCMAKE_BUILD_TYPE=Release \
          -DCMAKE_INSTALL_PREFIX="$OUT_PATH" \
          -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
          -DCMAKE_TOOLCHAIN_FILE="$ANDROID_NDK_ROOT/build/cmake/android.toolchain.cmake" \
          -DANDROID_ABI=$ABI \
          -DANDROID_PLATFORM=android-$SDK_VER \
          $extra_cmake_flags \
          "$ROOT/$module_name"

    make -j$(nproc)
    make install
    make clean
}

rm -rf "$OUT_PATH"

build_library "boringssl"
build_library "nghttp2" "-DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON"
build_library "ngtcp2" "-DBUILD_TESTING=OFF -DENABLE_BORINGSSL=ON -DBORINGSSL_INCLUDE_DIR=$OUT_PATH/include -DBORINGSSL_LIBRARIES=$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"
build_library "nghttp3" "-DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF -DBUILD_TESTING=OFF -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"
build_library "curl" "-DBUILD_CURL_EXE=OFF -DCURL_USE_OPENSSL=ON -DOPENSSL_INCLUDE_DIR=$OUT_PATH/include -DOPENSSL_CRYPTO_LIBRARY=$OUT_PATH/lib/libcrypto.a -DOPENSSL_SSL_LIBRARY=$OUT_PATH/lib/libssl.a -DOPENSSL_LIBRARIES=$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR=$OUT_PATH/include -DNGHTTP2_LIBRARY=$OUT_PATH/lib/libnghttp2.a -DUSE_NGTCP2=ON -DNGTCP2_INCLUDE_DIR=$OUT_PATH/include -DNGTCP2_LIBRARY=$OUT_PATH/lib/libngtcp2.a -Dngtcp2_crypto_boringssl_LIBRARY=$OUT_PATH/lib/libngtcp2_crypto_boringssl.a -DNGHTTP3_INCLUDE_DIR=$OUT_PATH/include -DNGHTTP3_LIBRARY=$OUT_PATH/lib/libnghttp3.a"
