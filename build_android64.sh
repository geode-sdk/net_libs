#!/bin/bash

ROOT=$PWD
SDK_VER=23

export PATH=$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin:$ANDROID_NDK_ROOT/toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin:$PATH
export ANDROID_NDK_HOME=$ANDROID_NDK_ROOT
export HOST_TAG="linux-x86_64"
export TARGET="aarch64-linux-android"
export TOOLCHAIN="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/$HOST_TAG"
export AR="$TOOLCHAIN/bin/llvm-ar"
export AS="$TOOLCHAIN/bin/llvm-as"
export CC="$TOOLCHAIN/bin/aarch64-linux-android$SDK_VER-clang"
export CXX="$TOOLCHAIN/bin/aarch64-linux-android$SDK_VER-clang++"
export LD="$TOOLCHAIN/bin/ld"
export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export STRIP="$TOOLCHAIN/bin/llvm-strip"

export BUILD_PATH="$ROOT/build/android64"
export OUT_PATH="$ROOT/out/android64"

#rm -rf "$OUT_PATH"

# Build OpenSSL

#rm -rf "$BUILD_PATH/openssl"
#mkdir -p "$BUILD_PATH/openssl"
#cd "$BUILD_PATH/openssl"

#"$ROOT/openssl/Configure" android-arm64 --prefix="$OUT_PATH" -D__ANDROID_API__=$SDK_VER -Wno-macro-redefined
#make -j$(nproc)
#make install_dev
#make clean

# Build nghttp2

#rm -rf "$BUILD_PATH/nghttp2"
#mkdir -p "$BUILD_PATH/nghttp2"
#cd "$BUILD_PATH/nghttp2"

#"$ROOT/nghttp2/configure" --host=$TARGET --prefix="$OUT_PATH" --disable-shared --without-libxml2 --disable-examples \
#    CPPFLAGS="-fPIE -I$OUT_PATH/include" PKG_CONFIG_LIBDIR="$OUT_PATH/lib/pkgconfig" LDFLAGS="-fPIE -pie -L$OUT_PATH/lib"
#make -j$(nproc)
#make install
#make clean

# Build ngtcp2

#rm -rf "$BUILD_PATH/ngtcp2"
#mkdir -p "$BUILD_PATH/ngtcp2"
#cd "$BUILD_PATH/ngtcp2"

#"$ROOT/ngtcp2/configure" --host $TARGET --prefix="$OUT_PATH" --disable-shared
#make -j$(nproc)
#make install
#make clean

# Build curl

rm -rf "$BUILD_PATH/curl"
mkdir -p "$BUILD_PATH/curl"
cd "$BUILD_PATH/curl"

"$ROOT/curl/configure" --host $TARGET --prefix="$OUT_PATH" --with-pic --disable-shared --with-openssl="$OUT_PATH" \
    --with-nghttp2="$OUT_PATH" --with-ngtcp2="$OUT_PATH" --disable-docs \
    LIBS="-lssl -lcrypto -lnghttp2 -lngtcp2" LDFLAGS=-L"$OUT_PATH/lib"
#make -j$(nproc)
#make install
#make clean