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
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.xmlpull.v1.XmlPullParser;
import org.xmlpull.v1.XmlPullParserFactory;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

/** Stable Android 12 compatible StatsYuri UI and local analysis launcher. */
public class StatsYuriActivity extends Activity {
    private static final int PICK_FILE = 42;
    private FrameLayout root;
    private LinearLayout content;
    private TextView status;
    private TextView fileName;
    private EditText question;
    private Uri selectedUri;
    private List<String[]> dataset;
    private boolean dark = true;
    private final int DARK_BG = Color.rgb(8,11,17), LIGHT_BG = Color.rgb(247,248,251);
    private final int DARK_TEXT = Color.rgb(244,241,250), LIGHT_TEXT = Color.rgb(28,32,42);
    private final int MUTED = Color.rgb(160,170,188), CYAN = Color.rgb(141,216,255);
    private final ExecutorService ioExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "StatsYuri-worker");
        t.setDaemon(true);
        return t;
    });

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(DARK_BG);
        getWindow().setNavigationBarColor(DARK_BG);
        buildUi();
    }

    @Override protected void onDestroy() {
        ioExecutor.shutdownNow();
        super.onDestroy();
    }

    private void buildUi() {
        root=new FrameLayout(this);
        root.setBackgroundColor(DARK_BG);
        root.addView(new StatsBackgroundView(this),new FrameLayout.LayoutParams(-1,-1));
        LinearLayout toolbar=new LinearLayout(this);
        toolbar.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.setPadding(dp(14),0,dp(8),0);
        toolbar.setBackgroundColor(Color.argb(242,14,18,27));
        TextView title=text("StatsYuri",19,DARK_TEXT,true);
        title.setGravity(Gravity.CENTER_VERTICAL);
        toolbar.addView(title,new LinearLayout.LayoutParams(0,dp(58),1));
        Button theme=button("☾",20);
        theme.setContentDescription("Toggle theme");
        theme.setOnClickListener(v->toggleTheme());
        toolbar.addView(theme,toolbarParams());
        Button menu=button("⋮",23);
        menu.setContentDescription("Settings");
        menu.setOnClickListener(v->showSettings());
        toolbar.addView(menu,toolbarParams());
        FrameLayout.LayoutParams tp=new FrameLayout.LayoutParams(-1,dp(58));
        tp.gravity=Gravity.TOP;
        root.addView(toolbar,tp);
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.TRANSPARENT);
        content=new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(16),dp(14),dp(16),dp(28));
        scroll.addView(content);
        FrameLayout.LayoutParams sp=new FrameLayout.LayoutParams(-1,-1);
        sp.topMargin=dp(58);
        root.addView(scroll,sp);
        addHero();
        addDatasetCard();
        addAnalysisCard();
        addFooter();
        setContentView(root);
    }

    private LinearLayout.LayoutParams toolbarParams(){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(dp(58),dp(48));p.setMargins(dp(3),dp(4),0,dp(4));return p;}
    private void addHero(){TextView h=text("Making statistics easier to understand",23,CYAN,true);h.setPadding(0,dp(9),0,dp(3));content.addView(h);content.addView(text("A lightweight local workspace with the main StatsYuri analysis families. No Google sign-in, Python runtime, or cloud service is required.",14,MUTED,false),margins(0,0,0,12));}

    private void addDatasetCard(){
        LinearLayout card=card();
        card.addView(text("Dataset",20,currentText(),true));
        card.addView(text("CSV and XLSX are handled locally. Choose a file, then run a focused analysis or the complete analysis suite.",13,MUTED,false),margins(0,3,0,10));
        question=new EditText(this);
        question.setHint("What do you want to find out?  Example: compare the means of two groups");
        question.setHintTextColor(Color.rgb(120,130,148));
        question.setTextColor(currentText());
        question.setTextSize(15);
        question.setGravity(Gravity.TOP|Gravity.START);
        question.setMinHeight(dp(86));
        question.setPadding(dp(13),dp(11),dp(13),dp(11));
        question.setBackgroundColor(dark?Color.rgb(31,37,50):Color.rgb(239,242,247));
        card.addView(question,margins(0,0,0,10));
        Button choose=button("Choose CSV / XLSX dataset",15);
        choose.setOnClickListener(v->chooseFile());
        card.addView(choose,margins(0,0,0,2));
        fileName=text("No dataset selected",12,MUTED,false);
        card.addView(fileName,margins(0,2,0,8));
        status=text("Ready. Select a dataset to begin.",13,CYAN,true);
        card.addView(status,margins(0,3,0,0));
        content.addView(card,margins(0,0,0,12));
    }

    private void addAnalysisCard(){LinearLayout card=card();card.addView(text("Analysis tools",20,currentText(),true));card.addView(text("The Android build exposes the main model families used by the Streamlit app: descriptive statistics, tests, ANOVA, chi-square, non-parametric methods, effect sizes, regression, diagnostics and critical values.",13,MUTED,false),margins(0,3,0,10));HorizontalScrollView hsv=new HorizontalScrollView(this);LinearLayout row=new LinearLayout(this);row.setPadding(0,0,0,dp(4));String[][]tools={{"Auto","auto"},{"Full","full"},{"Descriptive","desc"},{"Parametric","param"},{"ANOVA","anova"},{"Non-parametric","nonparam"},{"Association","assoc"},{"Regression","reg"},{"Diagnostics","diag"}};for(String[]t:tools){Button b=button(t[0],14);b.setOnClickListener(v->runTool(t[1]));row.addView(b,new LinearLayout.LayoutParams(dp(122),dp(48)));}hsv.addView(row);card.addView(hsv);content.addView(card,margins(0,0,0,12));}
    private void addFooter(){TextView f=text("© 2026 Yugen Beyondverse. All rights reserved.",10,Color.rgb(105,112,128),false);f.setGravity(Gravity.CENTER);content.addView(f,margins(0,14,0,0));}

    private void chooseFile(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("*/*");i.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"text/csv","text/comma-separated-values","application/csv","application/vnd.ms-excel","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","text/plain"});startActivityForResult(i,PICK_FILE);}

    @Override protected void onActivityResult(int requestCode,int resultCode,Intent data){
        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=PICK_FILE||resultCode!=RESULT_OK||data==null||data.getData()==null)return;
        selectedUri=data.getData();
        try{
            int flags=data.getFlags()&(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            if((flags&Intent.FLAG_GRANT_READ_URI_PERMISSION)!=0) getContentResolver().takePersistableUriPermission(selectedUri,flags);
        }catch(Exception ignored){}
        fileName.setText(getFileName(selectedUri));
        status.setText("File selected. Reading locally…");
        final Uri uri=selectedUri;
        ioExecutor.execute(()->{
            try{
                String name=getFileName(uri).toLowerCase(Locale.US);
                List<String[]>rows=name.endsWith(".xlsx")?readXlsx(uri):readCsv(uri);
                runOnUiThread(()->{
                    dataset=rows;
                    status.setText("Dataset ready: "+Math.max(0,rows.size()-1)+" rows × "+(rows.isEmpty()?0:rows.get(0).length)+" columns.");
                });
            }catch(Exception e){
                final String message=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();
                runOnUiThread(()->status.setText("Could not read file: "+message));
            }
        });
    }

    private String getFileName(Uri uri){try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){if(c!=null&&c.moveToFirst()){int i=c.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(i>=0)return c.getString(i);}}catch(Exception ignored){}return uri.toString();}
    private List<String[]> readCsv(Uri uri)throws Exception{ArrayList<String[]>rows=new ArrayList<>();try(InputStream in=getContentResolver().openInputStream(uri)){if(in==null)throw new IllegalStateException("file could not be opened");try(BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null&&rows.size()<10001)if(!line.trim().isEmpty())rows.add(splitCsv(line));}}return rows;}
    private String[] splitCsv(String line){ArrayList<String>v=new ArrayList<>();StringBuilder b=new StringBuilder();boolean q=false;for(int i=0;i<line.length();i++){char c=line.charAt(i);if(c=='"'){if(q&&i+1<line.length()&&line.charAt(i+1)=='"'){b.append('"');i++;}else q=!q;}else if(c==','&&!q){v.add(b.toString().trim());b.setLength(0);}else b.append(c);}v.add(b.toString().trim());return v.toArray(new String[0]);}

    private List<String[]> readXlsx(Uri uri)throws Exception{ArrayList<String[]>rows=new ArrayList<>();ArrayList<String>shared=new ArrayList<>();String sheet=null;try(InputStream raw=getContentResolver().openInputStream(uri)){if(raw==null)throw new IllegalStateException("file could not be opened");try(ZipInputStream z=new ZipInputStream(raw)){ZipEntry e;while((e=z.getNextEntry())!=null){if(e.getName().equals("xl/sharedStrings.xml"))shared=parseSharedStrings(z);else if(e.getName().equals("xl/worksheets/sheet1.xml"))sheet=readText(z);}}}if(sheet==null)throw new IllegalStateException("first worksheet was not found");return parseSheet(sheet,shared);}
    private String readText(InputStream in)throws Exception{StringBuilder b=new StringBuilder();byte[]buf=new byte[8192];int n;while((n=in.read(buf))!=-1)b.append(new String(buf,0,n,StandardCharsets.UTF_8));return b.toString();}
    private ArrayList<String> parseSharedStrings(InputStream in)throws Exception{ArrayList<String>out=new ArrayList<>();XmlPullParser p=XmlPullParserFactory.newInstance().newPullParser();p.setInput(in,"UTF-8");StringBuilder s=null;for(int e=p.getEventType();e!=XmlPullParser.END_DOCUMENT;e=p.next()){if(e==XmlPullParser.START_TAG&&"si".equals(p.getName()))s=new StringBuilder();else if(e==XmlPullParser.TEXT&&s!=null)s.append(p.getText());else if(e==XmlPullParser.END_TAG&&"si".equals(p.getName())&&s!=null){out.add(s.toString());s=null;}}return out;}
    private List<String[]> parseSheet(String xml,List<String>shared)throws Exception{ArrayList<String[]>rows=new ArrayList<>();XmlPullParser p=XmlPullParserFactory.newInstance().newPullParser();p.setInput(new java.io.StringReader(xml));ArrayList<String>cur=null;String type=null,ref=null,val=null;for(int e=p.getEventType();e!=XmlPullParser.END_DOCUMENT;e=p.next()){if(e==XmlPullParser.START_TAG&&"row".equals(p.getName()))cur=new ArrayList<>();else if(e==XmlPullParser.START_TAG&&"c".equals(p.getName())){ref=p.getAttributeValue(null,"r");type=p.getAttributeValue(null,"t");val=null;}else if(e==XmlPullParser.START_TAG&&"v".equals(p.getName())&&cur!=null)val=p.nextText();else if(e==XmlPullParser.END_TAG&&"c".equals(p.getName())&&cur!=null){String s=val==null?"":val;if("s".equals(type)){try{s=shared.get(Integer.parseInt(s));}catch(Exception ignored){}}int col=columnIndex(ref);while(cur.size()<=col)cur.add("");cur.set(col,s);}else if(e==XmlPullParser.END_TAG&&"row".equals(p.getName())&&cur!=null){rows.add(cur.toArray(new String[0]));cur=null;}}return rows;}
    private int columnIndex(String ref){if(ref==null)return 0;int n=0;for(int i=0;i<ref.length();i++){char c=ref.charAt(i);if(Character.isLetter(c))n=n*26+(Character.toUpperCase(c)-'A'+1);else break;}return Math.max(0,n-1);}

    private void runTool(String tool){
        if(dataset==null||dataset.size()<2){status.setText("Choose a dataset first.");return;}
        final String questionText=question==null?"":question.getText().toString();
        status.setText("Running locally…");
        ioExecutor.execute(()->{
            try{
                StatisticsEngine.Result r;
                if("auto".equals(tool))r=StatisticsEngine.focused(dataset,questionText);
                else if("full".equals(tool))r=StatisticsEngine.full(dataset);
                else if("desc".equals(tool))r=StatisticsEngine.descriptive(dataset);
                else if("param".equals(tool))r=new StatisticsEngine.Result("Parametric analyses",StatisticsEngine.oneSampleT(dataset,0).body+"\n\n"+StatisticsEngine.twoSampleT(dataset).body+"\n\n"+StatisticsEngine.confidenceIntervals(dataset).body);
                else if("anova".equals(tool))r=new StatisticsEngine.Result("ANOVA family",StatisticsEngine.oneWayAnova(dataset).body+"\n\n"+StatisticsEngine.twoWayAnova(dataset).body+"\n\n"+StatisticsEngine.tukey(dataset).body);
                else if("nonparam".equals(tool))r=new StatisticsEngine.Result("Non-parametric analyses",StatisticsEngine.mannWhitney(dataset).body+"\n\n"+StatisticsEngine.wilcoxon(dataset).body+"\n\n"+StatisticsEngine.kruskal(dataset).body);
                else if("assoc".equals(tool))r=new StatisticsEngine.Result("Association and effect sizes",StatisticsEngine.correlation(dataset).body+"\n\n"+StatisticsEngine.chiSquareGoodness(dataset).body+"\n\n"+StatisticsEngine.chiSquareIndependence(dataset).body+"\n\n"+StatisticsEngine.effectSizes(dataset).body);
                else if("reg".equals(tool))r=new StatisticsEngine.Result("Regression",StatisticsEngine.regression(dataset,false).body+"\n\n"+StatisticsEngine.regression(dataset,true).body);
                else r=new StatisticsEngine.Result("Diagnostics",StatisticsEngine.diagnostics(dataset).body+"\n\n"+StatisticsEngine.shapiro(dataset).body+"\n\n"+StatisticsEngine.levene(dataset).body+"\n\n"+StatisticsEngine.outliers(dataset).body+"\n\n"+StatisticsEngine.criticalValues().body);
                final StatisticsEngine.Result result=r;
                runOnUiThread(()->showResult(result));
            }catch(Throwable e){
                final String message=e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();
                runOnUiThread(()->status.setText("Analysis error: "+message));
            }
        });
    }

    private void showResult(StatisticsEngine.Result r){status.setText("Completed locally: "+r.title);LinearLayout card=card();card.addView(text(r.title,19,currentText(),true));TextView body=text(r.body,14,currentText(),false);body.setLineSpacing(dp(3),1f);body.setTextIsSelectable(true);body.setPadding(dp(4),dp(10),dp(4),dp(10));card.addView(body);content.addView(card,Math.max(0,content.getChildCount()-1));}
    private void toggleTheme(){dark=!dark;root.setBackgroundColor(dark?DARK_BG:LIGHT_BG);getWindow().setStatusBarColor(dark?DARK_BG:LIGHT_BG);getWindow().setNavigationBarColor(dark?DARK_BG:LIGHT_BG);status.setTextColor(dark?CYAN:Color.rgb(45,111,150));status.setText("Theme changed. Analysis remains local.");}
    private void showSettings(){new AlertDialog.Builder(this).setTitle("StatsYuri settings").setMessage("Appearance\nUse the moon button for dark/light mode.\n\nAnalysis\nFocused mode follows your question; Full runs all compatible model families.\n\nPrivacy\nFiles are processed locally by this Android build. Google sign-in and cloud data access are intentionally disabled in this stable Android 12 build.\n\n© 2026 Yugen Beyondverse. All rights reserved.").setPositiveButton("Close",null).show();}
    private LinearLayout card(){LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(18),dp(17),dp(18),dp(18));c.setBackgroundColor(dark?Color.argb(238,20,25,36):Color.argb(245,255,255,255));return c;}
    private Button button(String s,int size){Button b=new Button(this);b.setText(s);b.setTextSize(size);b.setAllCaps(false);b.setMinWidth(0);b.setMinHeight(0);b.setPadding(dp(8),0,dp(8),0);b.setTextColor(currentText());return b;}
    private TextView text(String s,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);t.setLineSpacing(dp(2),1f);return t;}
    private int currentText(){return dark?DARK_TEXT:LIGHT_TEXT;}
    private LinearLayout.LayoutParams margins(int l,int t,int r,int b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(dp(l),dp(t),dp(r),dp(b));return p;}
    private int dp(int v){return Math.round(v*getResources().getDisplayMetrics().density);}
}
