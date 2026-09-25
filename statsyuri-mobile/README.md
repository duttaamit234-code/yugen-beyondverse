# StatsYuri Mobile

This is a separate Android client. The existing Streamlit website remains unchanged.

Architecture:
- Flutter: mobile interface
- Chaquopy: embedded Python runtime
- Shared StatsYuri Python analysis modules
- Pandas, SciPy and Statsmodels: local statistical computation
- CSV/XLSX/XLS file selection
- Efficient / Full analysis mode foundation

The APK is built by GitHub Actions and is designed to work without a network connection after installation.

Current milestone:
1. Experimental-design ANOVA execution is wired to the shared engine.
2. Common generic analysis executors are next.
3. OCR/PDF support will be added after the core mobile engine is stable.

Chaquopy 17 requires Android API 24+ and supports current arm64-v8a and x86_64 targets. Flutter's Android build system is used only for the mobile app; the web deployment is independent.
