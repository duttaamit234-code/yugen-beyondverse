package com.yugen.statsyuri;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.FrameLayout;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

/** Short statistical introduction shown before the main analysis screen. */
public class SplashActivity extends AppCompatActivity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private volatile boolean pythonReady = false;
    private volatile boolean launchRequested = false;
    private TextView status;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(11, 14, 20));
        getWindow().setNavigationBarColor(Color.rgb(11, 14, 20));

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(11, 14, 20));
        root.addView(new StatsBackgroundView(this), new FrameLayout.LayoutParams(-1, -1));

        TextView title = label("StatsYuri", 38, Color.rgb(245, 241, 255), true);
        FrameLayout.LayoutParams tp = new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER);
        tp.gravity = Gravity.CENTER;
        tp.bottomMargin = 34;
        root.addView(title, tp);

        TextView subtitle = label("Making statistics easier to understand", 15, Color.rgb(141, 216, 255), false);
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER);
        sp.gravity = Gravity.CENTER;
        sp.topMargin = 58;
        root.addView(subtitle, sp);

        TextView formula = label("x̄   σ   p   r   F   χ²", 20, Color.rgb(201, 169, 255), true);
        FrameLayout.LayoutParams fp = new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER);
        fp.gravity = Gravity.CENTER;
        fp.topMargin = 118;
        root.addView(formula, fp);

        status = label("Preparing statistical engine…", 12, Color.rgb(127, 138, 158), false);
        FrameLayout.LayoutParams stp = new FrameLayout.LayoutParams(-2, -2, Gravity.CENTER_HORIZONTAL | Gravity.BOTTOM);
        stp.bottomMargin = 54;
        root.addView(status, stp);

        setContentView(root);

        AnimatorSet intro = new AnimatorSet();
        ObjectAnimator alpha = ObjectAnimator.ofFloat(title, View.ALPHA, 0f, 1f);
        ObjectAnimator scaleX = ObjectAnimator.ofFloat(title, View.SCALE_X, 0.88f, 1f);
        ObjectAnimator scaleY = ObjectAnimator.ofFloat(title, View.SCALE_Y, 0.88f, 1f);
        ObjectAnimator subAlpha = ObjectAnimator.ofFloat(subtitle, View.ALPHA, 0f, 1f);
        ObjectAnimator formulaAlpha = ObjectAnimator.ofFloat(formula, View.ALPHA, 0f, 1f);
        intro.playTogether(alpha, scaleX, scaleY, subAlpha, formulaAlpha);
        intro.setDuration(1000);
        intro.start();

        // Python.start() can take several seconds on a cold Android launch.
        // Never run it on the UI thread, otherwise the splash screen appears frozen.
        new Thread(() -> {
            try {
                if (!Python.isStarted()) Python.start(new AndroidPlatform(getApplicationContext()));
                pythonReady = true;
                handler.post(this::tryLaunchMain);
            } catch (Throwable error) {
                handler.post(() -> status.setText("Starting statistical engine…"));
                // MainActivity will report any actual Python failure when analysis is requested.
                pythonReady = true;
                handler.post(this::tryLaunchMain);
            }
        }, "StatsYuri-Python-Init").start();

        handler.postDelayed(() -> {
            launchRequested = true;
            tryLaunchMain();
        }, 1900);
    }

    private void tryLaunchMain() {
        if (!launchRequested || !pythonReady || isFinishing()) return;
        startActivity(new android.content.Intent(this, MainActivity.class));
        finish();
        overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
    }

    private TextView label(String text, int size, int color, boolean bold) {
        TextView v = new TextView(this);
        v.setText(text);
        v.setTextColor(color);
        v.setTextSize(size);
        v.setGravity(Gravity.CENTER);
        if (bold) v.setTypeface(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.BOLD);
        return v;
    }
}
