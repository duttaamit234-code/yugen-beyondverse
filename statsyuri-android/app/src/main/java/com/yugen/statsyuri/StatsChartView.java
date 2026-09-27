package com.yugen.statsyuri;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.View;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/** Lightweight Canvas charts. No webview, plotting runtime, or image assets required. */
public final class StatsChartView extends View {
    public enum Mode { HISTOGRAM, SCATTER, BOXPLOT }

    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private List<String[]> rows = new ArrayList<>();
    private Mode mode = Mode.HISTOGRAM;
    private boolean dark = true;

    public StatsChartView(Context context) {
        super(context);
        paint.setStrokeCap(Paint.Cap.ROUND);
        setMinimumHeight(dp(220));
    }

    public void setData(List<String[]> rows, Mode mode, boolean dark) {
        this.rows = rows == null ? new ArrayList<>() : rows;
        this.mode = mode == null ? Mode.HISTOGRAM : mode;
        this.dark = dark;
        invalidate();
    }

    @Override protected void onDraw(Canvas c) {
        super.onDraw(c);
        int bg = dark ? 0xFF171D29 : 0xFFF7F8FB;
        int grid = dark ? 0xFF2C3547 : 0xFFDDE2EA;
        int text = dark ? 0xFFCBD4E4 : 0xFF4B5568;
        int accent = dark ? 0xFF9EDCFF : 0xFF356E9E;
        int accent2 = dark ? 0xFFC5A8FF : 0xFF7650B5;
        c.drawColor(bg);

        float left = dp(42), top = dp(22), right = getWidth() - dp(16), bottom = getHeight() - dp(34);
        if (right <= left || bottom <= top) return;

        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(dp(1));
        paint.setColor(grid);
        for (int i = 0; i <= 4; i++) {
            float y = top + (bottom - top) * i / 4f;
            c.drawLine(left, y, right, y, paint);
        }
        for (int i = 0; i <= 5; i++) {
            float x = left + (right - left) * i / 5f;
            c.drawLine(x, top, x, bottom, paint);
        }

        if (mode == Mode.SCATTER) drawScatter(c, left, top, right, bottom, accent, text);
        else if (mode == Mode.BOXPLOT) drawBox(c, left, top, right, bottom, accent2, text);
        else drawHistogram(c, left, top, right, bottom, accent, text);
    }

    private void drawHistogram(Canvas c, float l, float t, float r, float b, int color, int textColor) {
        List<Integer> nums = StatisticsEngine.numericColumns(rows);
        if (nums.isEmpty()) { drawCentered(c, "No numeric variable detected", textColor); return; }
        double[] x = column(nums.get(0));
        if (x.length == 0) { drawCentered(c, "No usable observations", textColor); return; }
        double min = x[0], max = x[0];
        for (double v : x) { min = Math.min(min, v); max = Math.max(max, v); }
        if (max == min) max = min + 1;
        int bins = Math.min(12, Math.max(5, (int)Math.sqrt(x.length)));
        int[] counts = new int[bins];
        for (double v : x) {
            int k = (int)Math.floor((v - min) / (max - min) * bins);
            if (k == bins) k = bins - 1;
            counts[Math.max(0, Math.min(bins - 1, k))]++;
        }
        int peak = 1; for (int n : counts) peak = Math.max(peak, n);
        paint.setStyle(Paint.Style.FILL); paint.setColor(color);
        float gap = dp(3), w = (r-l)/bins;
        for (int i=0;i<bins;i++) {
            float h = (b-t) * counts[i] / (float)peak;
            c.drawRoundRect(new RectF(l+i*w+gap, b-h, l+(i+1)*w-gap, b), dp(4), dp(4), paint);
        }
        drawLabel(c, rows.get(0)[nums.get(0)] + "  •  distribution", l, dp(16), textColor);
        drawLabel(c, "n = " + x.length, r-dp(72), b+dp(24), textColor);
    }

    private void drawScatter(Canvas c, float l, float t, float r, float b, int color, int textColor) {
        List<Integer> nums = StatisticsEngine.numericColumns(rows);
        if (nums.size() < 2) { drawCentered(c, "Two numeric variables are needed", textColor); return; }
        double[] x = column(nums.get(0)), y = column(nums.get(1));
        int n = Math.min(x.length, y.length);
        if (n == 0) { drawCentered(c, "No paired observations", textColor); return; }
        double minX=x[0],maxX=x[0],minY=y[0],maxY=y[0];
        for(int i=0;i<n;i++){minX=Math.min(minX,x[i]);maxX=Math.max(maxX,x[i]);minY=Math.min(minY,y[i]);maxY=Math.max(maxY,y[i]);}
        if(maxX==minX)maxX=minX+1;if(maxY==minY)maxY=minY+1;
        paint.setStyle(Paint.Style.FILL); paint.setColor(color);
        for(int i=0;i<n;i++){
            float px=l+(float)((x[i]-minX)/(maxX-minX))*(r-l);
            float py=b-(float)((y[i]-minY)/(maxY-minY))*(b-t);
            c.drawCircle(px,py,dp(3.5f),paint);
        }
        double corr = correlation(x,y,n);
        drawLabel(c, rows.get(0)[nums.get(0)] + " × " + rows.get(0)[nums.get(1)], l, dp(16), textColor);
        drawLabel(c, String.format(Locale.US,"r = %.3f   n = %d",corr,n), l, b+dp(24), textColor);
    }

