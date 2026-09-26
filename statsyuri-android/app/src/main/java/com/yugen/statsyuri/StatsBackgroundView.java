package com.yugen.statsyuri;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

/** Small, dependency-free animated statistical background. */
public class StatsBackgroundView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String[] symbols = {"Σ", "μ", "σ", "x̄", "p", "r", "χ²", "α", "H₀", "H₁", "F", "R²"};
    private long start;
    private boolean light;
    private boolean attached;

    public StatsBackgroundView(Context context) {
        super(context);
        start = System.currentTimeMillis();
        paint.setTypeface(android.graphics.Typeface.create("sans-serif", android.graphics.Typeface.BOLD));
        setFocusable(false);
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
    }

    public void setLightMode(boolean value) {
        light = value;
        invalidate();
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        attached = true;
        start = System.currentTimeMillis();
        postInvalidateOnAnimation();
    }

    @Override protected void onDetachedFromWindow() {
        attached = false;
        removeCallbacksAndMessages(null);
        super.onDetachedFromWindow();
    }

    @Override
    protected void onDraw(Canvas canvas) {
        float w = getWidth();
        float h = getHeight();
        if (w <= 0f || h <= 0f) return;
        float seconds = (System.currentTimeMillis() - start) / 1000f;

        canvas.drawColor(light ? Color.rgb(246, 247, 250) : Color.rgb(8, 11, 17));

        paint.setStrokeWidth(1f);
        paint.setColor(light ? 0x14000000 : 0x16FFFFFF);
        float grid = 44f;
        float shift = (seconds * 7f) % grid;
        for (float x = -grid + shift; x < w + grid; x += grid) canvas.drawLine(x, 0, x, h, paint);
        for (float y = -grid + shift; y < h + grid; y += grid) canvas.drawLine(0, y, w, y, paint);

        paint.setTextSize(Math.max(26f, Math.min(42f, w * .075f)));
        paint.setColor(light ? 0x160D5A75 : 0x1C8DD8FF);
        for (int i = 0; i < symbols.length; i++) {
            float x = (i * 97f + seconds * (8f + i % 3 * 4f)) % (w + 140f) - 70f;
            float y = 100f + i * (h / 15f) + (float) Math.sin(seconds * .45f + i) * 12f;
            canvas.drawText(symbols[i], x, y, paint);
        }

        paint.setTextSize(Math.max(18f, w * .045f));
        paint.setColor(light ? 0x120D5A75 : 0x155F88A8);
        String lower = "∑   z   t   E(X)   Var(X)   P(A)   CI   Cov(X,Y)";
        float x = -w * .2f + ((seconds * 12f) % (w * 1.2f));
        canvas.drawText(lower, x, h * .78f, paint);

        if (attached) postInvalidateOnAnimation();
    }
}
