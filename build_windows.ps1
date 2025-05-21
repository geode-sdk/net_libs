$ROOT=$PWD
$NPROC=(Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors

if ($env:PLATFORM -eq "x86") {
    $BUILD_PATH="$ROOT/build/windows32"
    $OUT_PATH="$ROOT/out/windows32"
} elseif ($env:PLATFORM -eq "x64") {
    $BUILD_PATH="$ROOT/build/windows64"
    $OUT_PATH="$ROOT/out/windows64"
} else {
    "Invalid Platform!"
    Exit
}

# Remove previous output files

if (Test-Path $OUT_PATH) {
    Remove-Item -Path $OUT_PATH -Recurse | out-null
}

# Build nghttp2

if (Test-Path "$BUILD_PATH/nghttp2") {
    Remove-Item -Path "$BUILD_PATH/nghttp2" -Recurse | out-null
}

New-Item -Path $BUILD_PATH -Name "nghttp2" -ItemType "directory" | out-null
Set-Location -Path "$BUILD_PATH/nghttp2" | out-null

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DENABLE_LIB_ONLY=ON -DENABLE_EXAMPLES=OFF `
    -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/nghttp2"
ninja -j $NPROC
ninja install
ninja clean

# Build curl

if (Test-Path "$BUILD_PATH/curl") {
    Remove-Item -Path "$BUILD_PATH/curl" -Recurse | out-null
}

New-Item -Path $BUILD_PATH -Name "curl" -ItemType "directory" | out-null
Set-Location -Path "$BUILD_PATH/curl" | out-null

$env:CFLAGS="-DNGHTTP2_STATICLIB -DNGTCP2_STATICLIB -DNGHTTP3_STATICLIB"
$env:CXXFLAGS=$env:CFLAGS
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$OUT_PATH" -G Ninja -DBUILD_CURL_EXE=OFF `
    -D CURL_DISABLE_LDAP=ON -DCURL_USE_SCHANNEL=ON `
    -DUSE_NGHTTP2=ON -DNGHTTP2_INCLUDE_DIR="$OUT_PATH/include" -DNGHTTP2_LIBRARY="$OUT_PATH/lib/nghttp2.lib" `
    -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC_LIBS=ON "$ROOT/curl"

ninja -j $NPROC
ninja install
ninja clean