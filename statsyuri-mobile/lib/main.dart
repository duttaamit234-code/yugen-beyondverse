import 'dart:convert';
import 'dart:math' as math;

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() => runApp(const StatsYuriApp());

class StatsYuriApp extends StatelessWidget {
  const StatsYuriApp({super.key});

  @override
  Widget build(BuildContext context) {
    const bg = Color(0xFF0B0E14);
    const card = Color(0xFF1A1F2C);
    const surface = Color(0xFF242B3D);
    const accent = Color(0xFFC9A9FF);
    return MaterialApp(
      title: 'StatsYuri',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: bg,
        colorScheme: const ColorScheme.dark(
          primary: accent,
          secondary: Color(0xFF8DD8FF),
          surface: card,
          onSurface: Colors.white,
        ),
        useMaterial3: true,
        cardTheme: const CardThemeData(color: card, elevation: 0, margin: EdgeInsets.zero),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: surface,
          border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(16)), borderSide: BorderSide.none),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(16)), borderSide: BorderSide.none),
          focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(16)), borderSide: BorderSide(color: accent, width: 1.2)),
        ),
      ),
      home: const StatsYuriHome(),
    );
  }
}

class StatsYuriHome extends StatefulWidget {
  const StatsYuriHome({super.key});
  @override State<StatsYuriHome> createState() => _StatsYuriHomeState();
}

class _StatsYuriHomeState extends State<StatsYuriHome> with SingleTickerProviderStateMixin {
  static const _python = MethodChannel('statsyuri/python');
  String? _filePath, _fileName, _error;
  String _question = '', _mode = 'efficient';
  bool _busy = false;
  Map<String, dynamic>? _result;
  late final AnimationController _backgroundController;

  @override
  void initState() {
    super.initState();
    _backgroundController = AnimationController(vsync: this, duration: const Duration(seconds: 18))..repeat();
  }

  @override
  void dispose() {
    _backgroundController.dispose();
    super.dispose();
  }

  Future<void> _pickFile() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['csv', 'xlsx', 'xls']);
    if (picked == null || picked.files.single.path == null) return;
    setState(() {
      _filePath = picked.files.single.path;
      _fileName = picked.files.single.name;
      _result = null;
      _error = null;
    });
  }

  Future<void> _analyze() async {
    if (_filePath == null) {
      setState(() => _error = 'Choose a CSV or Excel dataset first.');
      return;
    }
    setState(() { _busy = true; _error = null; _result = null; });
    try {
      final raw = await _python.invokeMethod<String>('analyze', {'path': _filePath, 'question': _question.trim(), 'mode': _mode});
      setState(() => _result = jsonDecode(raw ?? '{}') as Map<String, dynamic>);
    } on PlatformException catch (e) {
      setState(() => _error = e.message ?? e.code);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        titleSpacing: 18,
        title: const Row(children: [AppMark(size: 34), SizedBox(width: 10), Text('StatsYuri', style: TextStyle(fontWeight: FontWeight.w800))]),
        actions: [Container(margin: const EdgeInsets.only(right: 16), padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6), decoration: BoxDecoration(color: const Color(0xFF242B3D).withOpacity(.85), borderRadius: BorderRadius.circular(30), border: Border.all(color: Colors.white.withOpacity(.06))), child: const Text('OFFLINE', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800)))],
      ),
      body: Stack(children: [
        Positioned.fill(child: AnimatedBuilder(animation: _backgroundController, builder: (_, __) => CustomPaint(painter: StatisticalBackground(progress: _backgroundController.value)))),
        SafeArea(child: ListView(padding: const EdgeInsets.fromLTRB(18, 8, 18, 36), children: [
          const SizedBox(height: 6),
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('Statistical Analysis', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 6),
              Text('Analyze locally. Understand the calculation. Keep your data on your device.', style: TextStyle(color: Colors.white.withOpacity(.68), height: 1.4)),
            ])),
            const AppMark(size: 58),
          ]),
          const SizedBox(height: 20),
          _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const _SectionTitle(icon: Icons.dataset_rounded, title: 'Dataset'),
            const SizedBox(height: 12),
            InkWell(onTap: _busy ? null : _pickFile, borderRadius: BorderRadius.circular(16), child: Container(width: double.infinity, padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16), decoration: BoxDecoration(color: const Color(0xFF242B3D), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.white.withOpacity(.05))), child: Row(children: [const Icon(Icons.upload_file_rounded), const SizedBox(width: 12), Expanded(child: Text(_fileName ?? 'Choose CSV / Excel dataset', style: const TextStyle(fontWeight: FontWeight.w700))), const Icon(Icons.chevron_right_rounded)]))),
          ])),
          const SizedBox(height: 14),
          _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const _SectionTitle(icon: Icons.auto_awesome_rounded, title: 'Ask StatsYuri'),
            const SizedBox(height: 6),
            Text('Optional. Leave it empty and StatsYuri will infer a compatible analysis from the dataset.', style: TextStyle(color: Colors.white.withOpacity(.55), fontSize: 12, height: 1.35)),
            const SizedBox(height: 12),
            TextField(minLines: 3, maxLines: 6, onChanged: (v) => _question = v, decoration: const InputDecoration(hintText: 'Example: Do mean crop yields differ among treatments?', hintStyle: TextStyle(color: Colors.white38))),
            const SizedBox(height: 14),
            Container(padding: const EdgeInsets.all(4), decoration: BoxDecoration(color: const Color(0xFF242B3D), borderRadius: BorderRadius.circular(16)), child: SegmentedButton<String>(showSelectedIcon: false, segments: const [ButtonSegment(value: 'efficient', label: Text('Efficient'), icon: Icon(Icons.bolt_rounded, size: 18)), ButtonSegment(value: 'full', label: Text('Full'), icon: Icon(Icons.analytics_rounded, size: 18))], selected: {_mode}, onSelectionChanged: (v) => setState(() => _mode = v.first))),
            const SizedBox(height: 14),
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _busy ? null : _analyze, style: FilledButton.styleFrom(backgroundColor: const Color(0xFFC9A9FF), foregroundColor: const Color(0xFF25183E), padding: const EdgeInsets.symmetric(vertical: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18))), icon: _busy ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.search_rounded), label: Text(_busy ? 'Analyzing…' : 'Analyze', style: const TextStyle(fontWeight: FontWeight.w900)))),
          ])),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 14), child: _SectionCard(child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [const Icon(Icons.error_outline_rounded), const SizedBox(width: 10), Expanded(child: Text(_error!))]))),
          if (_result != null) _ResultCard(result: _result!),
        ])),
      ]),
    );
  }
}

