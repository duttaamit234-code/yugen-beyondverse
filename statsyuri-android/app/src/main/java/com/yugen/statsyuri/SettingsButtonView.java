package com.yugen.statsyuri;

import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.util.AttributeSet;
import android.view.Gravity;

import androidx.appcompat.widget.AppCompatTextView;

/** Compact settings control that owns its navigation so the main activity stays simple. */
public class SettingsButtonView extends AppCompatTextView {
    public SettingsButtonView(Context context) { super(context); init(); }
    public SettingsButtonView(Context context, AttributeSet attrs) { super(context, attrs); init(); }
    public SettingsButtonView(Context context, AttributeSet attrs, int defStyleAttr) { super(context, attrs, defStyleAttr); init(); }

    private void init() {
        setText("⚙");
        setTextSize(22);
        setTextColor(Color.rgb(235, 230, 255));
        setGravity(Gravity.CENTER);
        setContentDescription("Settings");
        setClickable(true);
        setFocusable(true);
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.rgb(36, 43, 61));
        bg.setCornerRadius(18f);
        bg.setStroke(1, 0x18FFFFFF);
        setBackground(bg);
        setOnClickListener(v -> getContext().startActivity(new Intent(getContext(), SettingsActivity.class)));
    }
}
