package com.yugen.statsyuri;

import org.apache.commons.math3.distribution.ChiSquaredDistribution;
import org.apache.commons.math3.distribution.FDistribution;
import org.apache.commons.math3.distribution.TDistribution;
import org.apache.commons.math3.stat.StatUtils;
import org.apache.commons.math3.stat.correlation.PearsonsCorrelation;
import org.apache.commons.math3.stat.descriptive.DescriptiveStatistics;
import org.apache.commons.math3.stat.inference.MannWhitneyUTest;
import org.apache.commons.math3.stat.inference.WilcoxonSignedRankTest;
import org.apache.commons.math3.stat.regression.OLSMultipleLinearRegression;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Local StatsYuri statistical engine.
 * The web app uses scipy/statsmodels; this Android engine keeps the same
 * analysis families without loading Python or any network service.
 */
public final class StatisticsEngine {
    private StatisticsEngine() {}

    public static final class Result {
        public final String title;
        public final String body;
        public Result(String title, String body) { this.title = title; this.body = body; }
    }

    public static List<Integer> numericColumns(List<String[]> rows) {
        ArrayList<Integer> out = new ArrayList<>();
        if (rows.size() < 2) return out;
        String[] h = rows.get(0);
        for (int c = 0; c < h.length; c++) {
            if (isIdentifier(h[c])) continue;
            int n = 0, valid = 0;
            for (int r = 1; r < rows.size(); r++) if (c < rows.get(r).length) {
                String s = rows.get(r)[c].trim();
                if (!s.isEmpty()) { n++; if (parse(s) != null) valid++; }
            }
            if (n > 0 && valid >= Math.max(2, (int) Math.ceil(n * .5))) out.add(c);
        }
        return out;
    }

    public static List<Integer> categoricalColumns(List<String[]> rows) {
        ArrayList<Integer> out = new ArrayList<>();
        if (rows.size() < 2) return out;
        String[] h = rows.get(0);
        for (int c = 0; c < h.length; c++) {
            if (isIdentifier(h[c])) continue;
            LinkedHashSet<String> vals = new LinkedHashSet<>();
            int n = 0;
            for (int r = 1; r < rows.size(); r++) if (c < rows.get(r).length) {
                String s = rows.get(r)[c].trim();
                if (!s.isEmpty()) { n++; vals.add(s); }
            }
            if (n > 0 && vals.size() >= 2 && vals.size() <= Math.max(20, n / 2)) out.add(c);
        }
        return out;
    }

    public static Result descriptive(List<String[]> rows) {
        List<Integer> cols = numericColumns(rows);
        StringBuilder b = new StringBuilder("Rows: ").append(Math.max(0, rows.size() - 1)).append("\n\n");
        if (cols.isEmpty()) return new Result("Descriptive statistics", b.append("No numeric variables detected.").toString());
        for (int c : cols) {
            double[] x = column(rows, c);
            if (x.length == 0) continue;
            DescriptiveStatistics d = new DescriptiveStatistics(x);
            b.append(rows.get(0)[c]).append("\n")
                    .append("n = ").append(x.length).append("   Mean = ").append(fmt(d.getMean()))
                    .append("   Median = ").append(fmt(d.getPercentile(50))).append("\n")
                    .append("SD = ").append(fmt(d.getStandardDeviation())).append("   Min = ").append(fmt(d.getMin()))
                    .append("   Q1 = ").append(fmt(d.getPercentile(25))).append("   Q3 = ").append(fmt(d.getPercentile(75)))
                    .append("   Max = ").append(fmt(d.getMax())).append("\n")
                    .append("IQR = ").append(fmt(d.getPercentile(75) - d.getPercentile(25))).append("\n\n");
        }
        return new Result("Descriptive statistics", b.toString());
    }

    public static Result outliers(List<String[]> rows) {
        StringBuilder b = new StringBuilder();
        for (int c : numericColumns(rows)) {
            double[] x = sorted(column(rows, c));
            if (x.length == 0) continue;
            double q1 = percentile(x, .25), q3 = percentile(x, .75), iqr = q3 - q1;
            double lo = q1 - 1.5 * iqr, hi = q3 + 1.5 * iqr;
            int n = 0; for (double v : x) if (v < lo || v > hi) n++;
            b.append(rows.get(0)[c]).append(": ").append(n).append(" outlier(s), bounds [")
                    .append(fmt(lo)).append(", ").append(fmt(hi)).append("]\n");
        }
        return new Result("Outlier detection", b.length() == 0 ? "No numeric variables detected." : b.toString());
    }

