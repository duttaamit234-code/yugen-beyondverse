# StatsYuri Offline Android

Separate Android application for StatsYuri. The existing Streamlit web application remains unchanged.

The app embeds the StatsYuri Python engine with Chaquopy, so supported statistical calculations run locally after installation.

## Current scope

- CSV
- XLS/XLSX
- Natural-language analysis planning
- Experimental-design ANOVA execution
- Core t-test, ANOVA, correlation, regression and chi-square paths

OCR and scanned-PDF support are intentionally left for the next Android milestone because they require a separate on-device OCR runtime.

## Build

From this directory:

    gradle assembleDebug

The APK is:

    app/build/outputs/apk/debug/app-debug.apk

The first build needs internet access to download Android and Python build dependencies. Once installed, supported analysis does not require network access.
