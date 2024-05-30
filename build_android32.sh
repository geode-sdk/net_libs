#!/bin/bash

# Build OpenSSL

export PATH=$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin:$ANDROID_NDK_ROOT/toolchains/arm-linux-androideabi-4.9/prebuilt/linux-x86_64/bin:$PATH

rm -rf build/android32/openssl
rm -rf out/android32
mkdir -p build/android32/openssl
cd build/android32/openssl

./../../../openssl/Configure android-arm -D__ANDROID_API__=23 -Wno-macro-redefined
make -j$(nproc)

cd ../../../
mkdir -p out/android32
mv build/android32/openssl/libcrypto.a out/android32/libcrypto.a
mv build/android32/openssl/libssl.a out/android32/libssl.a
llvm-strip out/android32/libcrypto.a
llvm-strip out/android32/libssl.a

# Build CURL

# TODO...