class AppMark extends StatelessWidget {
  const AppMark({super.key, required this.size});
  final double size;
  @override
  Widget build(BuildContext context) => Container(width: size, height: size, decoration: BoxDecoration(borderRadius: BorderRadius.circular(size * .28), gradient: const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFFD9C2FF), Color(0xFF8DD8FF)]), boxShadow: [BoxShadow(color: Color(0x2EBDA0FF), blurRadius: 18)]), child: CustomPaint(painter: AppMarkPainter()));
}

class AppMarkPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final stroke = Paint()..color = const Color(0xFF141826)..style = PaintingStyle.stroke..strokeWidth = size.width * .08..strokeCap = StrokeCap.round;
    final fill = Paint()..color = const Color(0xFF141826);
    final w = size.width;
    canvas.drawLine(Offset(w * .18, w * .78), Offset(w * .82, w * .78), stroke);
    for (final b in [const [0.23, 0.53, 0.09, 0.25], const [0.40, 0.39, 0.09, 0.39], const [0.57, 0.26, 0.09, 0.52]]) {
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(w * b[0], w * b[1], w * b[2], w * b[3]), Radius.circular(w * .03)), fill);
    }
    final sigma = Path()..moveTo(w * .30, w * .23)..lineTo(w * .48, w * .23)..lineTo(w * .35, w * .39)..lineTo(w * .50, w * .55);
    canvas.drawPath(sigma, stroke);
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _SectionCard extends StatelessWidget {
  const _SectionCard({required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Container(decoration: BoxDecoration(color: const Color(0xFF1A1F2C).withOpacity(.94), borderRadius: BorderRadius.circular(22), border: Border.all(color: Colors.white.withOpacity(.055)), boxShadow: [BoxShadow(color: Colors.black.withOpacity(.18), blurRadius: 24, offset: const Offset(0, 10))]), padding: const EdgeInsets.all(18), child: child);
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle({required this.icon, required this.title});
  final IconData icon;
  final String title;
  @override
  Widget build(BuildContext context) => Row(children: [Icon(icon, size: 21, color: const Color(0xFFC9A9FF)), const SizedBox(width: 9), Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900))]);
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final Map<String, dynamic> result;
  @override
  Widget build(BuildContext context) {
    final ok = result['ok'] == true;
    final analysis = result['analysis']?.toString() ?? 'Analysis';
    final rows = result['rows']?.toString();
    final columns = result['columns'];
    final calculation = result['calculation'];
    final values = result['result'];
    return Padding(padding: const EdgeInsets.only(top: 14), child: _SectionCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Icon(ok ? Icons.check_circle_rounded : Icons.info_rounded, color: ok ? const Color(0xFF9FE7C4) : const Color(0xFFFFD27D)), const SizedBox(width: 9), Expanded(child: Text(analysis, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w900)))]),
      if (result['reason'] != null) ...[const SizedBox(height: 9), Text(result['reason'].toString(), style: TextStyle(color: Colors.white.withOpacity(.65), height: 1.4))],
      if (rows != null || columns is List) ...[const SizedBox(height: 12), Wrap(spacing: 8, runSpacing: 8, children: [if (rows != null) _MetricChip(label: 'Rows', value: rows), if (columns is List) _MetricChip(label: 'Columns', value: '${columns.length}')])],
      if (values is Map<String, dynamic>) ...[const SizedBox(height: 14), const _Subheading(title: 'Results'), const SizedBox(height: 8), _DataMap(data: values)],
      if (calculation is Map<String, dynamic>) ...[const SizedBox(height: 16), const _Subheading(title: 'Calculation'), const SizedBox(height: 8), _CalculationCard(calculation: calculation)],
      if (result['error'] != null) ...[const SizedBox(height: 12), Text(result['error'].toString())],
    ])));
  }
}

