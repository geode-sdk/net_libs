$ROOT = $PWD
$NPROC = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors

if ($env:PLATFORM -eq "x86") {
    $BUILD_PATH = "$ROOT/build/windows32"
    $OUT_PATH = "$ROOT/out/windows32"
} elseif ($env:PLATFORM -eq "x64") {
    $BUILD_PATH = "$ROOT/build/windows64"
    $OUT_PATH = "$ROOT/out/windows64"
} else {
    "Invalid Platform!"
    Exit
}

if (Test-Path $OUT_PATH) {
    Remove-Item -Path $OUT_PATH -Recurse | Out-Null
}

if (Test-Path "$BUILD_PATH/boringssl") {
    Remove-Item -Path "$BUILD_PATH/boringssl" -Recurse | Out-Null
}

New-Item -Path $BUILD_PATH -Name "boringssl" -ItemType "directory" | Out-Null
Set-Location -Path "$BUILD_PATH/boringssl" | Out-Null

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja "$ROOT/boringssl"
ninja -j $NPROC
ninja install
ninja clean

if (Test-Path "$BUILD_PATH/nghttp2") {
    Remove-Item -Path "$BUILD_PATH/nghttp2" -Recurse | Out-Null
}

New-Item -Path $BUILD_PATH -Name "nghttp2" -ItemType "directory" | Out-Null
Set-Location -Path "$BUILD_PATH/nghttp2" | Out-Null

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF `
    -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/nghttp2"
ninja -j $NPROC
ninja install
ninja clean

if (Test-Path "$BUILD_PATH/ngtcp2") {
    Remove-Item -Path "$BUILD_PATH/ngtcp2" -Recurse | Out-Null
}

New-Item -Path $BUILD_PATH -Name "ngtcp2" -ItemType "directory" | Out-Null
Set-Location -Path "$BUILD_PATH/ngtcp2" | Out-Null

$BORINGSSL_LIB_PATHS = "$OUT_PATH/lib/crypto.lib;$OUT_PATH/lib/ssl.lib" -replace '[\\]', '/'
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DBUILD_TESTING=OFF `
    -DCMAKE_TRY_COMPILE_CONFIGURATION=Release `
    -DENABLE_BORINGSSL=ON -DBORINGSSL_INCLUDE_DIR="$OUT_PATH/include" -DBORINGSSL_LIBRARIES="$BORINGSSL_LIB_PATHS" `
    -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON "$ROOT/ngtcp2"
ninja -j $NPROC
ninja install
ninja clean

if (Test-Path "$BUILD_PATH/nghttp3") {
    Remove-Item -Path "$BUILD_PATH/nghttp3" -Recurse | Out-Null
}

New-Item -Path $BUILD_PATH -Name "nghttp3" -ItemType "directory" | Out-Null
Set-Location -Path "$BUILD_PATH/nghttp3" | Out-Null

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF `
    -DBUILD_TESTING=OFF -DENABLE_SHARED_LIB=OFF -DENABLE_STATIC_LIB=ON "$ROOT/nghttp3"
ninja -j $NPROC
ninja install
ninja clean

if (Test-Path "$BUILD_PATH/curl") {
    Remove-Item -Path "$BUILD_PATH/curl" -Recurse | Out-Null
}

New-Item -Path $BUILD_PATH -Name "curl" -ItemType "directory" | Out-Null
Set-Location -Path "$BUILD_PATH/curl" | Out-Null

$env:CFLAGS = "-DNGHTTP2_STATICLIB -DNGTCP2_STATICLIB -DNGHTTP3_STATICLIB"
$env:CXXFLAGS = $env:CFLAGS

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DBUILD_CURL_EXE=OFF `
    -D CURL_DISABLE_LDAP=ON -DCURL_USE_OPENSSL=ON -DOPENSSL_INCLUDE_DIR="$OUT_PATH/include" `
    -DOPENSSL_CRYPTO_LIBRARY="$OUT_PATH/lib/crypto.lib" -DOPENSSL_SSL_LIBRARY="$OUT_PATH/lib/ssl.lib" `
    -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP2_LIBRARY="$OUT_PATH/lib/nghttp2.lib" `
    -DUSE_NGTCP2=ON -DNGTCP2_INCLUDE_DIR="$OUT_PATH/include" -DNGTCP2_LIBRARY="$OUT_PATH/lib/ngtcp2.lib" `
    -Dngtcp2_crypto_boringssl_LIBRARY="$OUT_PATH/lib/ngtcp2_crypto_boringssl.lib" `
    -DNGHTTP3_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP3_LIBRARY="$OUT_PATH/lib/nghttp3.lib" `
    -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/curl"
ninja -j $NPROC
ninja install
ninja clean
