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

/** Short statistical introduction shown before the main analysis screen. */
public class SplashActivity extends AppCompatActivity {
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

        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            startActivity(new android.content.Intent(this, MainActivity.class));
            finish();
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        }, 1900);
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