class _MetricChip extends StatelessWidget {
  const _MetricChip({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Container(padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8), decoration: BoxDecoration(color: const Color(0xFF242B3D), borderRadius: BorderRadius.circular(12)), child: RichText(text: TextSpan(style: const TextStyle(fontSize: 12), children: [TextSpan(text: '$label  ', style: const TextStyle(color: Colors.white54)), TextSpan(text: value, style: const TextStyle(fontWeight: FontWeight.w800))])));
}

class _Subheading extends StatelessWidget {
  const _Subheading({required this.title});
  final String title;
  @override
  Widget build(BuildContext context) => Text(title, style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 14));
}

class _DataMap extends StatelessWidget {
  const _DataMap({required this.data});
  final Map<String, dynamic> data;
  @override
  Widget build(BuildContext context) => Column(children: data.entries.map((entry) {
    final value = entry.value;
    if (value is Map<String, dynamic>) return Card(color: const Color(0xFF242B3D), margin: const EdgeInsets.only(bottom: 7), child: ExpansionTile(title: Text(_prettyKey(entry.key), style: const TextStyle(fontWeight: FontWeight.w700)), children: [Padding(padding: const EdgeInsets.all(12), child: _DataMap(data: value))]));
    if (value is List) return Card(color: const Color(0xFF242B3D), margin: const EdgeInsets.only(bottom: 7), child: ExpansionTile(title: Text(_prettyKey(entry.key), style: const TextStyle(fontWeight: FontWeight.w700)), children: [Padding(padding: const EdgeInsets.fromLTRB(14, 0, 14, 12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: value.take(20).map((v) => Padding(padding: const EdgeInsets.symmetric(vertical: 3), child: Text(_prettyValue(v))).toList()))]));
    return Container(margin: const EdgeInsets.only(bottom: 7), padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11), decoration: BoxDecoration(color: const Color(0xFF242B3D), borderRadius: BorderRadius.circular(12)), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: Text(_prettyKey(entry.key), style: const TextStyle(color: Colors.white60))), const SizedBox(width: 12), Flexible(child: Text(_prettyValue(value), textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w800)))]));
  }).toList());
}

