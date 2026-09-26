# StatsYuri Offline Android

This is a separate Android build of StatsYuri. The existing Streamlit web application remains unchanged.

## Architecture

- Native Android UI
- Chaquopy embedded Python runtime
- Shared StatsYuri `src/` analysis engine from `yugen-analytica/`
- Bundled ML Kit text recognition for offline image OCR
- Local CSV/XLS/XLSX/PDF parsing
- No network connection is required for the analysis engine after installation

## Build

GitHub Actions builds the release APK with `.github/workflows/build-statsyuri-apk.yml` and publishes it as the `StatsYuri-offline-apk` artifact.

The build currently targets `arm64-v8a` and `x86_64` and uses Chaquopy 17 with Python 3.10 because the Android statsmodels wheel is available for that runtime. Chaquopy requires Android API 24 or newer. See the Chaquopy documentation for supported Python versions and ABIs.

## Current offline workflow

1. Upload CSV/XLS/XLSX/PDF or an image for OCR.
2. Enter the statistical question, or let OCR/PDF text contribute to the question.
3. Analyze to identify the compatible analysis.
4. Solve to run the confirmed calculation locally.
5. Efficient mode behavior is preserved by solving only the selected analysis.

The mobile bridge deliberately reuses the existing question engine and statistical core instead of maintaining a second copy of the statistical algorithms.
