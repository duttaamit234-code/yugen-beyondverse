package com.yugen.statsyuri;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Safe Android-only build of StatsYuri.
 * No Google services, no AppCompat, no Python runtime, no splash activity,
 * and no third-party UI library are loaded during startup.
 */
public class MainActivity extends Activity {
    private static final int PICK_FILE = 42;

    private FrameLayout root;
    private StatsBackgroundView background;
    private LinearLayout content;
    private TextView status;
    private TextView fileName;
    private EditText question;
    private Uri selectedUri;
    private boolean dark = true;

    private final int DARK_BG = Color.rgb(8, 11, 17);
    private final int DARK_CARD = Color.rgb(20, 25, 36);
    private final int DARK_TEXT = Color.rgb(244, 241, 250);
    private final int DARK_MUTED = Color.rgb(170, 178, 194);
    private final int ACCENT = Color.rgb(202, 171, 255);
    private final int CYAN = Color.rgb(141, 216, 255);

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(DARK_BG);
        getWindow().setNavigationBarColor(DARK_BG);
        getWindow().getDecorView().setSystemUiVisibility(0);
        buildUi();
    }

    private void buildUi() {
        root = new FrameLayout(this);
        background = new StatsBackgroundView(this);
        root.addView(background, new FrameLayout.LayoutParams(-1, -1));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.TRANSPARENT);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16), dp(12), dp(16), dp(26));
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));

        addToolbar();
        addIntro();
        addToolCard();
        addFooter();

        FrameLayout.LayoutParams scrollParams = new FrameLayout.LayoutParams(-1, -1);
        scrollParams.topMargin = dp(58);
        root.addView(scroll, scrollParams);
        setContentView(root);
    }

    private void addToolbar() {
        LinearLayout bar = new LinearLayout(this);
        bar.setOrientation(LinearLayout.HORIZONTAL);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(14), 0, dp(8), 0);
        bar.setBackgroundColor(Color.argb(235, 14, 18, 27));

        TextView title = text("StatsYuri", 19, DARK_TEXT, true);
        bar.addView(title, new LinearLayout.LayoutParams(0, dp(56), 1f));
        title.setGravity(Gravity.CENTER_VERTICAL);

        Button theme = toolbarButton("☾");
        theme.setContentDescription("Toggle light and dark appearance");
        theme.setOnClickListener(v -> toggleTheme());
        bar.addView(theme);

        Button settings = toolbarButton("⋮");
        settings.setContentDescription("Open settings");
        settings.setOnClickListener(v -> showSettings());
        bar.addView(settings);

        FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(-1, dp(58));
        p.gravity = Gravity.TOP;
        root.addView(bar, p);
    }

    private Button toolbarButton(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(DARK_TEXT);
        b.setTextSize(22);
        b.setAllCaps(false);
        b.setMinWidth(0);
        b.setMinHeight(0);
        b.setPadding(0, 0, 0, 0);
        return b;
    }

    private void addIntro() {
        TextView title = text("Making statistics easier to understand", 23, CYAN, true);
        title.setPadding(0, dp(10), 0, dp(3));
        content.addView(title);

        TextView sub = text("A lightweight local workspace. No account, network service, or Google component is required.", 14, DARK_MUTED, false);
        content.addView(sub, margins(0, 0, 0, 12));
    }

    private void addToolCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(18), dp(17), dp(18), dp(18));
        card.setBackgroundColor(Color.argb(236, 20, 25, 36));

        TextView heading = text("Dataset tools", 20, DARK_TEXT, true);
        card.addView(heading);
        card.addView(text("Start with a CSV file. The safe build performs a small local numerical summary without loading a Python runtime.", 13, DARK_MUTED, false), margins(0, 3, 0, 10));

        question = new EditText(this);
        question.setHint("Optional question about your dataset");
        question.setHintTextColor(Color.rgb(125, 134, 151));
        question.setTextColor(DARK_TEXT);
        question.setTextSize(15);
        question.setGravity(Gravity.TOP | Gravity.START);
        question.setMinHeight(dp(82));
        question.setPadding(dp(13), dp(11), dp(13), dp(11));
        question.setBackgroundColor(Color.rgb(31, 37, 50));
        card.addView(question, margins(0, 0, 0, 10));

        Button choose = new Button(this);
        choose.setText("Choose CSV dataset");
        choose.setAllCaps(false);
        choose.setTextSize(15);
        choose.setOnClickListener(v -> chooseFile());
        card.addView(choose, margins(0, 0, 0, 2));

        fileName = text("No dataset selected", 12, DARK_MUTED, false);
        card.addView(fileName, margins(0, 2, 0, 8));

        Button analyze = new Button(this);
        analyze.setText("Analyze locally");
        analyze.setAllCaps(false);
        analyze.setTextSize(16);
        analyze.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        analyze.setOnClickListener(v -> analyzeCsv());
        card.addView(analyze);

        status = text("Ready. The app is running in safe Android-only mode.", 13, CYAN, true);
        card.addView(status, margins(0, 12, 0, 0));

        content.addView(card, margins(0, 0, 0, 12));
    }

    private void addFooter() {
        TextView footer = text("© 2026 Yugen Beyondverse. All rights reserved.", 10, Color.rgb(105, 112, 128), false);
        footer.setGravity(Gravity.CENTER);
        content.addView(footer, margins(0, 14, 0, 0));
    }

    private void chooseFile() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("text/csv");
        startActivityForResult(intent, PICK_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && resultCode == RESULT_OK && data != null && data.getData() != null) {
            selectedUri = data.getData();
            fileName.setText(getFileName(selectedUri));
            status.setText("CSV ready. Tap Analyze locally.");
        }
    }

    private String getFileName(Uri uri) {
        try (android.database.Cursor cursor = getContentResolver().query(uri, null, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) return cursor.getString(index);
            }
        } catch (Exception ignored) { }
        return uri.toString();
    }

    private void analyzeCsv() {
        if (selectedUri == null) {
            status.setText("Choose a CSV dataset first.");
            return;
        }
        status.setText("Reading CSV locally…");
        new Thread(() -> {
            try {
                List<String[]> rows = readCsv(selectedUri);
                String result = summarize(rows);
                runOnUiThread(() -> showResult(result));
            } catch (Exception e) {
                runOnUiThread(() -> status.setText("Could not read this CSV: " + e.getMessage()));
            }
        }, "StatsYuri-CSV").start();
    }

    private List<String[]> readCsv(Uri uri) throws Exception {
        ArrayList<String[]> rows = new ArrayList<>();
        try (InputStream in = getContentResolver().openInputStream(uri);
             BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8))) {
            if (in == null) throw new IllegalStateException("file could not be opened");
            String line;
            while ((line = reader.readLine()) != null && rows.size() < 1001) {
                if (!line.trim().isEmpty()) rows.add(splitCsvLine(line));
            }
        }
        return rows;
    }

    private String[] splitCsvLine(String line) {
        ArrayList<String> values = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        boolean quoted = false;
        for (int i = 0; i < line.length(); i++) {
            char c = line.charAt(i);
            if (c == '"') {
                if (quoted && i + 1 < line.length() && line.charAt(i + 1) == '"') {
                    current.append('"'); i++;
                } else {
                    quoted = !quoted;
                }
            } else if (c == ',' && !quoted) {
                values.add(current.toString().trim());
                current.setLength(0);
            } else {
                current.append(c);
            }
        }
        values.add(current.toString().trim());
        return values.toArray(new String[0]);
    }

    private String summarize(List<String[]> rows) {
        if (rows.size() < 2) return "The CSV needs a header and at least one data row.";
        String[] header = rows.get(0);
        int columns = header.length;
        ArrayList<Integer> numeric = new ArrayList<>();
        for (int c = 0; c < columns; c++) {
            int valid = 0;
            for (int r = 1; r < rows.size(); r++) {
                if (c < rows.get(r).length && parse(rows.get(r)[c]) != null) valid++;
            }
            if (valid >= Math.max(2, (rows.size() - 1) / 2)) numeric.add(c);
        }
        StringBuilder out = new StringBuilder();
        out.append("Dataset summary\n\n");
        out.append("Rows: ").append(rows.size() - 1).append("\n");
        out.append("Columns: ").append(columns).append("\n");
        out.append("Numeric columns: ").append(numeric.size()).append("\n\n");
        int shown = Math.min(6, numeric.size());
        for (int i = 0; i < shown; i++) {
            int c = numeric.get(i);
            double[] stats = columnStats(rows, c);
            out.append(header[c].replace('_', ' ')).append("\n");
            out.append("Mean: ").append(fmt(stats[0])).append("   SD: ").append(fmt(stats[1])).append("\n\n");
        }
        if (numeric.size() >= 2) {
            double r = correlation(rows, numeric.get(0), numeric.get(1));
            out.append("Pearson correlation\n");
            out.append(header[numeric.get(0)]).append(" vs ").append(header[numeric.get(1)]).append("\n");
            out.append("r = ").append(fmt(r)).append("\n\n");
        }
        out.append("This safe build intentionally keeps the analysis engine small so startup remains independent of Python, Google services, and third-party UI libraries.");
        return out.toString();
    }

    private double[] columnStats(List<String[]> rows, int c) {
        ArrayList<Double> v = new ArrayList<>();
        for (int r = 1; r < rows.size(); r++) if (c < rows.get(r).length) {
            Double d = parse(rows.get(r)[c]); if (d != null) v.add(d);
        }
        double mean = 0;
        for (double d : v) mean += d;
        mean /= v.size();
        double ss = 0;
        for (double d : v) ss += (d - mean) * (d - mean);
        double sd = v.size() > 1 ? Math.sqrt(ss / (v.size() - 1)) : 0;
        return new double[]{mean, sd};
    }

    private double correlation(List<String[]> rows, int a, int b) {
        ArrayList<Double> x = new ArrayList<>(), y = new ArrayList<>();
        for (int r = 1; r < rows.size(); r++) {
            if (a >= rows.get(r).length || b >= rows.get(r).length) continue;
            Double xv = parse(rows.get(r)[a]), yv = parse(rows.get(r)[b]);
            if (xv != null && yv != null) { x.add(xv); y.add(yv); }
        }
        if (x.size() < 2) return 0;
        double mx = 0, my = 0;
        for (int i = 0; i < x.size(); i++) { mx += x.get(i); my += y.get(i); }
        mx /= x.size(); my /= y.size();
        double num = 0, dx = 0, dy = 0;
        for (int i = 0; i < x.size(); i++) {
            double xx = x.get(i) - mx, yy = y.get(i) - my;
            num += xx * yy; dx += xx * xx; dy += yy * yy;
        }
        return dx == 0 || dy == 0 ? 0 : num / Math.sqrt(dx * dy);
    }

    private Double parse(String s) {
        try { return Double.parseDouble(s.trim()); } catch (Exception e) { return null; }
    }

    private String fmt(double d) {
        return String.format(Locale.US, "%.5f", d).replaceAll("0+$", "").replaceAll("\\.$", "");
    }

    private void showResult(String result) {
        status.setText("Completed locally.");
        TextView resultView = text(result, 15, DARK_TEXT, false);
        resultView.setPadding(dp(15), dp(14), dp(15), dp(14));
        content.addView(resultView, Math.max(0, content.getChildCount() - 1));
    }

    private void toggleTheme() {
        dark = !dark;
        background.setLightMode(!dark);
        int bg = dark ? DARK_BG : Color.rgb(246, 247, 250);
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        status.setTextColor(dark ? CYAN : Color.rgb(45, 111, 150));
        status.setText("Appearance changed. The lightweight UI remains local.");
    }

    private void showSettings() {
        String message = "Safe Android build\n\nNo Google sign-in, cloud account, splash activity, Python runtime, or third-party UI framework is loaded at startup.\n\n© 2026 Yugen Beyondverse. All rights reserved.";
        new AlertDialog.Builder(this)
                .setTitle("StatsYuri settings")
                .setMessage(message)
                .setPositiveButton("Close", null)
                .show();
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextColor(color);
        t.setTextSize(size);
        t.setLineSpacing(dp(2), 1f);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private LinearLayout.LayoutParams margins(int l, int top, int r, int bottom) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.setMargins(dp(l), dp(top), dp(r), dp(bottom));
        return p;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
