package com.yugenbeyondverse.statsyuri_mobile

import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import com.chaquo.python.Python
import java.util.concurrent.Executors

class MainActivity : FlutterActivity() {
    private val executor = Executors.newSingleThreadExecutor()
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "statsyuri/python").setMethodCallHandler { call, result ->
            if (call.method != "analyze") { result.notImplemented(); return@setMethodCallHandler }
            val path = call.argument<String>("path")
            val question = call.argument<String>("question") ?: ""
            val mode = call.argument<String>("mode") ?: "efficient"
            if (path.isNullOrBlank()) { result.error("NO_FILE","No dataset file was supplied.",null); return@setMethodCallHandler }
            executor.execute {
                try {
                    val py = Python.getInstance()
                    val output = py.getModule("mobile_engine").callAttr("analyze_file", path, question, mode).toJava(String::class.java)
                    runOnUiThread { result.success(output) }
                } catch (e: Exception) {
                    runOnUiThread { result.error("PYTHON_ERROR", e.message ?: e.toString(), null) }
                }
            }
        }
    }
    override fun onDestroy() { executor.shutdownNow(); super.onDestroy() }
}
