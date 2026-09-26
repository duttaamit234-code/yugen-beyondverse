package com.yugen.statsyuri;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Typeface;
import android.util.AttributeSet;
import android.view.View;
import android.view.animation.DecelerateInterpolator;

/** A small, offline learning surface that keeps the analysis workflow educational without adding clutter. */
public class StatsLearningView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path chart = new Path();
    private final String[] titles = {
            "Stat tip • p-value",
            "Stat tip • assumptions",
            "Stat tip • effect size",
            "Stat tip • full analysis"
    };
    private final String[] messages = {
            "A small p-value is evidence against the null hypothesis. It is not a measure of how large the effect is.",
            "A test is only as trustworthy as its assumptions. Check the data structure before trusting the result.",
            "Report practical size as well as significance. A statistically significant result can still be small in practice.",
            "Full mode compares compatible analyses. Use it when you want to see alternatives, not just the first answer."
    };
    private int page = 0;
    private float phase = 0f;
    private ValueAnimator animator;

    public StatsLearningView(Context context, AttributeSet attrs) {
        super(context, attrs);
        setMinimumHeight(dp(118));
        setContentDescription("Animated statistics learning tips");
        animator = ValueAnimator.ofFloat(0f, 1f);
        animator.setDuration(3200);
        animator.setRepeatCount(ValueAnimator.INFINITE);
        animator.setInterpolator(new DecelerateInterpolator());
        animator.addUpdateListener(a -> {
            phase = (float) a.getAnimatedValue();
            if (phase > 0.985f) page = (page + 1) % messages.length;
            invalidate();
        });
    }

    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        animator.start();
    }

    @Override protected void onDetachedFromWindow() {
        animator.cancel();
        super.onDetachedFromWindow();
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float w = getWidth();
        float h = getHeight();

        paint.setStyle(Paint.Style.FILL);
        paint.setColor(Color.rgb(26, 31, 44));
        canvas.drawRoundRect(0, 0, w, h, dp(22), dp(22), paint);

        paint.setColor(Color.rgb(201, 169, 255));
        paint.setAlpha(80);
        canvas.drawCircle(w - dp(26), dp(20), dp(42), paint);
        paint.setAlpha(255);

        paint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
        paint.setTextSize(dp(14));
        paint.setColor(Color.rgb(201, 169, 255));
        canvas.drawText(titles[page], dp(17), dp(25), paint);

        paint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.NORMAL));
        paint.setTextSize(dp(13));
        paint.setColor(Color.rgb(221, 226, 235));
        drawWrapped(canvas, messages[page], dp(17), dp(49), w - dp(34), dp(17));

        // Tiny animated distribution/fit line. It reinforces the statistical theme without stealing attention.
        float baseY = h - dp(15);
        chart.reset();
        chart.moveTo(dp(17), baseY);
        for (int i = 0; i <= 8; i++) {
            float x = dp(17) + (w - dp(34)) * i / 8f;
            float y = baseY - dp(7) - (float)Math.sin(i * 0.9 + phase * Math.PI * 2) * dp(3);
            chart.lineTo(x, y);
        }
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(dp(1.5f));
        paint.setColor(Color.rgb(110, 204, 236));
        canvas.drawPath(chart, paint);
        paint.setStyle(Paint.Style.FILL);
    }

    private void drawWrapped(Canvas canvas, String text, float x, float y, float maxWidth, float lineHeight) {
        String[] words = text.split(" ");
        String line = "";
        float cy = y;
        for (String word : words) {
            String next = line.isEmpty() ? word : line + " " + word;
            if (paint.measureText(next) > maxWidth && !line.isEmpty()) {
                canvas.drawText(line, x, cy, paint);
                line = word;
                cy += lineHeight;
            } else line = next;
        }
        if (!line.isEmpty()) canvas.drawText(line, x, cy, paint);
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
