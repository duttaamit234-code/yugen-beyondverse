package com.yugen.statsyuri;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import android.graphics.Color;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.chaquo.python.PyObject;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.button.MaterialButtonToggleGroup;
import com.google.android.material.card.MaterialCardView;

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
    private final ExecutorService executor = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());

    private final int BG = Color.rgb(11, 14, 20);
    private final int CARD = Color.rgb(26, 31, 44);
    private final int SURFACE = Color.rgb(36, 43, 61);
    private final int ACCENT = Color.rgb(201, 169, 255);
    private final int CYAN = Color.rgb(141, 216, 255);

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        questionInput = findViewById(R.id.questionInput);
        fileName = findViewById(R.id.fileName);
        status = findViewById(R.id.status);
        modeHint = findViewById(R.id.modeHint);
        resultContainer = findViewById(R.id.resultContainer);

        findViewById(R.id.selectFileButton).setOnClickListener(v -> chooseFile());
        findViewById(R.id.analyzeButton).setOnClickListener(v -> analyze());

        MaterialButtonToggleGroup modes = findViewById(R.id.modeGroup);
        modes.addOnButtonCheckedListener((group, checkedId, checked) -> {
            if (!checked) return;
            modeHint.setText(checkedId == R.id.fullMode
                    ? "Full evaluates every compatible analysis it can calculate."
                    : "Efficient selects one compatible analysis and explains it.");
        });

        if (!Python.isStarted()) Python.start(new AndroidPlatform(this));
    }

    private boolean isFullMode() {
        MaterialButtonToggleGroup modes = findViewById(R.id.modeGroup);
        return modes.getCheckedButtonId() == R.id.fullMode;
    }

    private void chooseFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, PICK_FILE);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && resultCode == RESULT_OK && data != null) {
            selectedUri = data.getData();
            fileName.setText(getFileName(selectedUri));
            status.setText("Dataset ready. Tap Analyze to inspect it automatically.");
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
        } catch (Exception ignored) {}
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

    private void renderResult(String json, boolean full) {
        try {
            JSONObject root = new JSONObject(json);
            addSummary(root, full);

            if (full && root.optJSONArray("analyses") != null) {
                JSONArray analyses = root.optJSONArray("analyses");
                addHeading("Compatible analyses", (analyses == null ? 0 : analyses.length()) + " calculated candidates");
                if (analyses != null) {
                    for (int i = 0; i < analyses.length(); i++) {
                        JSONObject item = analyses.optJSONObject(i);
                        if (item != null) addAnalysisCard(item, i + 1);
                    }
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
        String columnText = columns == null ? "-" : joinArray(columns, ", ");

        LinearLayout box = cardLayout();
        TextView title = text(analysis, 20, Color.rgb(245,241,255), true);
        box.addView(title);
        TextView subtitle = text(full
                ? root.optInt("analysis_count", 0) + " compatible analyses were evaluated."
                : "One compatible analysis was selected from the dataset.", 13, Color.LTGRAY, false);
        subtitle.setPadding(0, 7, 0, 0);
        box.addView(subtitle);

        LinearLayout chips = new LinearLayout(this);
        chips.setOrientation(LinearLayout.HORIZONTAL);
        chips.setPadding(0, 13, 0, 0);
        chips.addView(chip("Rows", rows));
        chips.addView(chip("Columns", columns == null ? "0" : String.valueOf(columns.length())));
        box.addView(chips);
        if (!columnText.equals("-")) {
            TextView c = text(columnText, 12, Color.rgb(127,138,158), false);
            c.setPadding(0, 9, 0, 0);
            box.addView(c);
        }
        if (!reason.isEmpty()) {
            TextView why = text(simplifyReason(reason), 14, Color.rgb(221,226,235), false);
            why.setPadding(0, 13, 0, 0);
            box.addView(why);
        }
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
        addPlan(root.optJSONObject("plan"));
    }

    private void addPlan(JSONObject plan) {
        if (plan == null || plan.length() == 0) return;
        LinearLayout box = cardLayout();
        box.addView(text("Statistical plan", 18, Color.rgb(245,241,255), true));
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
        TextView v = text(label + "\n" + value, 14, Color.rgb(220,225,234), false);
        v.setPadding(0, 11, 0, 0);
        box.addView(v);
    }

    private void addAnalysisCard(JSONObject item, int number) {
        String name = humanAnalysis(item.optString("analysis", item.optString("confirmed_analysis", "Analysis")));
        boolean ok = item.optBoolean("ok", true);
        LinearLayout box = cardLayout();
        TextView heading = text(number + ".  " + name, 18, Color.rgb(245,241,255), true);
        box.addView(heading);
        TextView state = text(ok ? "Calculated successfully" : "Could not calculate this analysis", 12,
                ok ? Color.rgb(159,231,196) : Color.rgb(255,210,125), true);
        state.setPadding(0, 7, 0, 0);
        box.addView(state);

        String reason = item.optString("reason", "");
        if (!reason.isEmpty()) {
            TextView why = text("WHY THIS ANALYSIS\n" + simplifyReason(reason), 14, Color.rgb(218,224,234), false);
            why.setPadding(0, 14, 0, 0);
            box.addView(why);
        }

        JSONObject execution = item.optJSONObject("execution");
        if (execution == null && item.has("execution") && !item.isNull("execution")) {
            try { execution = new JSONObject(item.optString("execution")); } catch (Exception ignored) {}
        }
        if (execution != null) {
            String calculation = execution.optString("calculation", "");
            if (!calculation.isEmpty()) addCalculation(box, calculation);
            JSONObject values = execution.optJSONObject("result");
            if (values != null) addResults(box, values);
        }

        JSONObject directResult = item.optJSONObject("result");
        if (directResult != null) addResults(box, directResult);
        if (item.has("error") && !item.isNull("error")) {
            TextView err = text(humanValue(item.opt("error")), 13, Color.rgb(255,176,176), false);
            err.setPadding(0, 12, 0, 0);
            box.addView(err);
        }
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
    }

    private void addCalculation(LinearLayout box, String calculation) {
        box.addView(text("CALCULATION", 11, ACCENT, true));
        String[] lines = calculation.split("\\n");
        for (String line : lines) {
            if (line.trim().isEmpty()) continue;
            TextView step = text(line.trim(), 14, Color.rgb(224,228,236), false);
            step.setPadding(0, 8, 0, 0);
            box.addView(step);
        }
    }

    private void addResults(LinearLayout box, JSONObject values) {
        box.addView(text("RESULT", 11, ACCENT, true));
        Iterator<String> keys = values.keys();
        while (keys.hasNext()) {
            String key = keys.next();
            Object value = values.opt(key);
            LinearLayout row = new LinearLayout(this);
            row.setOrientation(LinearLayout.VERTICAL);
            row.setPadding(13, 11, 13, 11);
            row.setBackgroundColor(SURFACE);
            TextView label = text(humanKey(key), 12, Color.rgb(151,161,178), true);
            TextView val = text(humanValue(value), 14, Color.rgb(240,243,248), false);
            val.setPadding(0, 4, 0, 0);
            row.addView(label);
            row.addView(val);
            box.addView(row, marginParams(0, 9, 0, 0));
        }
    }

    private void addHeading(String title, String subtitle) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(4, 8, 4, 2);
        box.addView(text(title, 20, Color.rgb(245,241,255), true));
        box.addView(text(subtitle, 13, Color.rgb(127,138,158), false));
        resultContainer.addView(box, marginParams(0, 8, 0, 0));
    }

    private void addCard(String title, String body, boolean success) {
        LinearLayout box = cardLayout();
        box.addView(text(title, 18, success ? Color.rgb(159,231,196) : Color.rgb(255,210,125), true));
        box.addView(text(body, 14, Color.rgb(220,225,234), false));
        resultContainer.addView(box, marginParams(0, 12, 0, 0));
    }

    private LinearLayout cardLayout() {
        MaterialCardView card = new MaterialCardView(this);
        card.setCardBackgroundColor(CARD);
        card.setRadius(22f);
        card.setStrokeColor(0x0DFFFFFF);
        card.setStrokeWidth(1);
        LinearLayout inner = new LinearLayout(this);
        inner.setOrientation(LinearLayout.VERTICAL);
        inner.setPadding(18, 17, 18, 17);
        card.addView(inner);
        resultContainer.addView(card, marginParams(0, 0, 0, 0));
        return inner;
    }

    private TextView chip(String label, String value) {
        TextView t = text(label + "  " + value, 12, Color.rgb(232,236,244), true);
        t.setBackgroundColor(SURFACE);
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
        return value.replace("Pearson correlation + simple linear regression", "Pearson correlation + linear regression")
                .replace("Welch two-sample t-test", "Welch two-sample t-test")
                .replace("Chi-square test of independence", "Chi-square test of independence");
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
        if (k.equals("P-Value")) return "p-value";
        if (k.equals("F-Statistic")) return "F statistic";
        if (k.equals("T-Statistic")) return "t statistic";
        if (k.equals("R-Squared")) return "R²";
        if (k.equals("Degrees of Freedom")) return "Degrees of freedom";
        return k;
    }

    private String humanValue(Object value) {
        if (value == null || value == JSONObject.NULL) return "Not available";
        if (value instanceof JSONObject) return prettyObject((JSONObject) value, 0);
        if (value instanceof JSONArray) return prettyArray((JSONArray) value);
        if (value instanceof Double || value instanceof Float) {
            double d = ((Number)value).doubleValue();
            if (Double.isNaN(d) || Double.isInfinite(d)) return String.valueOf(d);
            if (Math.abs(d) < 0.0001 && d != 0) return String.format(java.util.Locale.US, "%.3e", d);
            return String.format(java.util.Locale.US, "%.5f", d).replaceAll("0+$", "").replaceAll("\\.$", "");
        }
        return String.valueOf(value).replace('_', ' ');
    }

    private String prettyObject(JSONObject object, int depth) {
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
            if (i > 0) out.append("  •  ");
            out.append(humanValue(array.opt(i)));
        }
        return out.toString();
    }

    private String joinArray(JSONArray array, String separator) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < array.length(); i++) {
            if (i > 0) out.append(separator);
            out.append(humanValue(array.opt(i)));
        }
        return out.toString();
    }

    @Override protected void onDestroy() {
        executor.shutdownNow();
        super.onDestroy();
    }
}
