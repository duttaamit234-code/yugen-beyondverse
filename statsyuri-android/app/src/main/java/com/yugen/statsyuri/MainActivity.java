package com.yugen.statsyuri;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.chaquo.python.PyObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_FILE = 42;

    private EditText questionInput;
    private TextView fileName;
    private TextView status;
    private TextView result;
    private Uri selectedUri;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(com.yugen.statsyuri.R.layout.activity_main);

        questionInput = findViewById(R.id.questionInput);
        fileName = findViewById(R.id.fileName);
        status = findViewById(R.id.status);
        result = findViewById(R.id.result);

        Button select = findViewById(R.id.selectFileButton);
        Button analyze = findViewById(R.id.analyzeButton);

        select.setOnClickListener(v -> chooseFile());
        analyze.setOnClickListener(v -> analyze());

        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
    }

    private void chooseFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, PICK_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && resultCode == RESULT_OK && data != null) {
            selectedUri = data.getData();
            fileName.setText(getFileName(selectedUri));
        }
    }

    private String getFileName(Uri uri) {
        String name = null;
        try (android.database.Cursor cursor = getContentResolver().query(
                uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) name = cursor.getString(index);
            }
        } catch (Exception ignored) {}
        return name == null ? uri.toString() : name;
    }

    private void analyze() {
        final String question = questionInput.getText().toString().trim();
        if (question.isEmpty()) {
            status.setText("Describe the statistical problem first.");
            return;
        }

        final boolean efficient = ((RadioButton) findViewById(R.id.efficientMode)).isChecked();
        status.setText("Analyzing locally…");
        result.setText("");

        executor.execute(() -> {
            try {
                File localFile = selectedUri == null ? null : copyToCache(selectedUri);
                Python py = Python.getInstance();
                PyObject module = py.getModule("statsyuri_bridge");
                String mode = efficient ? "Efficient" : "Full";
                String output = module.callAttr("analyze", question,
                        localFile == null ? null : localFile.getAbsolutePath(),
                        mode).toString();

                main.post(() -> {
                    status.setText("Completed locally. No server was used.");
                    result.setText(pretty(output));
                });
            } catch (Exception e) {
                main.post(() -> {
                    status.setText("Analysis failed");
                    result.setText(e.getMessage() == null ? e.toString() : e.getMessage());
                });
            }
        });
    }

    private File copyToCache(Uri uri) throws Exception {
        String name = getFileName(uri);
        String safe = name.replaceAll("[^A-Za-z0-9._-]", "_");
        File file = new File(getCacheDir(), safe);
        try (InputStream input = getContentResolver().openInputStream(uri);
             FileOutputStream output = new FileOutputStream(file)) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = input.read(buffer)) != -1) output.write(buffer, 0, n);
        }
        return file;
    }

    private String pretty(String json) {
        try {
            return new org.json.JSONObject(json).toString(2);
        } catch (Exception ignored) {
            return json;
        }
    }

    @Override
    protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
