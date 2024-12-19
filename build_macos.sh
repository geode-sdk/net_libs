#!/bin/zsh

ROOT=$PWD
BUILD_PATH="$ROOT/build/macos"
OUT_PATH="$ROOT/out/macos"

export CMAKE_OSX_ARCHITECTURES="x86_64;arm64"
export MACOSX_DEPLOYMENT_TARGET="10.15"

rm -rf "$OUT_PATH"

build_library() {
    local project_name="$1"
    local cmake_flags="$2"
    local build_dir="$BUILD_PATH/$project_name"

    rm -rf "$build_dir"
    mkdir -p "$build_dir"
    cd "$build_dir"

    cmake $cmake_flags "$ROOT/$project_name"
    make -j$(sysctl -n hw.ncpu)
    make install
    make clean
}

build_library "boringssl" "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=\"$OUT_PATH\" -DCMAKE_POSITION_INDEPENDENT_CODE=ON"
build_library "nghttp2" "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=\"$OUT_PATH\" -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON"
build_library "ngtcp2" "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=\"$OUT_PATH\" -DBUILD_TESTING=OFF -DENABLE_BORINGSSL=ON -DBORINGSSL_INCLUDE_DIR=\"$OUT_PATH/include\" -DBORINGSSL_LIBRARIES=\"$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a\" -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"
build_library "nghttp3" "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=\"$OUT_PATH\" -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF -DBUILD_TESTING=OFF -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON"
build_library "curl" "-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=\"$OUT_PATH\" -DBUILD_CURL_EXE=OFF -DCURL_DISABLE_LDAP=ON -DCURL_USE_OPENSSL=ON -DOPENSSL_INCLUDE_DIR=\"$OUT_PATH/include\" -DOPENSSL_CRYPTO_LIBRARY=\"$OUT_PATH/lib/libcrypto.a\" -DOPENSSL_SSL_LIBRARY=\"$OUT_PATH/lib/libssl.a\" -DOPENSSL_LIBRARIES=\"$OUT_PATH/lib/libcrypto.a;$OUT_PATH/lib/libssl.a\" -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR=\"$OUT_PATH/include\" -DNGHTTP2_LIBRARY=\"$OUT_PATH/lib/libnghttp2.a\" -DUSE_NGTCP2=ON -DNGTCP2_INCLUDE_DIR=\"$OUT_PATH/include\" -DNGTCP2_LIBRARY=\"$OUT_PATH/lib/libngtcp2.a\" -Dngtcp2_crypto_boringssl_LIBRARY=\"$OUT_PATH/lib/libngtcp2_crypto_boringssl.a\" -DNGHTTP3_INCLUDE_DIR=\"$OUT_PATH/include\" -DNGHTTP3_LIBRARY=\"$OUT_PATH/lib/libnghttp3.a\" -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON"
