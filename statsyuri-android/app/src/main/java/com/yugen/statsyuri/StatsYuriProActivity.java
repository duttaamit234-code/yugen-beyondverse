package com.yugen.statsyuri;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;

import org.xmlpull.v1.XmlPullParser;
import org.xmlpull.v1.XmlPullParserFactory;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/** Professional offline-first Android workspace. */
public final class StatsYuriProActivity extends Activity {
    private static final int PICK_FILE = 77;
    private FrameLayout root; private LinearLayout content, reportHost; private TextView status, fileName; private EditText question;
    private List<String[]> dataset; private boolean dark = true; private StatsChartView chart;
    private final ExecutorService worker = Executors.newSingleThreadExecutor(r -> { Thread t=new Thread(r,"StatsYuri-analysis");t.setDaemon(true);return t; });

    @Override protected void onCreate(Bundle state){super.onCreate(state);build();}
    @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}

    private void build(){
        int bg=dark?0xFF080B11:0xFFF6F7FA;getWindow().setStatusBarColor(bg);getWindow().setNavigationBarColor(bg);
        root=new FrameLayout(this);root.setBackgroundColor(bg);StatsBackgroundView background=new StatsBackgroundView(this);background.setLightMode(!dark);root.addView(background,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout toolbar=new LinearLayout(this);toolbar.setGravity(Gravity.CENTER_VERTICAL);toolbar.setPadding(dp(14),0,dp(8),0);toolbar.setBackgroundColor(dark?0xF20E121B:0xF2FFFFFF);
        TextView brand=text("StatsYuri",20,primaryText(),true);brand.setGravity(Gravity.CENTER_VERTICAL);toolbar.addView(brand,new LinearLayout.LayoutParams(0,dp(58),1));
        Button theme=actionButton(dark?"☼":"☾",20);theme.setContentDescription("Toggle light and dark theme");theme.setOnClickListener(v->{dark=!dark;build();});toolbar.addView(theme,new LinearLayout.LayoutParams(dp(58),dp(48)));
        Button menu=actionButton("⋮",23);menu.setContentDescription("StatsYuri information");menu.setOnClickListener(v->showAbout());toolbar.addView(menu,new LinearLayout.LayoutParams(dp(58),dp(48)));
        root.addView(toolbar,new FrameLayout.LayoutParams(-1,dp(58)));
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(16),dp(12),dp(16),dp(32));scroll.addView(content);FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-1,-1);sp.topMargin=dp(58);root.addView(scroll,sp);
        addHero();addDatasetSection();addToolsSection();addChartSection();addReportSection();addFooter();setContentView(root);
        if(dataset!=null){updateDatasetUi();updateChart(StatsChartView.Mode.HISTOGRAM);}
    }

    private void addHero(){content.addView(text("Analyze. Visualize. Understand.",27,dark?0xFF9EDCFF:0xFF356E9E,true),margins(0,6,0,3));content.addView(text("A local statistics workspace designed as one continuous report, not a pile of tiny boxes pretending to be software.",14,muted(),false),margins(0,0,0,14));}

    private void addDatasetSection(){LinearLayout card=surface();card.addView(text("1  Dataset",20,primaryText(),true));card.addView(text("Import a dataset, preview the actual rows, then choose automatic or focused analysis.",13,muted(),false),margins(0,3,0,10));
        question=new EditText(this);question.setHint("Optional question: e.g. compare yield across treatments");question.setHintTextColor(dark?0xFF7D8697:0xFF7A8391);question.setTextColor(primaryText());question.setTextSize(15);question.setGravity(Gravity.TOP|Gravity.START);question.setMinHeight(dp(74));question.setPadding(dp(13),dp(11),dp(13),dp(11));question.setBackgroundColor(dark?0xFF1F2532:0xFFEDF0F5);card.addView(question,margins(0,0,0,9));
        Button choose=actionButton("Choose CSV / XLSX / XLS",15);choose.setOnClickListener(v->chooseFile());card.addView(choose,margins(0,0,0,2));fileName=text("No dataset selected",12,muted(),false);card.addView(fileName,margins(0,2,0,3));status=text("Ready. Your data stays on the device.",13,dark?0xFF9EDCFF:0xFF356E9E,true);card.addView(status,margins(0,2,0,0));content.addView(card,margins(0,0,0,10));}

    private void addToolsSection(){LinearLayout card=surface();card.addView(text("2  Analysis",20,primaryText(),true));card.addView(text("The full engine mirrors the web project's analysis families. Start focused, or let the suite run every compatible method.",13,muted(),false),margins(0,3,0,8));HorizontalScrollView hsv=new HorizontalScrollView(this);hsv.setHorizontalScrollBarEnabled(false);LinearLayout row=new LinearLayout(this);
        String[][]tools={{"✦  Automatic","auto"},{"▦  Full suite","full"},{"Σ  Descriptive","desc"},{"t  t-tests","ttest"},{"F  ANOVA","anova"},{"ρ  Correlation","corr"},{"↗  Regression","reg"},{"χ²  Association","chi"},{"◌  Non-parametric","nonparam"},{"⚙  Diagnostics","diag"}};
        for(String[]item:tools){Button b=actionButton(item[0],13);b.setOnClickListener(v->run(item[1]));row.addView(b,new LinearLayout.LayoutParams(dp(138),dp(46)));}hsv.addView(row);card.addView(hsv);content.addView(card,margins(0,0,0,10));}

    private void addChartSection(){LinearLayout card=surface();card.addView(text("3  Visualize",20,primaryText(),true));card.addView(text("Charts are generated from the loaded data, not pasted screenshots or decorative numbers.",13,muted(),false),margins(0,3,0,7));chart=new StatsChartView(this);card.addView(chart,margins(0,2,0,7));LinearLayout modes=new LinearLayout(this);String[][]m={{"Distribution","hist"},{"Scatter","scatter"},{"Box plot","box"}};for(String[]x:m){Button b=actionButton(x[0],12);b.setOnClickListener(v->updateChart("scatter".equals(x[1])?StatsChartView.Mode.SCATTER:"box".equals(x[1])?StatsChartView.Mode.BOXPLOT:StatsChartView.Mode.HISTOGRAM));modes.addView(b,new LinearLayout.LayoutParams(0,dp(42),1));}card.addView(modes);content.addView(card,margins(0,0,0,10));}

    private void addReportSection(){LinearLayout card=surface();card.addView(text("4  Results",20,primaryText(),true));card.addView(text("Results use readable headings, assumptions, calculation blocks and interpretation rather than one enormous paragraph.",13,muted(),false),margins(0,3,0,8));reportHost=new LinearLayout(this);reportHost.setOrientation(LinearLayout.VERTICAL);reportHost.addView(text("Run an analysis to generate the report.",14,muted(),false));card.addView(reportHost);content.addView(card,margins(0,0,0,10));}
    private void addFooter(){TextView footer=text("StatsYuri  •  Yugen Beyondverse Studios  •  Local-first statistics",10,dark?0xFF7A8292:0xFF737B89,false);footer.setGravity(Gravity.CENTER);content.addView(footer,margins(0,10,0,0));}

    private void chooseFile(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"text/csv","text/comma-separated-values","application/csv","application/vnd.ms-excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","text/plain"});startActivityForResult(i,PICK_FILE);}

    private String getFileName(Uri uri){try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0){String n=c.getString(i);if(n!=null&&!n.isEmpty())return n;}}}catch(Exception ignored){}String s=uri.getLastPathSegment();return s==null?"dataset":s;}

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){super.onActivityResult(requestCode,resultCode,data);if(requestCode!=PICK_FILE||resultCode!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();try{int flags=data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);if((flags&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0)getContentResolver().takePersistableUriPermission(uri,flags);}catch(Exception ignored){}fileName.setText(getFileName(uri));status.setText("Reading dataset locally…");worker.execute(()->{try{String name=getFileName(uri).toLowerCase(Locale.US);List<String[]>rows;if(name.endsWith(".xlsx"))rows=readXlsx(uri);else if(name.endsWith(".xls"))throw new IllegalStateException("Legacy .xls is not enabled in this safe build. Save it as .xlsx or .csv on the device.");else rows=readCsv(uri);dataset=rows;runOnUiThread(this::updateDatasetUi);}catch(Throwable e){String msg=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();runOnUiThread(()->status.setText("Could not read file: "+msg));}});}

    private void updateDatasetUi(){if(dataset==null||dataset.isEmpty())return;int cols=dataset.get(0).length;status.setText("Loaded locally  •  "+Math.max(0,dataset.size()-1)+" rows × "+cols+" columns");fileName.setText(fileName.getText()+"  ✓");addPreview();updateChart(StatsChartView.Mode.HISTOGRAM);}

    private void addPreview(){for(int i=content.getChildCount()-1;i>=0;i--)if("__preview__".equals(content.getChildAt(i).getTag()))content.removeViewAt(i);if(dataset==null||dataset.isEmpty())return;LinearLayout card=surface();card.setTag("__preview__");card.addView(text("Dataset preview",17,primaryText(),true),margins(0,0,0,7));HorizontalScrollView hsv=new HorizontalScrollView(this);TableLayout table=new TableLayout(this);int rows=Math.min(dataset.size(),9),cols=Math.min(dataset.get(0).length,12);for(int r=0;r<rows;r++){TableRow tr=new TableRow(this);for(int c=0;c<cols;c++){String value=c<dataset.get(r).length?dataset.get(r)[c]:"";TextView cell=text(value,12,r==0?(dark?0xFF071018:0xFF25374A):primaryText(),r==0);cell.setPadding(dp(10),dp(8),dp(10),dp(8));cell.setBackgroundColor(r==0?(dark?0xFF9EDCFF:0xFFD8EAF7):(r%2==0?(dark?0xFF1C2330:0xFFF3F5F8):(dark?0xFF171D28:0xFFFFFFFF)));tr.addView(cell,new TableRow.LayoutParams(dp(118),-2));}table.addView(tr);}hsv.addView(table);card.addView(hsv);card.addView(text(rows<dataset.size()?"Showing first 8 rows. Use analysis results for the complete calculation.":"Preview complete.",11,muted(),false),margins(0,6,0,0));content.addView(card,Math.min(2,content.getChildCount()-1));}
    private void updateChart(StatsChartView.Mode mode){if(chart!=null)chart.setData(dataset,mode,dark);}

    private void run(String kind){if(dataset==null||dataset.size()<2){status.setText("Choose a dataset first.");return;}status.setText("Calculating locally…");final String q=question==null?"":question.getText().toString();worker.execute(()->{try{StatisticsEngine.Result r;if("auto".equals(kind))r=StatisticsEngine.focused(dataset,q);else if("full".equals(kind))r=StatisticsEngine.full(dataset);else if("desc".equals(kind))r=StatisticsEngine.descriptive(dataset);else if("ttest".equals(kind))r=new StatisticsEngine.Result("t-test family",StatisticsEngine.oneSampleT(dataset,0).body+"\n\n"+StatisticsEngine.twoSampleT(dataset).body+"\n\n"+StatisticsEngine.confidenceIntervals(dataset).body);else if("anova".equals(kind))r=new StatisticsEngine.Result("ANOVA family",StatisticsEngine.oneWayAnova(dataset).body+"\n\n"+StatisticsEngine.twoWayAnova(dataset).body);else if("corr".equals(kind))r=StatisticsEngine.correlation(dataset);else if("reg".equals(kind))r=StatisticsEngine.regression(dataset,false);else if("chi".equals(kind))r=new StatisticsEngine.Result("Association tests",StatisticsEngine.chiSquareGoodness(dataset).body+"\n\n"+StatisticsEngine.chiSquareIndependence(dataset).body+"\n\n"+StatisticsEngine.effectSizes(dataset).body);else if("nonparam".equals(kind))r=new StatisticsEngine.Result("Non-parametric tests",StatisticsEngine.mannWhitney(dataset).body+"\n\n"+StatisticsEngine.wilcoxon(dataset).body+"\n\n"+StatisticsEngine.kruskal(dataset).body);else r=new StatisticsEngine.Result("Diagnostics",StatisticsEngine.outliers(dataset).body+"\n\n"+StatisticsEngine.shapiro(dataset).body+"\n\n"+StatisticsEngine.levene(dataset).body);final StatisticsEngine.Result result=r;runOnUiThread(()->showResult(result));}catch(Throwable e){String msg=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();runOnUiThread(()->status.setText("Analysis error: "+msg));}});}

    private void showResult(StatisticsEngine.Result result){status.setText("Completed locally  •  "+result.title);reportHost.removeAllViews();AnalysisReportView report=new AnalysisReportView(this,dark);reportHost.addView(report.render(result));}
    private void showAbout(){new AlertDialog.Builder(this).setTitle("StatsYuri").setMessage("Statistical Analysis Made Simple\n\nLocal-first Android build. No Google sign-in, cloud service or Python runtime is required for the core analysis engine.\n\nThe Android design follows consistent spacing, adaptive content structure and Material-style hierarchy rather than stuffing every statistic into a tiny card.").setPositiveButton("Close",null).show();}

    private List<String[]> readCsv(Uri uri)throws Exception{ArrayList<String[]>rows=new ArrayList<>();try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)throw new IllegalStateException("file could not be opened");try(BufferedReader reader=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String line;while((line=reader.readLine())!=null&&rows.size()<=10001)if(!line.trim().isEmpty())rows.add(splitCsv(line));}}return rows;}
    private String[] splitCsv(String line){ArrayList<String>values=new ArrayList<>();StringBuilder current=new StringBuilder();boolean quoted=false;for(int i=0;i<line.length();i++){char c=line.charAt(i);if(c=='"'){if(quoted&&i+1<line.length()&&line.charAt(i+1)=='"'){current.append('"');i++;}else quoted=!quoted;}else if(c==','&&!quoted){values.add(current.toString().trim());current.setLength(0);}else current.append(c);}values.add(current.toString().trim());return values.toArray(new String[0]);}

    private List<String[]> readXlsx(Uri uri)throws Exception{ArrayList<String>shared=new ArrayList<>();String sheet=null;try(InputStream raw=getContentResolver().openInputStream(uri)){if(raw==null)throw new IllegalStateException("file could not be opened");try(ZipInputStream zip=new ZipInputStream(raw)){ZipEntry e;while((e=zip.getNextEntry())!=null){if("xl/sharedStrings.xml".equals(e.getName()))shared=parseSharedStrings(zip);else if("xl/worksheets/sheet1.xml".equals(e.getName()))sheet=readText(zip);}}}if(sheet==null)throw new IllegalStateException("first worksheet was not found");return parseSheet(sheet,shared);}
    private String readText(InputStream in)throws Exception{StringBuilder b=new StringBuilder();byte[]buf=new byte[8192];int n;while((n=in.read(buf))!=-1)b.append(new String(buf,0,n,StandardCharsets.UTF_8));return b.toString();}
    private ArrayList<String> parseSharedStrings(InputStream in)throws Exception{ArrayList<String>out=new ArrayList<>();XmlPullParser p=XmlPullParserFactory.newInstance().newPullParser();p.setInput(in,"UTF-8");StringBuilder s=null;for(int e=p.getEventType();e!=XmlPullParser.END_DOCUMENT;e=p.next()){if(e==XmlPullParser.START_TAG&&"si".equals(p.getName()))s=new StringBuilder();else if(e==XmlPullParser.TEXT&&s!=null)s.append(p.getText());else if(e==XmlPullParser.END_TAG&&"si".equals(p.getName())&&s!=null){out.add(s.toString());s=null;}}return out;}
    private List<String[]> parseSheet(String xml,List<String>shared)throws Exception{ArrayList<String[]>rows=new ArrayList<>();XmlPullParser p=XmlPullParserFactory.newInstance().newPullParser();p.setInput(new StringReader(xml));ArrayList<String>cur=null;String type=null,ref=null,value=null;for(int e=p.getEventType();e!=XmlPullParser.END_DOCUMENT;e=p.next()){if(e==XmlPullParser.START_TAG&&"row".equals(p.getName()))cur=new ArrayList<>();else if(e==XmlPullParser.START_TAG&&"c".equals(p.getName())){ref=p.getAttributeValue(null,"r");type=p.getAttributeValue(null,"t");value=null;}else if(e==XmlPullParser.START_TAG&&"v".equals(p.getName())&&cur!=null)value=p.nextText();else if(e==XmlPullParser.END_TAG&&"c".equals(p.getName())&&cur!=null){String s=value==null?"":value;if("s".equals(type))try{s=shared.get(Integer.parseInt(s));}catch(Exception ignored){}int col=columnIndex(ref);while(cur.size()<=col)cur.add("");cur.set(col,s);}else if(e==XmlPullParser.END_TAG&&"row".equals(p.getName())&&cur!=null){rows.add(cur.toArray(new String[0]));cur=null;}}return rows;}
    private int columnIndex(String ref){if(ref==null)return 0;int n=0;for(int i=0;i<ref.length();i++){char c=ref.charAt(i);if(!Character.isLetter(c))break;n=n*26+Character.toUpperCase(c)-'A'+1;}return Math.max(0,n-1);}

    private LinearLayout surface(){LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(15),dp(14),dp(15),dp(14));c.setBackgroundColor(dark?0xEC141A26:0xF7FFFFFF);return c;}
    private Button actionButton(String label,int size){Button b=new Button(this);b.setText(label);b.setTextSize(size);b.setAllCaps(false);b.setTypeface(Typeface.DEFAULT,Typeface.BOLD);b.setTextColor(primaryText());b.setMinWidth(0);b.setMinHeight(0);b.setPadding(dp(8),0,dp(8),0);b.setBackgroundColor(dark?0xFF303746:0xFFE6EAF1);return b;}
    private TextView text(String value,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);t.setLineSpacing(dp(2),1f);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private LinearLayout.LayoutParams margins(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int primaryText(){return dark?0xFFF4F1FA:0xFF1C202A;}private int muted(){return dark?0xFFA6B0C2:0xFF596476;}private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
}
