package com.yugen.statsyuri;

import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;

public class SettingsActivity extends AppCompatActivity {
    private static final String PREFS = "statsyuri_settings";
    private static final String TERMS_ACCEPTED = "terms_accepted";
    private CheckBox terms;
    private SharedPreferences prefs;
    private int BG, CARD, TEXT, MUTED, ACCENT, FOOTER;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        BG = getColor(R.color.statsyuri_background);
        CARD = getColor(R.color.statsyuri_card);
        TEXT = getColor(R.color.statsyuri_text);
        MUTED = getColor(R.color.statsyuri_muted);
        ACCENT = getColor(R.color.statsyuri_accent);
        FOOTER = getColor(R.color.statsyuri_footer);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        setTitle("Settings");
        buildUi();
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(20, 20, 20, 30);
        scroll.addView(root);

        root.addView(text("Settings", 30, TEXT, true));
        root.addView(text("Personalize StatsYuri and review its terms.", 14, MUTED, false), margin(0, 4, 0, 18));

        LinearLayout appearance = card();
        appearance.addView(text("Appearance", 19, TEXT, true));
        appearance.addView(text("Choose how StatsYuri should look.", 13, MUTED, false));

        RadioGroup modes = new RadioGroup(this);
        modes.setOrientation(RadioGroup.HORIZONTAL);
        modes.setGravity(Gravity.CENTER_VERTICAL);
        modes.setPadding(0, 8, 0, 0);
        android.widget.RadioButton system = radio("System");
        android.widget.RadioButton dark = radio("Dark");
        android.widget.RadioButton light = radio("Light");
        modes.addView(system, weight());
        modes.addView(dark, weight());
        modes.addView(light, weight());
        int current = AppCompatDelegate.getDefaultNightMode();
        if (current == AppCompatDelegate.MODE_NIGHT_YES) modes.check(dark.getId());
        else if (current == AppCompatDelegate.MODE_NIGHT_NO) modes.check(light.getId());
        else modes.check(system.getId());
        modes.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == dark.getId()) AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_YES);
            else if (checkedId == light.getId()) AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_NO);
            else AppCompatDelegate.setDefaultNightMode(AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM);
        });
        appearance.addView(modes);
        root.addView(appearance, margin(0, 0, 0, 12));

        LinearLayout termsCard = card();
        termsCard.addView(text("Terms & Conditions", 19, TEXT, true));
        termsCard.addView(text("Google sign-in and cloud-account features have been removed from this Android build. Offline analysis remains available without an account.", 13, MUTED, false), margin(0, 4, 0, 6));

        terms = new CheckBox(this);
        terms.setText("I have read and accept the StatsYuri Terms & Conditions");
        terms.setTextColor(TEXT);
        terms.setTextSize(14);
        terms.setChecked(prefs.getBoolean(TERMS_ACCEPTED, false));
        terms.setOnCheckedChangeListener((button, checked) -> prefs.edit().putBoolean(TERMS_ACCEPTED, checked).apply());
        termsCard.addView(terms, margin(0, 6, 0, 0));

        TextView termsButton = text("Read Terms & Conditions", 14, ACCENT, true);
        termsButton.setClickable(true);
        termsButton.setOnClickListener(v -> showTerms());
        termsCard.addView(termsButton, margin(4, 5, 0, 4));
        root.addView(termsCard, margin(0, 0, 0, 12));

        LinearLayout privacy = card();
        privacy.addView(text("Privacy", 19, TEXT, true));
        privacy.addView(text("CSV and Excel analysis is performed locally on the device. StatsYuri does not upload a dataset merely because you analyze it.", 13, MUTED, false));
        root.addView(privacy, margin(0, 0, 0, 12));

        LinearLayout legal = card();
        legal.addView(text("Legal & ownership", 17, TEXT, true));
        legal.addView(text("© 2026 Yugen Beyondverse. All rights reserved.", 13, FOOTER, true), margin(0, 6, 0, 0));
        legal.addView(text("StatsYuri and its original software, interface design, branding, documentation, and content are protected intellectual property of Yugen Beyondverse, except where otherwise stated.", 12, MUTED, false), margin(0, 4, 0, 0));
        root.addView(legal, margin(0, 0, 0, 12));

        TextView footer = text("© 2026 Yugen Beyondverse. All rights reserved.", 11, FOOTER, false);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer, margin(0, 4, 0, 0));
        setContentView(scroll);
    }

    private void showTerms() {
        new AlertDialog.Builder(this)
                .setTitle("StatsYuri Terms & Conditions")
                .setMessage(getTerms())
                .setPositiveButton("Close", null)
                .show();
    }

    private String getTerms() {
        return "Last updated: 26 September 2026\n\n"
                + "1. Use of the app\nStatsYuri provides statistical analysis and educational explanations. You are responsible for checking whether an analysis is appropriate for your study, data, and assumptions. The app is not a substitute for professional statistical, medical, legal, financial, or scientific advice.\n\n"
                + "2. Your data\nOffline CSV and Excel analysis is performed on the device. Do not provide data you do not have permission to process.\n\n"
                + "3. Accuracy\nStatistical calculations are provided without a guarantee that they are suitable for every dataset or research question. Inspect the data, assumptions, sample design, and reported results before using them in a consequential decision.\n\n"
                + "4. Availability\nFeatures may change, be added, removed, or temporarily become unavailable.\n\n"
                + "5. Intellectual property\nStatsYuri and its original software, interface design, branding, documentation, and content are the intellectual property of Yugen Beyondverse, except where otherwise stated. All rights are reserved.\n\n"
                + "6. Acceptance\nBy enabling the acceptance checkbox, you confirm that you have read and accepted these Terms & Conditions. Offline analysis does not require an account.\n\n"
                + "These terms should be reviewed by a qualified legal professional before public commercial release.";
    }

    private LinearLayout card() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(18, 17, 18, 17);
        android.graphics.drawable.GradientDrawable bg = new android.graphics.drawable.GradientDrawable();
        bg.setColor(CARD);
        bg.setCornerRadius(22f);
        box.setBackground(bg);
        return box;
    }

    private TextView text(String s, int size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(s);
        v.setTextSize(size);
        v.setTextColor(color);
        v.setLineSpacing(3f, 1f);
        if (bold) v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return v;
    }

    private android.widget.RadioButton radio(String label) {
        android.widget.RadioButton r = new android.widget.RadioButton(this);
        r.setId(View.generateViewId());
        r.setText(label);
        r.setTextColor(TEXT);
        r.setTextSize(12);
        return r;
    }

    private LinearLayout.LayoutParams weight() {
        return new LinearLayout.LayoutParams(0, -2, 1f);
    }

    private LinearLayout.LayoutParams margin(int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(-1, -2);
        p.setMargins(l, t, r, b);
        return p;
    }
}
