package com.yugenbeyondverse.statsyuri;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.database.Cursor;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.TextView;

import androidx.activity.ComponentActivity;

import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.google.mlkit.vision.common.InputImage;
import com.google.mlkit.vision.text.TextRecognition;
import com.google.mlkit.vision.text.latin.TextRecognizerOptions;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends ComponentActivity {
    private static final int PICK_DATA = 1001;
    private static final int PICK_IMAGE = 1002;

    private byte[] dataBytes;
    private String dataName = "";
    private String ocrText = "";
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    private EditText questionInput;
    private TextView status;
    private TextView result;
    private Button solveButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        questionInput = findViewById(R.id.questionInput);
        status = findViewById(R.id.status);
        result = findViewById(R.id.result);
        solveButton = findViewById(R.id.solveButton);

        findViewById(R.id.uploadButton).setOnClickListener(v -> pickData());
        findViewById(R.id.imageButton).setOnClickListener(v -> pickImage());
        findViewById(R.id.analyzeButton).setOnClickListener(v -> analyze());
        solveButton.setOnClickListener(v -> solve());
    }

    private void pickData() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{
                "text/csv",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/pdf"
        });
        startActivityForResult(intent, PICK_DATA);
    }

    private void pickImage() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        startActivityForResult(intent, PICK_IMAGE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri uri = data.getData();
        if (requestCode == PICK_IMAGE) {
            runOcr(uri);
        } else if (requestCode == PICK_DATA) {
            try {
                dataBytes = readBytes(uri);
                dataName = getFileName(uri);
                status.setText("Loaded: " + dataName);
                solveButton.setEnabled(false);
            } catch (Exception e) {
                status.setText("Could not read file: " + e.getMessage());
            }
        }
    }

    private void runOcr(Uri uri) {
        status.setText("Reading image offline…");
        try {
            InputImage image = InputImage.fromFilePath(this, uri);
            TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
                    .process(image)
                    .addOnSuccessListener(text -> {
                        ocrText = text.getText();
                        status.setText("OCR complete. Text is ready for analysis.");
                    })
                    .addOnFailureListener(e -> status.setText("OCR failed: " + e.getMessage()));
        } catch (Exception e) {
            status.setText("Could not open image: " + e.getMessage());
        }
    }

    private void analyze() {
        String question = questionInput.getText().toString().trim();
        status.setText("Analyzing locally…");
        solveButton.setEnabled(false);
        executor.execute(() -> {
            try {
                Python py = Python.getInstance();
                PyObject bridge = py.getModule("statsyuri_bridge");
                String json = bridge.callAttr("analyze", question, dataBytes, dataName, ocrText).toString();
                runOnUiThread(() -> {
                    result.setText(pretty(json));
                    status.setText("Analysis complete. Review the detected analysis, then Solve.");
                    solveButton.setEnabled(dataBytes != null);
                });
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("Analysis error: " + e.getMessage()));
            }
        });
    }

    private void solve() {
        String question = questionInput.getText().toString().trim();
        status.setText("Solving locally…");
        executor.execute(() -> {
            try {
                Python py = Python.getInstance();
                PyObject bridge = py.getModule("statsyuri_bridge");
                String json = bridge.callAttr("solve", question, dataBytes, dataName, ocrText).toString();
                runOnUiThread(() -> {
                    result.setText(pretty(json));
                    status.setText("Solved offline.");
                });
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("Solve error: " + e.getMessage()));
            }
        });
    }

    private byte[] readBytes(Uri uri) throws Exception {
        try (InputStream input = getContentResolver().openInputStream(uri);
             ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            if (input == null) throw new IllegalStateException("No input stream");
            byte[] buffer = new byte[8192];
            int read;
            while ((read = input.read(buffer)) != -1) output.write(buffer, 0, read);
            return output.toByteArray();
        }
    }

    private String getFileName(Uri uri) {
        try (Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) return cursor.getString(index);
            }
        }
        return "data";
    }

    private String pretty(String json) {
        return json.replace("{", "{\n  ")
                .replace("}", "\n}")
                .replace(",", ",\n  ")
                .replace(":[", ": [")
                .replace("\"", "\"");
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
