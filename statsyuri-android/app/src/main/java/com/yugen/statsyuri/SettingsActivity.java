package com.yugen.statsyuri;

import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.view.Gravity;
import android.widget.CheckBox;
import android.widget.LinearLayout;
import android.widget.RadioGroup;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.credentials.Credential;
import androidx.credentials.CredentialManager;
import androidx.credentials.CustomCredential;
import androidx.credentials.GetCredentialRequest;
import androidx.credentials.GetCredentialResponse;
import androidx.credentials.CredentialManagerCallback;
import androidx.credentials.exceptions.GetCredentialException;
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption;
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential;

import java.util.concurrent.Executors;

public class SettingsActivity extends AppCompatActivity {
    private static final String PREFS = "statsyuri_settings";
    private static final String TERMS_ACCEPTED = "terms_accepted";
    private static final String ACCOUNT_EMAIL = "account_email";
    private static final String ACCOUNT_NAME = "account_name";
    private CheckBox terms;
    private TextView account;
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
        root.addView(text("Personalize StatsYuri and manage your account.", 14, MUTED, false), margin(0, 4, 0, 18));

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

        LinearLayout accountCard = card();
        accountCard.addView(text("Account & cloud access", 19, TEXT, true));
        account = text("Not signed in", 14, MUTED, false);
        accountCard.addView(account, margin(0, 5, 0, 4));
        loadAccount();

        terms = new CheckBox(this);
        terms.setText("I agree to the StatsYuri Terms & Conditions");
        terms.setTextColor(TEXT);
        terms.setTextSize(14);
        terms.setChecked(prefs.getBoolean(TERMS_ACCEPTED, false));
        accountCard.addView(terms, margin(0, 8, 0, 0));
        terms.setOnCheckedChangeListener((button, checked) -> prefs.edit().putBoolean(TERMS_ACCEPTED, checked).apply());

        TextView termsButton = text("Read Terms & Conditions", 14, ACCENT, true);
        termsButton.setClickable(true);
        termsButton.setOnClickListener(v -> showTerms());
        accountCard.addView(termsButton, margin(4, 5, 0, 8));

        android.widget.Button google = new android.widget.Button(this);
        google.setText("Sign in with Google");
        google.setTextAllCaps(false);
        google.setTextSize(15);
        google.setOnClickListener(v -> signInWithGoogle());
        accountCard.addView(google);
        root.addView(accountCard, margin(0, 0, 0, 12));

        LinearLayout privacy = card();
        privacy.addView(text("Privacy", 19, TEXT, true));
        privacy.addView(text("CSV and Excel analysis remains local. StatsYuri does not upload a dataset merely because you analyze it. Google sign-in is for account identity and future synchronized features; it does not automatically grant access to Google Drive or other private Google data.", 13, MUTED, false));
        root.addView(privacy, margin(0, 0, 0, 12));

        root.addView(text("© 2026 Amit Dutta • StatsYuri • Yugen Beyondverse", 11, FOOTER, false));
        setContentView(scroll);
    }

    private void signInWithGoogle() {
        if (!terms.isChecked()) {
            Toast.makeText(this, "Accept the Terms & Conditions before signing in.", Toast.LENGTH_LONG).show();
            return;
        }
        String clientId = getString(R.string.default_web_client_id);
        if (clientId.startsWith("YOUR_")) {
            Toast.makeText(this, "Google sign-in is ready, but the OAuth Web Client ID still needs to be configured for StatsYuri.", Toast.LENGTH_LONG).show();
            return;
        }

        CredentialManager manager = CredentialManager.create(this);
        GetSignInWithGoogleOption option = new GetSignInWithGoogleOption.Builder(clientId).build();
        GetCredentialRequest request = new GetCredentialRequest.Builder().addCredentialOption(option).build();
        manager.getCredentialAsync(this, request, new CancellationSignal(), Executors.newSingleThreadExecutor(),
                new CredentialManagerCallback<GetCredentialResponse, GetCredentialException>() {
                    @Override public void onResult(@NonNull GetCredentialResponse response) {
                        runOnUiThread(() -> handleGoogleCredential(response.getCredential()));
                    }
                    @Override public void onError(@NonNull GetCredentialException e) {
                        runOnUiThread(() -> Toast.makeText(SettingsActivity.this, "Google sign-in failed: " + e.getMessage(), Toast.LENGTH_LONG).show());
                    }
                });
    }

    private void handleGoogleCredential(Credential credential) {
        if (credential instanceof CustomCredential
                && GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL.equals(credential.getType())) {
            try {
                GoogleIdTokenCredential google = GoogleIdTokenCredential.createFrom(((CustomCredential) credential).getData());
                String email = google.getEmail();
                String name = google.getDisplayName();
                prefs.edit().putString(ACCOUNT_EMAIL, email == null ? "" : email)
                        .putString(ACCOUNT_NAME, name == null ? "" : name)
                        .putBoolean(TERMS_ACCEPTED, true)
                        .apply();
                loadAccount();
                Toast.makeText(this, "Signed in as " + (email == null ? "your Google account" : email), Toast.LENGTH_LONG).show();
            } catch (Exception e) {
                Toast.makeText(this, "Google credential could not be read.", Toast.LENGTH_LONG).show();
            }
        } else {
            Toast.makeText(this, "Unexpected Google credential type.", Toast.LENGTH_LONG).show();
        }
    }

    private void loadAccount() {
        String email = prefs.getString(ACCOUNT_EMAIL, "");
        String name = prefs.getString(ACCOUNT_NAME, "");
        if (email.isEmpty()) account.setText("Not signed in");
        else account.setText(name.isEmpty() ? email : name + "\n" + email);
    }

    private void showTerms() {
        new androidx.appcompat.app.AlertDialog.Builder(this)
                .setTitle("StatsYuri Terms & Conditions")
                .setMessage(getTerms())
                .setPositiveButton("Close", null)
                .show();
    }

    private String getTerms() {
        return "Last updated: 26 September 2026\n\n"
                + "1. Use of the app\nStatsYuri provides statistical analysis and educational explanations. You are responsible for checking whether an analysis is appropriate for your study, data, and assumptions. The app is not a substitute for professional statistical, medical, legal, financial, or scientific advice.\n\n"
                + "2. Your data\nOffline CSV and Excel analysis is performed on the device. Do not provide data you do not have permission to process. If future cloud features are enabled, the app will request the permissions needed for those features before accessing cloud data.\n\n"
                + "3. Google account\nGoogle sign-in is optional. When enabled, it is used to identify your account and support account-based features. StatsYuri will not claim access to Google Drive or other private Google services unless a separate authorization request is shown and you approve it.\n\n"
                + "4. Accuracy\nStatistical calculations are provided without a guarantee that they are suitable for every dataset or research question. Always inspect the data, assumptions, sample design, and reported results before using them in a consequential decision.\n\n"
                + "5. Availability\nFeatures may change, be added, removed, or temporarily become unavailable.\n\n"
                + "6. Intellectual property\nStatsYuri, its software, interface, branding, and original content are associated with Amit Dutta / Yugen Beyondverse unless otherwise stated.\n\n"
                + "7. Acceptance\nBy enabling the acceptance checkbox and signing in, you confirm that you have read and accepted these Terms & Conditions. You may use the offline analysis features without a Google account.\n\n"
                + "Contact: use the project repository or the published contact information for Yugen Beyondverse."
                + "\n\nThese terms should be reviewed by a qualified legal professional before public commercial release.";
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
