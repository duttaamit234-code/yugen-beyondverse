import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() => runApp(const StatsYuriApp());

class StatsYuriApp extends StatelessWidget {
  const StatsYuriApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'StatsYuri',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1976D2)), useMaterial3: true),
    darkTheme: ThemeData(brightness: Brightness.dark, colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF4FC3F7), brightness: Brightness.dark), useMaterial3: true),
    themeMode: ThemeMode.system,
    home: const StatsYuriHome(),
  );
}

class StatsYuriHome extends StatefulWidget {
  const StatsYuriHome({super.key});
  @override State<StatsYuriHome> createState() => _StatsYuriHomeState();
}

class _StatsYuriHomeState extends State<StatsYuriHome> {
  static const _python = MethodChannel('statsyuri/python');
  String? _filePath, _fileName, _error;
  String _question = '', _mode = 'efficient';
  bool _busy = false;
  Map<String, dynamic>? _result;

  Future<void> _pickFile() async {
    final picked = await FilePicker.platform.pickFiles(type: FileType.custom, allowedExtensions: ['csv','xlsx','xls']);
    if (picked == null || picked.files.single.path == null) return;
    setState(() { _filePath = picked.files.single.path; _fileName = picked.files.single.name; _result = null; _error = null; });
  }

  Future<void> _analyze() async {
    if (_filePath == null) { setState(() => _error = 'Choose a CSV or Excel dataset first.'); return; }
    if (_question.trim().isEmpty) { setState(() => _error = 'Describe the statistical problem first.'); return; }
    setState(() { _busy = true; _error = null; _result = null; });
    try {
      final raw = await _python.invokeMethod<String>('analyze', {'path': _filePath, 'question': _question.trim(), 'mode': _mode});
      setState(() => _result = jsonDecode(raw ?? '{}') as Map<String, dynamic>);
    } on PlatformException catch (e) {
      setState(() => _error = e.message ?? e.code);
    } catch (e) { setState(() => _error = e.toString()); }
    finally { if (mounted) setState(() => _busy = false); }
  }

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      appBar: AppBar(title: const Text('StatsYuri'), actions: [Padding(padding: const EdgeInsets.only(right: 12), child: Center(child: Text('OFFLINE', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: dark ? Colors.lightBlueAccent : Colors.blue))))]),
      body: Stack(children: [
        Positioned.fill(child: CustomPaint(painter: StatisticalBackground(dark: dark))),
        SafeArea(child: ListView(padding: const EdgeInsets.fromLTRB(18,20,18,32), children: [
          Text('Statistical Analysis Platform', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          const Text('Understand your data, choose a compatible analysis, and explain the result locally on your device.'),
          const SizedBox(height: 22),
          Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Dataset', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            FilledButton.icon(onPressed: _busy ? null : _pickFile, icon: const Icon(Icons.upload_file), label: const Text('Choose CSV / Excel')),
            if (_fileName != null) ...[const SizedBox(height: 10), Text(_fileName!, style: const TextStyle(fontWeight: FontWeight.w600))],
          ]))),
          const SizedBox(height: 14),
          Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            const Text('Ask StatsYuri', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 10),
            TextField(minLines: 4, maxLines: 7, onChanged: (v) => _question = v, decoration: const InputDecoration(border: OutlineInputBorder(), hintText: 'Example: Determine whether mean crop yield differs among five fertilizer treatments after accounting for blocks.')),
            const SizedBox(height: 14),
            SegmentedButton<String>(segments: const [ButtonSegment(value: 'efficient', label: Text('Efficient'), icon: Icon(Icons.bolt)), ButtonSegment(value: 'full', label: Text('Full'), icon: Icon(Icons.analytics))], selected: {_mode}, onSelectionChanged: (v) => setState(() => _mode = v.first)),
            const SizedBox(height: 14),
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: _busy ? null : _analyze, icon: _busy ? const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)) : const Icon(Icons.search), label: Text(_busy ? 'Analyzing…' : 'Analyze'))),
          ]))),
          if (_error != null) Padding(padding: const EdgeInsets.only(top:14), child: Card(color: Theme.of(context).colorScheme.errorContainer, child: Padding(padding: const EdgeInsets.all(14), child: Text(_error!)))),
          if (_result != null) _ResultCard(result: _result!),
        ])),
      ]),
    );
  }
}

class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result});
  final Map<String,dynamic> result;
  @override
  Widget build(BuildContext context) => Card(margin: const EdgeInsets.only(top:14), child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(result['ok'] == true ? 'Analysis Result' : 'Analysis Needs Attention', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
    const SizedBox(height:12),
    if (result['analysis'] != null) Text('Analysis: ${result['analysis']}'),
    if (result['design'] != null) Text('Design: ${result['design']}'),
    if (result['rows'] != null) Text('Rows: ${result['rows']}'),
    if (result['error'] != null) Padding(padding: const EdgeInsets.only(top:8), child: Text('${result['error']}')),
    if (result['message'] != null) Padding(padding: const EdgeInsets.only(top:8), child: Text('${result['message']}')),
    if (result['roles'] != null) ...[const SizedBox(height:12), const Text('Detected roles', style: TextStyle(fontWeight: FontWeight.bold)), Text(const JsonEncoder.withIndent('  ').convert(result['roles']))],
    if (result['result'] != null) ...[const SizedBox(height:12), const Text('Statistical result', style: TextStyle(fontWeight: FontWeight.bold)), Text(const JsonEncoder.withIndent('  ').convert(result['result']))],
  ]));
}

class StatisticalBackground extends CustomPainter {
  StatisticalBackground({required this.dark});
  final bool dark;
  @override
  void paint(Canvas canvas, Size size) {
    final grid = Paint()..color = (dark ? Colors.white : Colors.blue).withOpacity(0.045)..strokeWidth = 1;
    for (double x=0; x<size.width; x+=32) canvas.drawLine(Offset(x,0),Offset(x,size.height),grid);
    for (double y=0; y<size.height; y+=32) canvas.drawLine(Offset(0,y),Offset(size.width,y),grid);
    final bar = Paint()..color = (dark ? Colors.lightBlueAccent : Colors.blue).withOpacity(0.10);
    final heights=[0.25,0.5,0.35,0.72,0.45,0.86,0.58,0.78,0.42,0.68];
    final width=size.width/(heights.length*2.2);
    for(var i=0;i<heights.length;i++){ final h=size.height*0.22*heights[i]; final left=i*width*2.2+width*0.6; canvas.drawRRect(RRect.fromRectAndRadius(Rect.fromLTWH(left,size.height-h,width,h),const Radius.circular(5)),bar); }
  }
  @override bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
