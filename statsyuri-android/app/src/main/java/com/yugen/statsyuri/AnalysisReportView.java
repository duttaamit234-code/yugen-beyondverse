package com.yugen.statsyuri;

import android.app.Activity;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;

import java.util.Locale;

/** Readable, sectioned statistical report renderer for small Android screens. */
public final class AnalysisReportView {
    private final Activity activity;
    private final boolean dark;
    private final int text, muted, accent, card, surface;

    public AnalysisReportView(Activity activity, boolean dark) {
        this.activity = activity;
        this.dark = dark;
        text = dark ? Color.rgb(244,241,250) : Color.rgb(28,32,42);
        muted = dark ? Color.rgb(166,176,194) : Color.rgb(82,91,108);
        accent = dark ? Color.rgb(160,215,255) : Color.rgb(43,101,150);
        card = dark ? Color.rgb(26,31,44) : Color.rgb(255,255,255);
        surface = dark ? Color.rgb(36,43,61) : Color.rgb(239,242,247);
    }

    public LinearLayout render(StatisticsEngine.Result result) {
        LinearLayout root = new LinearLayout(activity);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(17), dp(18), dp(18));
        root.setBackgroundColor(card);

        TextView title = label(result.title, 21, text, true);
        root.addView(title, margin(0,0,0,4));
        root.addView(label(shortDescription(result.title), 13, muted, false), margin(0,0,0,14));

        root.addView(section("Assumptions", assumptions(result.title), false));

        String body = result.body == null ? "" : result.body.trim();
        String[] blocks = body.split("\\n\\s*\\n");
        LinearLayout calc = sectionContainer("Calculation and data", false);
        if (blocks.length == 0 || body.isEmpty()) {
            calc.addView(label("No calculation details were returned.", 14, muted, false));
        } else {
            for (String block : blocks) addBlock(calc, block.trim());
        }
        root.addView(calc, margin(0,10,0,10));