class _CalculationCard extends StatelessWidget {
  const _CalculationCard({required this.calculation});
  final Map<String, dynamic> calculation;
  @override
  Widget build(BuildContext context) {
    final steps = calculation['steps'];
    final formula = calculation['formula']?.toString();
    return Container(width: double.infinity, padding: const EdgeInsets.all(14), decoration: BoxDecoration(color: const Color(0xFF242B3D), borderRadius: BorderRadius.circular(16), border: Border.all(color: const Color(0xFFC9A9FF).withOpacity(.12))), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      if (formula != null) ...[Text(formula, style: const TextStyle(fontWeight: FontWeight.w900, color: Color(0xFFD9C2FF))), const SizedBox(height: 10)],
      if (steps is List) ...steps.asMap().entries.map((entry) => Padding(padding: const EdgeInsets.only(bottom: 8), child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Container(width: 22, height: 22, alignment: Alignment.center, decoration: BoxDecoration(color: const Color(0xFFC9A9FF).withOpacity(.15), shape: BoxShape.circle), child: Text('${entry.key + 1}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900))), const SizedBox(width: 9), Expanded(child: Text(entry.value.toString(), style: const TextStyle(height: 1.35)))])))
    ]));
  }
}

String _prettyKey(String value) => value.replaceAll('_', ' ').replaceAll(RegExp(r'([a-z])([A-Z])'), r'$1 $2').trim();
String _prettyValue(dynamic value) {
  if (value == null) return '—';
  if (value is double) return value.isFinite ? value.toStringAsFixed(6).replaceFirst(RegExp(r'0+\$'), '').replaceFirst(RegExp(r'\.\$'), '') : value.toString();
  if (value is num) return value.toString();
  if (value is Map || value is List) return jsonEncode(value);
  return value.toString();
}

class StatisticalBackground extends CustomPainter {
  StatisticalBackground({required this.progress});
  final double progress;
  @override
  void paint(Canvas canvas, Size size) {
    final t = progress * math.pi * 2;
    final bg = Paint()..shader = const LinearGradient(begin: Alignment.topLeft, end: Alignment.bottomRight, colors: [Color(0xFF0B0E14), Color(0xFF121620)]).createShader(Offset.zero & size);
    canvas.drawRect(Offset.zero & size, bg);

    final blobPaint = Paint();
    final blobs = [
      (Offset(size.width * (.08 + .035 * math.sin(t)), size.height * .12), 170.0, const Color(0xFF6C4CA0)),
      (Offset(size.width * (.90 + .04 * math.cos(t * .8)), size.height * .44), 210.0, const Color(0xFF315E7D)),
      (Offset(size.width * (.50 + .07 * math.sin(t * .55)), size.height * .90), 190.0, const Color(0xFF49376F)),
    ];
    for (final blob in blobs) {
      blobPaint.shader = RadialGradient(colors: [blob.$3.withOpacity(.10), blob.$3.withOpacity(0)]).createShader(Rect.fromCircle(center: blob.$1, radius: blob.$2));
      canvas.drawCircle(blob.$1, blob.$2, blobPaint);
    }

    final grid = Paint()..color = Colors.white.withOpacity(.025)..strokeWidth = 1;
    const step = 36.0;
    final drift = (progress * step) % step;
    for (double x = -step + drift; x < size.width + step; x += step) canvas.drawLine(Offset(x, 0), Offset(x, size.height), grid);
    for (double y = -step + drift; y < size.height + step; y += step) canvas.drawLine(Offset(0, y), Offset(size.width, y), grid);

    final symbols = ['μ', 'σ', 'x̄', 'r', 'p', 'Σ', 'F', 't', 'χ²', 'β'];
    for (var i = 0; i < symbols.length; i++) {
      final phase = t * (.16 + i * .013) + i * 1.7;
      final x = ((i * 97.0 + math.sin(phase) * 24) % (size.width + 80)) - 40;
      final y = ((i * 137.0 + progress * 180 + math.cos(phase) * 32) % (size.height + 120)) - 60;
      final opacity = .035 + .018 * (math.sin(phase) + 1) / 2;
      final text = TextPainter(text: TextSpan(text: symbols[i], style: TextStyle(color: const Color(0xFFC9A9FF).withOpacity(opacity), fontSize: 22 + (i % 3) * 7, fontWeight: FontWeight.w700)), textDirection: TextDirection.ltr)..layout();
      text.paint(canvas, Offset(x, y));
    }

    final bar = Paint()..color = const Color(0xFF8DD8FF).withOpacity(.035);
    final heights = [0.25, 0.50, 0.35, 0.72, 0.45, 0.86, 0.58, 0.78, 0.42, 0.68];
    final width = size.width / (heights.length * 2.2);
    final lift = math.sin(t) * 4;
    for (var i = 0; i < heights.length; i++) {
      final h = size.height * .16 * heights[i];
      final left = i * width * 2.2 + width * .6;
      canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(left, size.height - h - 22 + lift, width, h), const Radius.circular(5)), bar);
    }
  }
  @override bool shouldRepaint(covariant StatisticalBackground oldDelegate) => oldDelegate.progress != progress;
}
