#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$ROOT/.build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

flutter create --platforms=android --org com.yugenbeyondverse --project-name statsyuri_mobile "$BUILD_DIR"
cp "$ROOT/pubspec.yaml" "$BUILD_DIR/pubspec.yaml"
rm -rf "$BUILD_DIR/lib"
mkdir -p "$BUILD_DIR/lib"
cp "$ROOT/lib/main_v3.dart" "$BUILD_DIR/lib/main.dart"

rm -rf "$BUILD_DIR/android/app/src/main/python"
mkdir -p "$BUILD_DIR/android/app/src/main/python"
cp -R "$ROOT/python/." "$BUILD_DIR/android/app/src/main/python/"

find "$BUILD_DIR/android/app/src/main/kotlin" -name MainActivity.kt -delete
mkdir -p "$BUILD_DIR/android/app/src/main/kotlin/com/yugenbeyondverse/statsyuri_mobile"
cp "$ROOT/android/MainActivity.kt" "$BUILD_DIR/android/app/src/main/kotlin/com/yugenbeyondverse/statsyuri_mobile/MainActivity.kt"

python3 - "$BUILD_DIR" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
app=root/'android/app/build.gradle.kts'
if not app.exists(): app=root/'android/app/build.gradle'
top=root/'android/build.gradle.kts'
if not top.exists(): top=root/'android/build.gradle'
settings=root/'android/settings.gradle.kts'
if not settings.exists(): settings=root/'android/settings.gradle'
manifest=root/'android/app/src/main/AndroidManifest.xml'
s=app.read_text()
if 'id("com.chaquo.python")' not in s: s=s.replace('plugins {','plugins {\n    id("com.chaquo.python")',1)
s=s.replace('minSdk = flutter.minSdkVersion','minSdk = 24\n        ndk {\n            abiFilters += listOf("arm64-v8a", "x86_64")\n        }')
if 'chaquopy {' not in s: s+='''\n\nchaquopy {\n    defaultConfig {\n        version = "3.10"\n        pip {\n            install("numpy==1.23.5")\n            install("pandas==2.1.3")\n            install("scipy==1.8.1")\n            install("statsmodels==0.14.5")\n            install("openpyxl==3.1.5")\n            install("xlrd==2.0.1")\n        }\n    }\n}\n'''
app.write_text(s)
t=top.read_text()
if 'id("com.chaquo.python")' not in t: t='plugins {\n    id("com.chaquo.python") version "17.0.0" apply false\n}\n\n'+t
top.write_text(t)
st=settings.read_text()
if 'mavenCentral()' not in st: st=st.replace('repositories {','repositories {\n        mavenCentral()',1)
settings.write_text(st)
m=manifest.read_text()
if 'com.chaquo.python.android.PyApplication' not in m: m=m.replace('<application ','<application android:name="com.chaquo.python.android.PyApplication" ',1)
manifest.write_text(m)
PY

cd "$BUILD_DIR"
flutter pub get
flutter build apk --release
mkdir -p "$ROOT/dist"
cp build/app/outputs/flutter-apk/app-release.apk "$ROOT/dist/StatsYuri-offline.apk"
echo "APK: $ROOT/dist/StatsYuri-offline.apk"