    private void drawBox(Canvas c, float l, float t, float r, float b, int color, int textColor) {
        List<Integer> nums = StatisticsEngine.numericColumns(rows);
        if (nums.isEmpty()) { drawCentered(c, "No numeric variable detected", textColor); return; }
        double[] x=column(nums.get(0)); if(x.length==0){drawCentered(c,"No usable observations",textColor);return;}
        ArrayList<Double> a=new ArrayList<>();for(double v:x)a.add(v);Collections.sort(a);
        double q1=percentile(a,.25), med=percentile(a,.5), q3=percentile(a,.75), lo=q1-1.5*(q3-q1), hi=q3+1.5*(q3-q1);
        double min=a.get(0),max=a.get(a.size()-1); double span=Math.max(1,max-min);
        float cx=(l+r)/2f, boxW=dp(58);
        float yQ1=b-(float)((q1-min)/span)*(b-t), yQ3=b-(float)((q3-min)/span)*(b-t), yMed=b-(float)((med-min)/span)*(b-t);
        float yLo=b-(float)((Math.max(min,lo)-min)/span)*(b-t), yHi=b-(float)((Math.min(max,hi)-min)/span)*(b-t);
        paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(dp(2));paint.setColor(color);
        c.drawLine(cx,yHi,cx,yQ3,paint);c.drawLine(cx,yQ1,cx,yLo,paint);c.drawLine(cx-boxW/3,yHi,cx+boxW/3,yHi,paint);c.drawLine(cx-boxW/3,yLo,cx+boxW/3,yLo,paint);
        paint.setStyle(Paint.Style.FILL);paint.setColor(color);c.drawRoundRect(new RectF(cx-boxW/2,yQ3,cx+boxW/2,yQ1),dp(8),dp(8),paint);
        paint.setColor(dark?0xFF171D29:0xFFF7F8FB);c.drawRect(cx-boxW/2+dp(2),yMed-dp(2),cx+boxW/2-dp(2),yMed+dp(2),paint);
        drawLabel(c, rows.get(0)[nums.get(0)] + "  •  box plot", l, dp(16), textColor);
        drawLabel(c, String.format(Locale.US,"Q1 %.2f   Median %.2f   Q3 %.2f",q1,med,q3), l, b+dp(24), textColor);
    }

    private double[] column(int c){ArrayList<Double> v=new ArrayList<>();for(int i=1;i<rows.size();i++){if(c>=rows.get(i).length)continue;try{v.add(Double.parseDouble(rows.get(i)[c].trim()));}catch(Exception ignored){}}double[]a=new double[v.size()];for(int i=0;i<a.length;i++)a[i]=v.get(i);return a;}
    private double correlation(double[]x,double[]y,int n){double mx=0,my=0;for(int i=0;i<n;i++){mx+=x[i];my+=y[i];}mx/=n;my/=n;double a=0,b=0,d=0;for(int i=0;i<n;i++){double u=x[i]-mx,v=y[i]-my;a+=u*v;b+=u*u;d+=v*v;}return b==0||d==0?0:a/Math.sqrt(b*d);}
    private double percentile(ArrayList<Double>a,double p){if(a.size()==1)return a.get(0);double pos=p*(a.size()-1),lo=Math.max(0,(int)Math.floor(pos)),hi=Math.min(a.size()-1,lo+1),f=pos-lo;return a.get(lo)+(a.get(hi)-a.get(lo))*f;}
    private void drawCentered(Canvas c,String s,int color){paint.setTextSize(dp(14));paint.setColor(color);paint.setStyle(Paint.Style.FILL);paint.setTextAlign(Paint.Align.CENTER);c.drawText(s,getWidth()/2f,getHeight()/2f,paint);paint.setTextAlign(Paint.Align.LEFT);}
    private void drawLabel(Canvas c,String s,float x,float y,int color){paint.setStyle(Paint.Style.FILL);paint.setColor(color);paint.setTextSize(dp(12));paint.setTypeface(android.graphics.Typeface.DEFAULT);c.drawText(s,x,y,paint);}
    private int dp(float x){return Math.round(x*getResources().getDisplayMetrics().density);}
}