        root.addView(section("Interpretation", interpretation(result.title, body), true));
        root.addView(section("Note", "Results are calculated locally from the selected dataset. Check the assumptions and study design before drawing a substantive conclusion.", true));
        return root;
    }

    private void addBlock(LinearLayout parent, String block) {
        String[] lines = block.split("\\n");
        if (lines.length == 1) {
            parent.addView(label(lines[0], 14, text, false), margin(0,5,0,7));
            return;
        }
        String heading = lines[0].trim();
        if (!heading.isEmpty() && !looksLikeValueLine(heading)) {
            parent.addView(label(heading, 16, accent, true), margin(0,7,0,5));
        }
        TableLayout table = new TableLayout(activity);
        table.setColumnStretchable(0,true);
        for (int i=1;i<lines.length;i++) {
            String line=lines[i].trim();
            if(line.isEmpty()) continue;
            String[] pair = splitKeyValue(line);
            if(pair != null) addRow(table,pair[0],pair[1]);
            else addWrapped(table,line);
        }
        parent.addView(table, margin(0,0,0,7));
    }

    private void addRow(TableLayout table,String key,String value){
        TableRow row=new TableRow(activity);
        row.setBackgroundColor(surface);
        TextView a=label(key,14,text,true); TextView b=label(value,14,text,false);
        a.setPadding(dp(11),dp(8),dp(8),dp(8)); b.setPadding(dp(8),dp(8),dp(11),dp(8));
        row.addView(a,new TableRow.LayoutParams(0,-2,0.42f)); row.addView(b,new TableRow.LayoutParams(0,-2,0.58f));
        table.addView(row,tableParams());
    }

    private void addWrapped(TableLayout table,String line){
        TableRow row=new TableRow(activity); TextView v=label(line,14,text,false);v.setPadding(dp(11),dp(7),dp(11),dp(7));row.addView(v,new TableRow.LayoutParams(-1,-2));table.addView(row,tableParams());
    }

    private TableLayout.LayoutParams tableParams(){TableLayout.LayoutParams p=new TableLayout.LayoutParams(-1,-2);p.setMargins(0,dp(2),0,dp(2));return p;}

    private String[] splitKeyValue(String s){
        int i=s.indexOf(" = "); if(i>0)return new String[]{s.substring(0,i).trim(),s.substring(i+3).trim()};
        i=s.indexOf(": "); if(i>0)return new String[]{s.substring(0,i).trim(),s.substring(i+2).trim()};
        return null;
    }
    private boolean looksLikeValueLine(String s){return s.matches(".*(?:^|\\s)(?:n|N|df|p|F|t|r|mean|SD|IQR|CI|η²)\\s*(?:=|:).*|.*\\b(?:p|df)\\s*=.*");}

    private LinearLayout section(String title,String body,boolean compact){
        LinearLayout c=sectionContainer(title,compact);c.addView(label(body,14,text,false));return c;
    }
    private LinearLayout sectionContainer(String title,boolean compact){
        LinearLayout c=new LinearLayout(activity);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(14),dp(compact?11:14),dp(14),dp(compact?11:14));c.setBackgroundColor(surface);c.addView(label(title,16,accent,true),margin(0,0,0,7));return c;
    }

    private String assumptions(String title){
        String t=title.toLowerCase(Locale.US);
        if(t.contains("anova"))return "Independent observations; approximately normal residuals; comparable group variances. For two-way ANOVA, the factor cells should contain observations.";
        if(t.contains("t-test"))return "Independent observations; numeric outcome; approximate normality for small samples. Welch's test does not require equal variances.";
        if(t.contains("chi-square"))return "Independent observations; categorical counts; expected cell counts should be large enough for the chi-square approximation.";
        if(t.contains("correlation"))return "Paired numeric observations; Pearson correlation is most informative for a roughly linear relationship without extreme outliers.";
        if(t.contains("regression"))return "Independent observations; appropriate functional form; residuals should be reasonably well behaved; check influential observations.";
        if(t.contains("mann")||t.contains("wilcoxon")||t.contains("kruskal"))return "Independent observations for independent-sample tests; paired observations for Wilcoxon signed-rank; ordinal or continuous outcome.";
        if(t.contains("descriptive"))return "Values should represent the variable you intend to summarize. Missing or invalid entries are excluded by the local parser.";
        return "The assumptions depend on the selected model. Review the model-specific notes before interpreting a result.";
    }

    private String shortDescription(String title){
        String t=title.toLowerCase(Locale.US);
        if(t.contains("descriptive"))return "Summarizes the center, spread and range of numeric variables.";
        if(t.contains("anova"))return "Compares means across groups and separates explained from residual variation.";
        if(t.contains("t-test"))return "Tests whether a mean or difference between means is compatible with a reference value.";
        if(t.contains("correlation"))return "Measures the strength and direction of a linear association between numeric variables.";
        if(t.contains("regression"))return "Estimates how an outcome changes with one or more explanatory variables.";
        if(t.contains("chi-square"))return "Compares observed categorical counts with counts expected under a null model.";
        if(t.contains("confidence"))return "Gives an interval of plausible values for a population parameter under the model.";
        if(t.contains("outlier"))return "Flags observations outside the 1.5×IQR rule.";
        return "Statistical calculation and interpretation from your selected dataset.";
    }

    private String interpretation(String title,String body){
        String p=find(body,"p = ");
        if(p!=null){try{double v=Double.parseDouble(p.split("\\s|,|\\]")[0]);return v<0.05?"The reported p-value is below 0.05. Under the stated model, this is evidence against the corresponding null hypothesis.":"The reported p-value is at least 0.05. Under the stated model, the result does not provide strong evidence against the corresponding null hypothesis.";}catch(Exception ignored){}}
        if(title.toLowerCase(Locale.US).contains("correlation")){String r=find(body,"r = ");if(r!=null)return "The sign of r indicates direction; its absolute value indicates the strength of the linear association.";}
        return "Read the numerical result together with the assumptions, sample size and study design. Statistical output describes evidence under a model, not a guarantee about the underlying process.";
    }
    private String find(String body,String marker){int i=body.indexOf(marker);if(i<0)return null;String s=body.substring(i+marker.length()).trim();return s.split("\\n")[0].trim();}
    private TextView label(String s,int size,int color,boolean bold){TextView v=new TextView(activity);v.setText(s);v.setTextSize(size);v.setTextColor(color);v.setTypeface(Typeface.DEFAULT,bold?Typeface.BOLD:Typeface.NORMAL);v.setLineSpacing(dp(2),1f);return v;}
    private LinearLayout.LayoutParams margin(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(int x){return Math.round(x*activity.getResources().getDisplayMetrics().density);}
}
