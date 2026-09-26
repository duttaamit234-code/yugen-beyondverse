package com.yugen.statsyuri;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.RadialGradient;
import android.graphics.Shader;
import android.view.View;
import android.view.animation.AnimationUtils;

public class StatsBackgroundView extends View {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final String symbols = "Σ   μ   σ   x̄   p   r   β   χ²   α   H₀   H₁   df   R²   ANOVA";
    private final String symbols2 = "∑   π   √n   z   t   F   E(X)   Var(X)   P(A)   CI   Cov(X,Y)";

    public StatsBackgroundView(Context context) {
        super(context);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        paint.setTypeface(android.graphics.Typeface.create("serif", android.graphics.Typeface.BOLD));
    }

    @Override
    protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float w = getWidth();
        float h = getHeight();
        float t = (AnimationUtils.currentAnimationTimeMillis() % 18000L) / 18000f;

        paint.setShader(new LinearGradient(0, 0, w, h,
                Color.rgb(11, 14, 20), Color.rgb(18, 22, 32), Shader.TileMode.CLAMP));
        canvas.drawRect(0, 0, w, h, paint);

        drawGlow(canvas, w * (0.10f + 0.025f * (float)Math.sin(t * Math.PI * 2)), h * .22f, 190, 0x176C4CA0);
        drawGlow(canvas, w * (0.88f + 0.025f * (float)Math.cos(t * Math.PI * 1.6)), h * .55f, 230, 0x14315E7D);
        drawGlow(canvas, w * (0.52f + 0.04f * (float)Math.sin(t * Math.PI)), h * .88f, 220, 0x1449376F);

        paint.setShader(null);
        paint.setStrokeWidth(1f);
        paint.setColor(0x06000000 | Color.WHITE);
        float step = 42f;
        float offset = (t * step) % step;
        for (float x = -step + offset; x < w + step; x += step) canvas.drawLine(x, 0, x, h, paint);
        for (float y = -step + offset; y < h + step; y += step) canvas.drawLine(0, y, w, y, paint);

        paint.setColor(0x1A8DD8FF);
        paint.setTextSize(Math.max(24f, Math.min(44f, w * .075f)));
        canvas.save();
        canvas.rotate(-4f, w / 2f, h * .30f);
        canvas.drawText(symbols, -w * .16f + t * w * .08f, h * .30f, paint);
        canvas.restore();

        paint.setColor(0x1749B7D4);
        paint.setTextSize(Math.max(20f, Math.min(36f, w * .060f)));
        canvas.save();
        canvas.rotate(3f, w / 2f, h * .67f);
        canvas.drawText(symbols2, w * .03f - t * w * .10f, h * .67f, paint);
        canvas.restore();

        postInvalidateDelayed(40);
    }

    private void drawGlow(Canvas canvas, float x, float y, float radius, int centerColor) {
        paint.setShader(new RadialGradient(x, y, radius,
                new int[]{centerColor, centerColor & 0x00FFFFFF},
                new float[]{0f, 1f}, Shader.TileMode.CLAMP));
        canvas.drawCircle(x, y, radius, paint);
    }
}