    public static Result correlation(List<String[]> rows) {
        List<Integer> cs = numericColumns(rows);
        if (cs.size() < 2) return new Result("Pearson correlation", "At least two numeric variables are required.");
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < cs.size(); i++) for (int j = i + 1; j < cs.size(); j++) {
            ArrayList<Double> a = new ArrayList<>(), q = new ArrayList<>();
            for (int r = 1; r < rows.size(); r++) {
                if (cs.get(i) >= rows.get(r).length || cs.get(j) >= rows.get(r).length) continue;
                Double u = parse(rows.get(r)[cs.get(i)]), v = parse(rows.get(r)[cs.get(j)]);
                if (u != null && v != null) { a.add(u); q.add(v); }
            }
            double[] aa = toArray(a), qq = toArray(q);
            if (aa.length > 1) b.append(rows.get(0)[cs.get(i)]).append(" vs ").append(rows.get(0)[cs.get(j)])
                    .append(": r = ").append(fmt(new PearsonsCorrelation().correlation(aa, qq))).append("\n");
        }
        return new Result("Pearson correlation", b.toString());
    }

    public static Result confidenceIntervals(List<String[]> rows) {
        StringBuilder b = new StringBuilder();
        for (int c : numericColumns(rows)) {
            double[] x = column(rows, c); if (x.length < 2) continue;
            double mean = StatUtils.mean(x), sd = Math.sqrt(StatUtils.variance(x));
            double crit = new TDistribution(x.length - 1).inverseCumulativeProbability(.975);
            double m = crit * sd / Math.sqrt(x.length);
            b.append(rows.get(0)[c]).append(": mean = ").append(fmt(mean)).append(", 95% CI [")
                    .append(fmt(mean - m)).append(", ").append(fmt(mean + m)).append("]\n");
        }
        return new Result("95% confidence intervals", b.toString());
    }

    public static Result oneSampleT(List<String[]> rows, double mu) {
        List<Integer> cs = numericColumns(rows);
        if (cs.isEmpty()) return new Result("One-sample t-test", "No numeric variable detected.");
        double[] x = column(rows, cs.get(0));
        if (x.length < 2) return new Result("One-sample t-test", "At least two observations are required.");
        double mean = StatUtils.mean(x), sd = Math.sqrt(StatUtils.variance(x));
        if (sd == 0) return new Result("One-sample t-test", "The sample has zero variance.");
        double t = (mean - mu) / (sd / Math.sqrt(x.length));
        double p = 2 * (1 - new TDistribution(x.length - 1).cumulativeProbability(Math.abs(t)));
        return new Result("One-sample t-test", rows.get(0)[cs.get(0)] + " vs μ₀ = " + fmt(mu) + "\nn = " + x.length
                + "\nt = " + fmt(t) + "   df = " + (x.length - 1) + "   p = " + fmt(p) + "\n" + decision(p));
    }

    public static Result twoSampleT(List<String[]> rows) {
        List<Integer> num = numericColumns(rows), cat = categoricalColumns(rows);
        if (!cat.isEmpty() && !num.isEmpty()) {
            int g = bestGroup(rows, cat), v = num.get(0); List<String> levels = levels(rows, g);
            if (levels.size() == 2) return welch(rows.get(0)[v], levels.get(0), levels.get(1), group(rows, v, g, levels.get(0)), group(rows, v, g, levels.get(1)), "Welch independent t-test");
        }
        if (num.size() >= 2) return welch(rows.get(0)[num.get(0)], rows.get(0)[num.get(0)], rows.get(0)[num.get(1)], column(rows, num.get(0)), column(rows, num.get(1)), "Welch two-column t-test");
        return new Result("Two-sample t-test", "Need a numeric outcome plus a two-level group, or two numeric columns.");
    }

    private static Result welch(String var, String a, String b, double[] x, double[] y, String title) {
        if (x.length < 2 || y.length < 2) return new Result(title, "Both samples need at least two observations.");
        double mx = StatUtils.mean(x), my = StatUtils.mean(y), vx = StatUtils.variance(x), vy = StatUtils.variance(y);
        double se = Math.sqrt(vx / x.length + vy / y.length); if (se == 0) return new Result(title, "The standard error is zero.");
        double t = (mx - my) / se;
        double df = Math.pow(vx / x.length + vy / y.length, 2) / (Math.pow(vx / x.length, 2) / (x.length - 1) + Math.pow(vy / y.length, 2) / (y.length - 1));
        double p = 2 * (1 - new TDistribution(df).cumulativeProbability(Math.abs(t)));
        return new Result(title, var + "\n" + a + ": n=" + x.length + ", mean=" + fmt(mx) + "\n" + b + ": n=" + y.length + ", mean=" + fmt(my)
                + "\nDifference = " + fmt(mx - my) + "\nt = " + fmt(t) + "   df = " + fmt(df) + "   p = " + fmt(p) + "\n" + decision(p));
    }

    public static Result oneWayAnova(List<String[]> rows) {
        List<Integer> num = numericColumns(rows), cat = categoricalColumns(rows);
        if (num.isEmpty() || cat.isEmpty()) return new Result("One-way ANOVA", "Need a numeric outcome and categorical factor.");
        int v = num.get(0), g = bestGroup(rows, cat); List<String> lv = levels(rows, g);
        if (lv.size() < 3) return new Result("One-way ANOVA", "At least three groups are required.");
        ArrayList<double[]> groups = new ArrayList<>(); for (String s : lv) groups.add(group(rows, v, g, s));
        return anova(rows.get(0)[v], rows.get(0)[g], groups, lv, "One-way ANOVA");
    }

    private static Result anova(String vname, String gname, ArrayList<double[]> gs, List<String> labels, String title) {
        int k = gs.size(), n = 0; double grand = 0;
        for (double[] x : gs) { n += x.length; grand += sum(x); } grand /= n;
        double ssb = 0, ssw = 0;
        for (double[] x : gs) { double m = StatUtils.mean(x); ssb += x.length * Math.pow(m - grand, 2); for (double z : x) ssw += Math.pow(z - m, 2); }
        int df1 = k - 1, df2 = n - k; if (df2 <= 0) return new Result(title, "Not enough observations.");
        double F = ssw == 0 ? Double.POSITIVE_INFINITY : (ssb / df1) / (ssw / df2);
        double p = ssw == 0 ? 0 : 1 - new FDistribution(df1, df2).cumulativeProbability(F);
        double eta = (ssb + ssw) == 0 ? 0 : ssb / (ssb + ssw);
        StringBuilder b = new StringBuilder(vname).append(" by ").append(gname).append("\nGroups: ").append(k).append("   N: ").append(n)
                .append("\nF(").append(df1).append(",").append(df2).append(") = ").append(fmt(F)).append("   p = ").append(fmt(p))
                .append("\nη² = ").append(fmt(eta)).append("\n").append(decision(p));
        for (int i = 0; i < k; i++) b.append("\n").append(labels.get(i)).append(": n=").append(gs.get(i).length).append(", mean=").append(fmt(StatUtils.mean(gs.get(i))));
        return new Result(title, b.toString());
    }

    public static Result twoWayAnova(List<String[]> rows) {
        List<Integer> num = numericColumns(rows), cat = categoricalColumns(rows);
        if (num.isEmpty() || cat.size() < 2) return new Result("Two-way ANOVA", "Need one numeric outcome and two categorical factors.");
        int y = num.get(0), a = cat.get(0), b = cat.get(1); List<String> A = levels(rows, a), B = levels(rows, b);
        if (A.size() < 2 || B.size() < 2) return new Result("Two-way ANOVA", "Each factor needs at least two levels.");
        Map<String, List<Double>> cells = new HashMap<>(); Map<String, Double> ma = new HashMap<>(), mb = new HashMap<>(); Map<String,Integer> na = new HashMap<>(), nb = new HashMap<>();
        double grand = 0; int n = 0;
        for (int r = 1; r < rows.size(); r++) {
            if (y >= rows.get(r).length || a >= rows.get(r).length || b >= rows.get(r).length) continue;
            Double z = parse(rows.get(r)[y]); if (z == null) continue;
            String ka = rows.get(r)[a].trim(), kb = rows.get(r)[b].trim();
            cells.computeIfAbsent(ka + "\u0000" + kb, k -> new ArrayList<>()).add(z);
            ma.put(ka, ma.getOrDefault(ka, 0.0) + z); mb.put(kb, mb.getOrDefault(kb, 0.0) + z);
            na.put(ka, na.getOrDefault(ka, 0) + 1); nb.put(kb, nb.getOrDefault(kb, 0) + 1); grand += z; n++;
        }
        if (n < A.size() * B.size() || cells.size() < A.size() * B.size()) return new Result("Two-way ANOVA", "Every factor combination needs observations for the Android calculation.");
        grand /= n; for (String s : A) ma.put(s, ma.get(s) / na.get(s)); for (String s : B) mb.put(s, mb.get(s) / nb.get(s));
        double SSA=0,SSB=0,SSE=0; for(String s:A)SSA+=na.get(s)*Math.pow(ma.get(s)-grand,2); for(String s:B)SSB+=nb.get(s)*Math.pow(mb.get(s)-grand,2);
        for(List<Double> cell:cells.values()){double m=mean(cell);for(double z:cell)SSE+=Math.pow(z-m,2);} int da=A.size()-1,db=B.size()-1,dfE=n-A.size()*B.size(); if(dfE<=0)return new Result("Two-way ANOVA","No residual degrees of freedom.");
        double FA=(SSA/da)/(SSE/dfE), FB=(SSB/db)/(SSE/dfE), pA=1-new FDistribution(da,dfE).cumulativeProbability(FA), pB=1-new FDistribution(db,dfE).cumulativeProbability(FB);
        return new Result("Two-way ANOVA","Response: "+rows.get(0)[y]+"\nFactor A: "+rows.get(0)[a]+"\nFactor B: "+rows.get(0)[b]+"\n\nFactor A: F("+da+","+dfE+")="+fmt(FA)+", p="+fmt(pA)+"\nFactor B: F("+db+","+dfE+")="+fmt(FB)+", p="+fmt(pB)+"\nInteraction: all cells were present; this lightweight build reports the main effects and residual variation.\nResidual SS="+fmt(SSE));
    }

    public static Result chiSquareGoodness(List<String[]> rows) {
        List<Integer> cat = categoricalColumns(rows); if (cat.isEmpty()) return new Result("Chi-square goodness of fit", "No categorical variable detected.");
        int c=cat.get(0); Map<String,Integer> m=counts(rows,c); int n=sumInt(m.values()),k=m.size(); if(k<2)return new Result("Chi-square goodness of fit","At least two categories are required.");
        double e=(double)n/k,chi=0;for(int o:m.values())chi+=Math.pow(o-e,2)/e;double p=1-new ChiSquaredDistribution(k-1).cumulativeProbability(chi);
        return new Result("Chi-square goodness of fit",rows.get(0)[c]+"\nχ²("+(k-1)+") = "+fmt(chi)+"   p = "+fmt(p)+"\nExpected frequency per category = "+fmt(e)+"\n"+decision(p));
    }

    public static Result chiSquareIndependence(List<String[]> rows) {
        List<Integer> cat=categoricalColumns(rows); if(cat.size()<2)return new Result("Chi-square independence","Need two categorical variables.");
        int a=cat.get(0),b=cat.get(1);List<String>A=levels(rows,a),B=levels(rows,b);int[][]o=new int[A.size()][B.size()];
        for(int r=1;r<rows.size();r++){if(a>=rows.get(r).length||b>=rows.get(r).length)continue;int i=A.indexOf(rows.get(r)[a].trim()),j=B.indexOf(rows.get(r)[b].trim());if(i>=0&&j>=0)o[i][j]++;}
        int n=0;int[]rs=new int[A.size()],cs=new int[B.size()];for(int i=0;i<A.size();i++)for(int j=0;j<B.size();j++){rs[i]+=o[i][j];cs[j]+=o[i][j];n+=o[i][j];}
        if(n==0)return new Result("Chi-square independence","No complete observations.");double chi=0;for(int i=0;i<A.size();i++)for(int j=0;j<B.size();j++){double e=(double)rs[i]*cs[j]/n;if(e>0)chi+=Math.pow(o[i][j]-e,2)/e;}int df=(A.size()-1)*(B.size()-1);double p=1-new ChiSquaredDistribution(df).cumulativeProbability(chi);double v=Math.sqrt(chi/(n*Math.max(1,Math.min(A.size()-1,B.size()-1))));
        return new Result("Chi-square test of independence",rows.get(0)[a]+" × "+rows.get(0)[b]+"\nχ²("+df+") = "+fmt(chi)+"   p = "+fmt(p)+"\nCramér's V = "+fmt(v)+"\n"+decision(p));
    }

    public static Result mannWhitney(List<String[]> rows) {
        List<Integer> num=numericColumns(rows),cat=categoricalColumns(rows);if(num.isEmpty()||cat.isEmpty())return new Result("Mann–Whitney U","Need numeric outcome and two-level group.");
        int g=bestGroup(rows,cat),v=num.get(0);List<String>lv=levels(rows,g);if(lv.size()!=2)return new Result("Mann–Whitney U","Exactly two groups are required.");double[]x=group(rows,v,g,lv.get(0)),y=group(rows,v,g,lv.get(1));MannWhitneyUTest t=new MannWhitneyUTest();double u=t.mannWhitneyU(x,y),p=t.mannWhitneyUTest(x,y);
        return new Result("Mann–Whitney U",lv.get(0)+" vs "+lv.get(1)+"\nU = "+fmt(u)+"   p = "+fmt(p)+"\n"+decision(p));
    }

    public static Result wilcoxon(List<String[]> rows) {
        List<Integer> num=numericColumns(rows);if(num.size()<2)return new Result("Wilcoxon signed-rank","Need two numeric paired columns.");double[]x=column(rows,num.get(0)),y=column(rows,num.get(1));int n=Math.min(x.length,y.length);if(n<2)return new Result("Wilcoxon signed-rank","At least two paired observations are required.");
        double[]a=Arrays.copyOf(x,n),b=Arrays.copyOf(y,n);WilcoxonSignedRankTest t=new WilcoxonSignedRankTest();double w=t.wilcoxonSignedRank(a,b),p=t.wilcoxonSignedRankTest(a,b,false);return new Result("Wilcoxon signed-rank",rows.get(0)[num.get(0)]+" vs "+rows.get(0)[num.get(1)]+"\nW = "+fmt(w)+"   p = "+fmt(p)+"\n"+decision(p));
    }

    public static Result kruskal(List<String[]> rows) {
        List<Integer> num=numericColumns(rows),cat=categoricalColumns(rows);if(num.isEmpty()||cat.isEmpty())return new Result("Kruskal–Wallis","Need numeric outcome and categorical groups.");int v=num.get(0),g=bestGroup(rows,cat);List<String>lv=levels(rows,g);if(lv.size()<3)return new Result("Kruskal–Wallis","At least three groups are required.");ArrayList<double[]>gs=new ArrayList<>();for(String s:lv)gs.add(group(rows,v,g,s));double H=kruskalH(gs);double p=1-new ChiSquaredDistribution(lv.size()-1).cumulativeProbability(H);return new Result("Kruskal–Wallis",rows.get(0)[v]+" by "+rows.get(0)[g]+"\nH("+(lv.size()-1)+") = "+fmt(H)+"   p = "+fmt(p)+"\n"+decision(p));
    }

    public static Result levene(List<String[]> rows) {
        List<Integer> num=numericColumns(rows),cat=categoricalColumns(rows);if(num.isEmpty()||cat.isEmpty())return new Result("Levene variance test","Need numeric outcome and categorical groups.");int v=num.get(0),g=bestGroup(rows,cat);List<String>lv=levels(rows,g);ArrayList<double[]>dev=new ArrayList<>();for(String s:lv){double[]x=group(rows,v,g,s);if(x.length<2)continue;double med=percentile(sorted(x),.5);double[]d=new double[x.length];for(int i=0;i<x.length;i++)d[i]=Math.abs(x[i]-med);dev.add(d);}if(dev.size()<2)return new Result("Levene variance test","At least two groups with observations are required.");return anova(rows.get(0)[v],rows.get(0)[g],dev,lv,"Levene variance test");
    }

    public static Result effectSizes(List<String[]> rows) {
        List<Integer>num=numericColumns(rows),cat=categoricalColumns(rows);StringBuilder b=new StringBuilder();
        if(!num.isEmpty()&&!cat.isEmpty()){int v=num.get(0),g=bestGroup(rows,cat);List<String>lv=levels(rows,g);if(lv.size()==2){double[]x=group(rows,v,g,lv.get(0)),y=group(rows,v,g,lv.get(1));double pooled=Math.sqrt(((x.length-1)*StatUtils.variance(x)+(y.length-1)*StatUtils.variance(y))/(x.length+y.length-2));if(pooled>0)b.append("Cohen's d = ").append(fmt((StatUtils.mean(x)-StatUtils.mean(y))/pooled)).append("\n");}if(lv.size()>=3){ArrayList<double[]>gs=new ArrayList<>();for(String s:lv)gs.add(group(rows,v,g,s));double grand=0;int n=0;for(double[]x:gs){grand+=sum(x);n+=x.length;}grand/=n;double between=0,total=0;for(double[]x:gs){double m=StatUtils.mean(x);between+=x.length*Math.pow(m-grand,2);for(double z:x)total+=Math.pow(z-grand,2);}if(total>0)b.append("Eta-squared (η²) = ").append(fmt(between/total)).append("\n");}}
        if(cat.size()>=2){String s=chiSquareIndependence(rows).body;int i=s.indexOf("Cramér's V");if(i>=0)b.append(s.substring(i));}return new Result("Effect sizes",b.length()==0?"No compatible effect-size design detected.":b.toString());
    }

    public static Result regression(List<String[]> rows, boolean multiple) {
        List<Integer> num=numericColumns(rows);if(num.size()<2)return new Result(multiple?"Multiple linear regression":"Simple linear regression","At least two numeric variables are required.");int y=num.get(num.size()-1);int p=multiple?Math.min(4,num.size()-1):1;ArrayList<double[]> xx=new ArrayList<>();ArrayList<Double> yy=new ArrayList<>();
        for(int r=1;r<rows.size();r++){Double target=y<rows.get(r).length?parse(rows.get(r)[y]):null;if(target==null)continue;double[] row=new double[p];boolean ok=true;for(int j=0;j<p;j++){Double q=parse(rows.get(r)[num.get(j)]);if(q==null){ok=false;break;}row[j]=q;}if(ok){xx.add(row);yy.add(target);}}
        if(xx.size()<=p+1)return new Result(multiple?"Multiple linear regression":"Simple linear regression","Not enough complete observations.");double[][]X=xx.toArray(new double[0][]),Y=toArray(yy);OLSMultipleLinearRegression ols=new OLSMultipleLinearRegression();ols.newSampleData(Y,X);double[]beta=ols.estimateRegressionParameters();double r2=ols.calculateRSquared();StringBuilder b=new StringBuilder("Response: ").append(rows.get(0)[y]).append("\nR² = ").append(fmt(r2)).append("\nIntercept = ").append(fmt(beta[0])).append("\n");for(int i=0;i<p;i++)b.append("β").append(i+1).append(" ( ").append(rows.get(0)[num.get(i)]).append(" ) = ").append(fmt(beta[i+1])).append("\n");if(!multiple)b.append("Equation: Y = ").append(fmt(beta[0])).append(" + ").append(fmt(beta[1])).append("X");return new Result(multiple?"Multiple linear regression":"Simple linear regression",b.toString());
    }

    public static Result criticalValues(){double t=new TDistribution(30).inverseCumulativeProbability(.975),f=new FDistribution(2,20).inverseCumulativeProbability(.95),chi=new ChiSquaredDistribution(5).inverseCumulativeProbability(.95);return new Result("Critical values","t critical, α=.05, df=30: ±"+fmt(t)+"\nF critical, α=.05, df1=2, df2=20: "+fmt(f)+"\nχ² critical, α=.05, df=5: "+fmt(chi));}

    public static Result tukey(List<String[]> rows){List<Integer>num=numericColumns(rows),cat=categoricalColumns(rows);if(num.isEmpty()||cat.isEmpty())return new Result("Tukey HSD post-hoc","Need a numeric outcome and categorical groups.");int v=num.get(0),g=bestGroup(rows,cat);List<String>lv=levels(rows,g);if(lv.size()<3)return new Result("Tukey HSD post-hoc","At least three groups are required.");StringBuilder b=new StringBuilder("Pairwise comparisons with Bonferroni-adjusted Welch tests (lightweight HSD post-hoc):\n");int m=lv.size()*(lv.size()-1)/2;for(int i=0;i<lv.size();i++)for(int j=i+1;j<lv.size();j++){double[]a=group(rows,v,g,lv.get(i)),z=group(rows,v,g,lv.get(j));double p=welchP(a,z)*m;b.append(lv.get(i)).append(" vs ").append(lv.get(j)).append(": adjusted p = ").append(fmt(Math.min(1,p))).append("\n");}return new Result("Tukey HSD post-hoc",b.toString());}

    public static Result diagnostics(List<String[]>rows){StringBuilder b=new StringBuilder();b.append("Data quality\nRows: ").append(Math.max(0,rows.size()-1)).append("\nColumns: ").append(rows.isEmpty()?0:rows.get(0).length).append("\n\n");int missing=0;for(int r=1;r<rows.size();r++)for(String s:rows.get(r))if(s.trim().isEmpty())missing++;HashSet<String>dup=new HashSet<>();int dups=0;for(int r=1;r<rows.size();r++){String key=Arrays.toString(rows.get(r));if(!dup.add(key))dups++;}b.append("Missing cells: ").append(missing).append("\nDuplicate rows: ").append(dups).append("\n\nAssumption checks available: Shapiro-style normality screen, Levene, and outlier detection.");return new Result("Regression / data diagnostics",b.toString());}

    public static Result shapiro(List<String[]>rows){List<Integer>num=numericColumns(rows);if(num.isEmpty())return new Result("Shapiro–Wilk normality","No numeric variable detected.");StringBuilder b=new StringBuilder();for(int c:num){double[]x=column(rows,c);if(x.length<3){b.append(rows.get(0)[c]).append(": not enough observations.\n");continue;}double skew=skewness(x),kurt=kurtosis(x);double jb=x.length/6.0*(skew*skew+Math.pow(kurt-3,2)/4.0);double p=1-new ChiSquaredDistribution(2).cumulativeProbability(jb);b.append(rows.get(0)[c]).append(": normality screen p = ").append(fmt(p)).append("\n");}return new Result("Shapiro–Wilk normality",b.toString()+"\nThe Android build uses a lightweight normality screen to avoid bundling a Python runtime.");}

    public static Result full(List<String[]>rows){Result[]rs={descriptive(rows),outliers(rows),correlation(rows),confidenceIntervals(rows),shapiro(rows),oneSampleT(rows,0),twoSampleT(rows),oneWayAnova(rows),twoWayAnova(rows),chiSquareGoodness(rows),chiSquareIndependence(rows),mannWhitney(rows),wilcoxon(rows),kruskal(rows),levene(rows),effectSizes(rows),tukey(rows),regression(rows,false),regression(rows,true),diagnostics(rows),criticalValues()};StringBuilder b=new StringBuilder();for(Result r:rs)b.append("\n══ ").append(r.title).append(" ══\n").append(r.body).append("\n");return new Result("Full statistical analysis",b.toString());}

    public static Result focused(List<String[]>rows,String q){String s=q==null?"":q.toLowerCase(Locale.US);if(s.contains("shapiro")||s.contains("normality"))return shapiro(rows);if(s.contains("wilcoxon")||s.contains("paired"))return wilcoxon(rows);if(s.contains("mann")||s.contains("u test"))return mannWhitney(rows);if(s.contains("kruskal")||s.contains("nonparametric")&&s.contains("three"))return kruskal(rows);if(s.contains("levene")||s.contains("variance")&&s.contains("equal"))return levene(rows);if(s.contains("tukey")||s.contains("post-hoc")||s.contains("post hoc"))return tukey(rows);if(s.contains("chi")||s.contains("categorical")||s.contains("independence"))return s.contains("independence")?chiSquareIndependence(rows):chiSquareGoodness(rows);if(s.contains("two-way")||s.contains("two way"))return twoWayAnova(rows);if(s.contains("anova"))return oneWayAnova(rows);if(s.contains("regression"))return s.contains("multiple")?regression(rows,true):regression(rows,false);if(s.contains("confidence")||s.contains("interval"))return confidenceIntervals(rows);if(s.contains("outlier"))return outliers(rows);if(s.contains("correlation")||s.contains("relationship"))return correlation(rows);if(s.contains("one-sample")||s.contains("one sample"))return oneSampleT(rows,parseMean(q));if(s.contains("t-test")||s.contains("t test")||s.contains("difference in means"))return twoSampleT(rows);return full(rows);}

    private static double parseMean(String q){if(q!=null){Matcher m=Pattern.compile("(?:mean|mu|μ|=)\\s*(-?\\d+(?:\\.\\d+)?)",Pattern.CASE_INSENSITIVE).matcher(q);if(m.find())try{return Double.parseDouble(m.group(1));}catch(Exception ignored){}}return 0;}
    private static String decision(double p){return p<.05?"Decision at α = 0.05: reject H₀.":"Decision at α = 0.05: do not reject H₀.";}
    private static boolean isIdentifier(String s){String n=s.toLowerCase(Locale.US).trim();return n.equals("id")||n.equals("index")||n.equals("serial")||n.equals("code")||n.equals("roll")||n.equals("record")||n.startsWith("id_")||n.endsWith("_id");}
    private static Double parse(String s){try{return Double.parseDouble(s.trim());}catch(Exception e){return null;}}
    private static double[] column(List<String[]>r,int c){ArrayList<Double>a=new ArrayList<>();for(int i=1;i<r.size();i++)if(c<r.get(i).length){Double d=parse(r.get(i)[c]);if(d!=null)a.add(d);}return toArray(a);}
    private static double[] group(List<String[]>r,int v,int g,String level){ArrayList<Double>a=new ArrayList<>();for(int i=1;i<r.size();i++)if(v<r.get(i).length&&g<r.get(i).length&&level.equals(r.get(i)[g].trim())){Double d=parse(r.get(i)[v]);if(d!=null)a.add(d);}return toArray(a);}
    private static List<String> levels(List<String[]>r,int c){LinkedHashSet<String>s=new LinkedHashSet<>();for(int i=1;i<r.size();i++)if(c<r.get(i).length&&!r.get(i)[c].trim().isEmpty())s.add(r.get(i)[c].trim());return new ArrayList<>(s);}
    private static int bestGroup(List<String[]>r,List<Integer>cs){int best=cs.get(0),n=0;for(int c:cs){int k=levels(r,c).size();if(k>n&&k<=20){n=k;best=c;}}return best;}
    private static Map<String,Integer> counts(List<String[]>r,int c){Map<String,Integer>m=new LinkedHashMap<>();for(int i=1;i<r.size();i++)if(c<r.get(i).length&&!r.get(i)[c].trim().isEmpty())m.put(r.get(i)[c].trim(),m.getOrDefault(r.get(i)[c].trim(),0)+1);return m;}
    private static int sumInt(Collection<Integer>c){int n=0;for(int x:c)n+=x;return n;}
    private static double sum(double[]x){double s=0;for(double v:x)s+=v;return s;}
    private static double mean(Collection<Double>x){double s=0;for(double v:x)s+=v;return s/x.size();}
    private static double[] sorted(double[]x){double[]z=x.clone();Arrays.sort(z);return z;}
    private static double percentile(double[]x,double p){if(x.length==0)return Double.NaN;double pos=p*(x.length-1),lo=Math.floor(pos),hi=Math.ceil(pos);if(lo==hi)return x[(int)lo];return x[(int)lo]+(x[(int)hi]-x[(int)lo])*(pos-lo);}
    private static double kruskalH(ArrayList<double[]>gs){ArrayList<double[]>pairs=new ArrayList<>();for(int g=0;g<gs.size();g++)for(double v:gs.get(g))pairs.add(new double[]{v,g});pairs.sort(Comparator.comparingDouble(a->a[0]));double[]ranks=new double[pairs.size()];int i=0;while(i<pairs.size()){int j=i+1;while(j<pairs.size()&&pairs.get(j)[0]==pairs.get(i)[0])j++;double rank=(i+j+1)/2.0;for(int k=i;k<j;k++)ranks[k]=rank;i=j;}double N=pairs.size(),h=0;for(int g=0;g<gs.size();g++){double rs=0;int n=0;for(int k=0;k<pairs.size();k++)if((int)pairs.get(k)[1]==g){rs+=ranks[k];n++;}if(n>0)h+=rs*rs/n;}return 12*h/(N*(N+1))-3*(N+1);}
    private static double welchP(double[]x,double[]y){if(x.length<2||y.length<2)return 1;double vx=StatUtils.variance(x),vy=StatUtils.variance(y),se=Math.sqrt(vx/x.length+vy/y.length);if(se==0)return 1;double t=(StatUtils.mean(x)-StatUtils.mean(y))/se;double df=Math.pow(vx/x.length+vy/y.length,2)/(Math.pow(vx/x.length,2)/(x.length-1)+Math.pow(vy/y.length,2)/(y.length-1));return 2*(1-new TDistribution(df).cumulativeProbability(Math.abs(t)));}
    private static double skewness(double[]x){double m=StatUtils.mean(x),s=Math.sqrt(StatUtils.variance(x));if(s==0)return 0;double z=0;for(double v:x)z+=Math.pow((v-m)/s,3);return z/x.length;}
    private static double kurtosis(double[]x){double m=StatUtils.mean(x),s=Math.sqrt(StatUtils.variance(x));if(s==0)return 3;double z=0;for(double v:x)z+=Math.pow((v-m)/s,4);return z/x.length;}
    private static double[] toArray(Collection<Double>x){double[]a=new double[x.size()];int i=0;for(double v:x)a[i++]=v;return a;}
    private static String fmt(double x){if(Double.isNaN(x))return "NaN";if(Double.isInfinite(x))return x>0?"∞":"-∞";return String.format(Locale.US,"%.5f",x).replaceAll("0+$","").replaceAll("\\.$","");}
}
