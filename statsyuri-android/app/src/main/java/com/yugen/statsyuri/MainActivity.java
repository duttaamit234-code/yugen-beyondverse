package com.yugen.statsyuri;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.chaquo.python.PyObject;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.Iterator;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends AppCompatActivity {
    private static final int PICK_FILE = 42;
    private EditText questionInput;
    private TextView fileName, status, modeHint;
    private LinearLayout resultContainer;
    private Uri selectedUri;
    private RadioGroup modeGroup;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    private final int CARD = Color.rgb(26, 31, 44);
    private final int SURFACE = Color.rgb(36, 43, 61);
    private final int ACCENT = Color.rgb(201, 169, 255);
    private final int TEXT = Color.rgb(245, 241, 255);
    private final int MUTED = Color.rgb(170, 178, 194);

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        questionInput = findViewById(R.id.questionInput);
        fileName = findViewById(R.id.fileName);
        status = findViewById(R.id.status);
        modeHint = findViewById(R.id.modeHint);
        resultContainer = findViewById(R.id.resultContainer);
        modeGroup = findViewById(R.id.modeGroup);

        findViewById(R.id.settingsButton).setOnClickListener(v ->
                startActivity(new Intent(this, SettingsActivity.class)));
        findViewById(R.id.selectFileButton).setOnClickListener(v -> chooseFile());
        findViewById(R.id.analyzeButton).setOnClickListener(v -> analyze());

        modeGroup.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.fullMode) {
                modeHint.setText("Full mode calculates every compatible analysis it can find.");
            } else {
                modeHint.setText("Efficient mode selects one compatible analysis and explains it.");
            }
        });
    }

    private boolean isFullMode() {
        return modeGroup.getCheckedRadioButtonId() == R.id.fullMode;
    }

    private void chooseFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, PICK_FILE);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && resultCode == RESULT_OK && data != null && data.getData() != null) {
            selectedUri = data.getData();
            fileName.setText(getFileName(selectedUri));
            status.setText("Dataset ready. Tap Analyze to inspect it locally.");
            resultContainer.removeAllViews();
        }
    }

    private String getFileName(Uri uri) {
        String name = null;
        try (android.database.Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) name = cursor.getString(index);
            }
        } catch (Exception ignored) { }
        return name == null ? uri.toString() : name;
    }

    private void analyze() {
        final String question = questionInput.getText().toString().trim();
        final boolean full = isFullMode();
        if (selectedUri == null) {
            status.setText("Choose a CSV / Excel dataset first. The question is optional.");
            return;
        }
        status.setText(full ? "Running compatible analyses locally…" : "Analyzing the dataset locally…");
        resultContainer.removeAllViews();
        executor.execute(() -> {
            try {
                File localFile = copyToCache(selectedUri);
                if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
                Python py = Python.getInstance();
                String moduleName = full ? "statsyuri_full_v2" : "statsyuri_bridge";
                PyObject module = py.getModule(moduleName);
                String output = full
                        ? module.callAttr("analyze_full", question, localFile.getAbsolutePath()).toString()
                        : module.callAttr("analyze", question, localFile.getAbsolutePath(), "Efficient").toString();
                main.post(() -> {
                    status.setText("Completed locally. No server was used.");
                    renderResult(output, full);
                });
            } catch (Exception e) {
                main.post(() -> {
                    status.setText("Analysis failed");
                    resultContainer.removeAllViews();
                    addCard("Could not complete the analysis", e.getMessage() == null ? e.toString() : e.getMessage(), false);
                });
            }
        });
    }

    private File copyToCache(Uri uri) throws Exception {
        String safe = getFileName(uri).replaceAll("[^A-Za-z0-9._-]", "_");
        File file = new File(getCacheDir(), safe);
        try (InputStream input = getContentResolver().openInputStream(uri);
             FileOutputStream output = new FileOutputStream(file)) {
            if (input == null) throw new IllegalStateException("Unable to open the selected file.");
            byte[] buffer = new byte[8192];
            int n;
            while ((n = input.read(buffer)) != -1) output.write(buffer, 0, n);
        }
        return file;
    }

    private void renderResult(String json, boolean full) {
        try {
            JSONObject root = new JSONObject(json);
            addSummary(root, full);
            JSONArray analyses = root.optJSONArray("analyses");
            if (full && analyses != null) {
                addHeading("Compatible analyses", analyses.length() + " calculated candidates");
                for (int i = 0; i < analyses.length(); i++) {
                    JSONObject item = analyses.optJSONObject(i);
                    if (item != null) addAnalysisCard(item, i + 1);
                }
            } else {
                addAnalysisCard(root, 1);
            }
        } catch (Exception e) {
            addCard("Analysis output", json, false);
        }
    }

    private void addSummary(JSONObject root, boolean full) {
        String analysis = humanAnalysis(root.optString("confirmed_analysis", "Statistical analysis"));
        String reason = root.optString("reason", "");
        String rows = root.isNull("rows") ? "-" : String.valueOf(root.optInt("rows", 0));
        JSONArray columns = root.optJSONArray("columns");
        LinearLayout box = cardLayout();
        box.addView(text(analysis, 20, TEXT, true));
        box.addView(text(full ? root.optInt("analysis_count", 0) + " compatible analyses were evaluated."
                : "One compatible analysis was selected from the dataset.", 14, MUTED, false));
        LinearLayout chips = new LinearLayout(this);
        chips.setOrientation(LinearLayout.HORIZONTAL);
        chips.setPadding(0, 12, 0, 0);
        chips.addView(chip("Rows", rows));
        chips.addView(chip("Columns", columns == null ? "0" : String.valueOf(columns.length())));
        box.addView(chips);
        if (columns != null) box.addView(text(joinArray(columns, ", "), 13, MUTED, false));
        if (!reason.isEmpty()) box.addView(text("Why this analysis\n" + simplifyReason(reason), 15, Color.rgb(221,226,235), false));
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
        addPlan(root.optJSONObject("plan"));
    }

    private void addPlan(JSONObject plan) {
        if (plan == null || plan.length() == 0) return;
        LinearLayout box = cardLayout();
        box.addView(text("Statistical plan", 18, TEXT, true));
        addPlanField(box, plan, "objective", "Objective");
        addPlanField(box, plan, "design", "Study design");
        addPlanField(box, plan, "response", "Response / outcome");
        addPlanField(box, plan, "factor", "Factor / predictor");
        addPlanField(box, plan, "treatment_factor", "Treatment factor");
        addPlanField(box, plan, "decision_rule", "Decision rule");
        addPlanField(box, plan, "data_needed", "Data needed");
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
    }

    private void addPlanField(LinearLayout box, JSONObject plan, String key, String label) {
        if (!plan.has(key) || plan.isNull(key)) return;
        String value = humanValue(plan.opt(key));
        if (value.isEmpty() || value.equals("null")) return;
        box.addView(text(label + "\n" + value, 15, Color.rgb(220,225,234), false));
    }

    private void addAnalysisCard(JSONObject item, int number) {
        String name = humanAnalysis(item.optString("analysis", item.optString("confirmed_analysis", "Analysis")));
        boolean ok = item.optBoolean("ok", true);
        LinearLayout box = cardLayout();
        box.addView(text(number + ".  " + name, 18, TEXT, true));
        box.addView(text(ok ? "Calculated successfully" : "Could not calculate this analysis", 13,
                ok ? Color.rgb(159,231,196) : Color.rgb(255,210,125), true));
        String reason = item.optString("reason", "");
        if (!reason.isEmpty()) box.addView(text("Why this analysis\n" + simplifyReason(reason), 15, Color.rgb(218,224,234), false));

        JSONObject execution = item.optJSONObject("execution");
        if (execution != null) {
            String calculation = execution.optString("calculation", "");
            if (!calculation.isEmpty()) addCalculation(box, calculation);
            JSONObject values = execution.optJSONObject("result");
            if (values != null) addResults(box, values);
        }
        JSONObject directResult = item.optJSONObject("result");
        if (directResult != null) addResults(box, directResult);
        if (item.has("error") && !item.isNull("error")) box.addView(text(humanValue(item.opt("error")), 14, Color.rgb(255,176,176), false));
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
    }

    private void addCalculation(LinearLayout box, String calculation) {
        box.addView(text("Calculation", 12, ACCENT, true));
        for (String line : calculation.split("\\n")) {
            if (!line.trim().isEmpty()) box.addView(text(line.trim(), 15, Color.rgb(224,228,236), false));
        }
    }

    private void addResults(LinearLayout box, JSONObject values) {
        box.addView(text("Results", 12, ACCENT, true));
        Iterator<String> keys = values.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(13, 11, 13, 11);
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(SURFACE);
            bg.setCornerRadius(13f);
            row.setBackground(bg);
            row.addView(text(humanKey(key), 13, Color.rgb(151,161,178), true));
            row.addView(text(humanValue(values.opt(key)), 15, Color.rgb(240,243,248), false));
            box.addView(row, marginParams(0, 9, 0, 0));
        }
    }

    private void addHeading(String title, String subtitle) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(4, 8, 4, 2);
        box.addView(text(title, 20, TEXT, true));
        box.addView(text(subtitle, 13, MUTED, false));
        resultContainer.addView(box, marginParams(0, 8, 0, 0));
    }

    private void addCard(String title, String body, boolean success) {
        LinearLayout box = cardLayout();
        box.addView(text(title, 18, success ? Color.rgb(159,231,196) : Color.rgb(255,210,125), true));
        box.addView(text(body, 15, Color.rgb(220,225,234), false));
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
    }

    private LinearLayout cardLayout() {
        LinearLayout inner = new LinearLayout(this);
        inner.setOrientation(LinearLayout.VERTICAL);
        inner.setPadding(18, 17, 18, 17);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(CARD);
        bg.setCornerRadius(22f);
        bg.setStroke(1, 0x0DFFFFFF);
        inner.setBackground(bg);
        return inner;
    }

    private TextView chip(String label, String value) {
        TextView t = text(label + "  " + value, 12, Color.rgb(232,236,244), true);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(SURFACE);
        bg.setCornerRadius(12f);
        t.setBackground(bg);
        t.setPadding(12, 8, 12, 8);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-2, -2);
        p.setMargins(0, 0, 8, 0);
        t.setLayoutParams(p);
        return t;
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextColor(color);
        t.setTextSize(size);
        t.setLineSpacing(3f, 1f);
        t.setPadding(0, 5, 0, 5);
        if (bold) t.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        return t;
    }

    private LinearLayout.LayoutParams marginParams(int l, int top, int r, int bottom) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.setMargins(l, top, r, bottom);
        return p;
    }

    private String humanAnalysis(String value) {
        if (value == null || value.trim().isEmpty()) return "Statistical analysis";
        return value.replace("Pearson correlation + simple linear regression", "Pearson correlation + linear regression");
    }

    private String simplifyReason(String value) {
        return value.replace("Automatically selected one-way ANOVA because", "I used one-way ANOVA because")
                .replace("Automatically selected Welch's t-test because", "I used Welch's t-test because")
                .replace("Automatically selected correlation and regression because", "I used correlation and regression because")
                .replace("the dataset contains at least two analysis-ready numeric variables", "the dataset has at least two numeric variables ready to compare")
                .replace("the dataset contains", "the dataset has");
    }

    private String humanKey(String key) {
        if (key == null) return "Value";
        String k = key.replace('_', ' ');
        if (k.equalsIgnoreCase("p-value")) return "p-value";
        if (k.equalsIgnoreCase("f-statistic")) return "F statistic";
        if (k.equalsIgnoreCase("t-statistic")) return "t statistic";
        if (k.equalsIgnoreCase("r-squared")) return "R²";
        return k;
    }

    private String humanValue(Object value) {
        if (value == null || value == JSONObject.NULL) return "Not available";
        if (value instanceof JSONObject) return prettyObject((JSONObject) value);
        if (value instanceof JSONArray) return prettyArray((JSONArray) value);
        if (value instanceof Double || value instanceof Float) {
            double d = ((Number) value).doubleValue();
            if (Double.isNaN(d) || Double.isInfinite(d)) return String.valueOf(d);
            if (Math.abs(d) < 0.0001 && d != 0) return String.format(java.util.Locale.US, "%.3e", d);
            return String.format(java.util.Locale.US, "%.5f", d).replaceAll("0+$", "").replaceAll("\\.$", "");
        }
        return String.valueOf(value).replace('_', ' ');
    }

    private String prettyObject(JSONObject object) {
        StringBuilder out = new StringBuilder();
        Iterator<String> keys = object.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            if (out.length() > 0) out.append("\n");
            out.append(humanKey(key)).append(": ").append(humanValue(object.opt(key)));
        }
        return out.toString();
    }

    private String prettyArray(JSONArray array) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < array.length(); i++) {
            if (i > 0) out.append(", ");
            out.append(humanValue(array.opt(i)));
        }
        return out.toString();
    }

    private String joinArray(JSONArray array, String separator) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < array.length(); i++) {
            if (i > 0) out.append(separator);
            out.append(String.valueOf(array.opt(i)).replace('_', ' '));
        }
        return out.toString();
    }

    @Override protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
