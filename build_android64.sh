#!/bin/bash

# Build OpenSSL

export PATH=$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin:$ANDROID_NDK_ROOT/toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin:$PATH

rm -rf build/android64/openssl
rm -rf out/android64
mkdir -p build/android64/openssl
cd build/android64/openssl

./../../../openssl/Configure android-arm64 -D__ANDROID_API__=23 -Wno-macro-redefined
make -j$(nproc)

cd ../../../
mkdir -p out/android64
mv build/android64/openssl/libcrypto.a out/android64/libcrypto.a
mv build/android64/openssl/libssl.a out/android64/libssl.a
llvm-strip out/android64/libcrypto.a
llvm-strip out/android64/libssl.a

# Build CURL

# TODO...