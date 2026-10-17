package com.example.photoviewer;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.net.Uri;
import android.view.*;
import android.widget.*;
import android.text.InputType;
import org.json.*;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.LinearLayoutManager;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Native Android client. All network and bitmap work runs off the UI thread. */
public class MainActivity extends Activity {
    private static final int GREEN = Color.rgb(49, 82, 61), INK = Color.rgb(36, 48, 39);
    private final ExecutorService worker = Executors.newFixedThreadPool(3);
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final List<JSONObject> posts = new ArrayList<>();
    private final Set<String> favorites = new HashSet<>();
    private android.content.SharedPreferences prefs;
    private LinearLayout root;
    private RecyclerView cards;
    private boolean lectureMode;
    private TextView status, counter;
    private EditText search, titleInput, textInput;
    private Button sync, upload, previous, next, choose;
    private String base, token, username, nextUrl, previousUrl, draftTitle = "", draftText = "";
    private Uri selectedImage;
    private boolean favoriteOnly = false, loading = false;
    private long generation = 0;
    private AlertDialog editor;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("photo-blog", MODE_PRIVATE);
        base = prefs.getString("server", "http://10.0.2.2:8000");
        lectureMode = prefs.getBoolean("lecture", true);
        token = prefs.getString("token", ""); username = prefs.getString("username", "");
        favorites.addAll(prefs.getStringSet("favorites", Collections.emptySet()));
        if (state != null) {
            draftTitle = state.getString("draftTitle", ""); draftText = state.getString("draftText", "");
            String uri = state.getString("image"); if (uri != null) selectedImage = Uri.parse(uri);
        }
        buildScreen();
        try {
            JSONArray cache = new JSONArray(prefs.getString("cache", "[]"));
            for (int i=0;i<cache.length();i++) posts.add(cache.getJSONObject(i));
            if (!posts.isEmpty()) { render(); status.setText("저장된 목록 · 동기화하여 최신 사진을 확인하세요"); }
        } catch(JSONException ignored) { }
    }
    @Override protected void onSaveInstanceState(Bundle out) {
        saveDraft(); out.putString("draftTitle", draftTitle); out.putString("draftText", draftText);
        if(selectedImage!=null) out.putString("image",selectedImage.toString()); super.onSaveInstanceState(out);
    }
    private int dp(int n) { return (int)(n * getResources().getDisplayMetrics().density); }
    private TextView label(String value, int size, int color) {
        TextView v = new TextView(this); v.setText(value); v.setTextSize(size); v.setTextColor(color); return v;
    }
    private LinearLayout column() { LinearLayout v = new LinearLayout(this); v.setOrientation(LinearLayout.VERTICAL); return v; }
    private Button button(String text, Runnable action) {
        Button b = new Button(this); b.setText(text); b.setAllCaps(false); b.setTextColor(GREEN); b.setOnClickListener(v->action.run()); return b;
    }
    private EditText field(String hint) {
        EditText e = new EditText(this); e.setHint(hint); e.setTextSize(14); e.setTextColor(INK); return e;
    }
    private void buildScreen() {
        root = column(); root.setPadding(dp(20),dp(12),dp(20),0); root.setBackgroundColor(Color.rgb(244,243,238));
        if(Build.VERSION.SDK_INT>=30) root.setOnApplyWindowInsetsListener((v,insets)->{
            android.graphics.Insets bars=insets.getInsets(WindowInsets.Type.systemBars());
            v.setPadding(dp(20),dp(12)+bars.top,dp(20),bars.bottom);return insets;
        });
        setContentView(root);
        LinearLayout head=new LinearLayout(this); head.setGravity(Gravity.CENTER_VERTICAL);
        TextView brand=label("◉ 빛의 기록",24,INK); brand.setTypeface(null,Typeface.BOLD);
        head.addView(brand,new LinearLayout.LayoutParams(0,-2,1)); head.addView(button("설정",this::settings));root.addView(head);
        TextView eyebrow=label("PHOTO JOURNAL / 일상의 조각",10,GREEN); eyebrow.setPadding(0,dp(16),0,dp(8));root.addView(eyebrow);
        root.addView(label("순간을 담고,\n이야기를 나누세요.",30,INK));
        status=label("서버 연결 대기 · 동기화를 눌러 시작하세요",12,GREEN);status.setPadding(0,dp(12),0,dp(8));root.addView(status);
        LinearLayout actions=new LinearLayout(this);
        sync=button("↻ 동기화",()->onClickDownload(null)); upload=button("＋ 사진 올리기",()->onClickUpload(null));
        actions.addView(sync,new LinearLayout.LayoutParams(0,-2,1));actions.addView(upload,new LinearLayout.LayoutParams(0,-2,1));root.addView(actions);
        LinearLayout filters=new LinearLayout(this);search=field("사진 검색");search.setSingleLine(true);filters.addView(search,new LinearLayout.LayoutParams(0,-2,1));
        filters.addView(button("검색",()->{try{load(base+postEndpoint()+"?search="+URLEncoder.encode(search.getText().toString(),"UTF-8"),false);}catch(Exception e){error(e);}}));
        filters.addView(button("☆",()->{favoriteOnly=!favoriteOnly;render();status.setText(favoriteOnly?"즐겨찾기만 표시 중 (현재 페이지)":"전체 사진 표시 중");}));root.addView(filters);
        counter=label("나의 포토 컬렉션",12,GREEN);counter.setPadding(0,dp(10),0,dp(10));root.addView(counter);
        cards=new RecyclerView(this);cards.setLayoutManager(new LinearLayoutManager(this));root.addView(cards,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout pager=new LinearLayout(this);previous=button("← 이전",()->load(previousUrl,false));next=button("다음 →",()->load(nextUrl,false));
        previous.setEnabled(false);next.setEnabled(false);pager.addView(previous,new LinearLayout.LayoutParams(0,-2,1));pager.addView(next,new LinearLayout.LayoutParams(0,-2,1));root.addView(pager);
        render();
    }
    private void busy(boolean value) { loading=value;sync.setEnabled(!value);upload.setEnabled(!value);previous.setEnabled(!value&&previousUrl!=null);next.setEnabled(!value&&nextUrl!=null); }
    private void load(String url, boolean afterUpload) {
        if(url==null||loading)return;
        busy(true); status.setText("서버에서 사진을 동기화하는 중…");
        worker.execute(()->{try{
            String raw=request("GET",url,null,null,!token.isEmpty());
            JSONObject data;
            if(raw.trim().startsWith("[")) {
                JSONArray array=new JSONArray(raw);data=new JSONObject();data.put("results",array);data.put("count",array.length());data.put("next",JSONObject.NULL);data.put("previous",JSONObject.NULL);
                for(int i=0;i<array.length();i++){JSONObject item=array.getJSONObject(i);item.put("author",item.optString("author_name",item.optString("author")));item.put("created_at",item.optString("created_date"));}
            } else data=new JSONObject(raw);
            JSONArray results=data.getJSONArray("results");
            ui.post(()->{if(isDestroyed())return;try{
                posts.clear();for(int i=0;i<results.length();i++)posts.add(results.getJSONObject(i));
                nextUrl=data.isNull("next")?null:data.getString("next");previousUrl=data.isNull("previous")?null:data.getString("previous");
                prefs.edit().putString("cache",results.toString()).apply();busy(false);render();
                counter.setText(getString(R.string.collection_count,data.getInt("count"),posts.size()));
                status.setText(getString(afterUpload?R.string.upload_done:R.string.sync_done,posts.size()));
            }catch(Exception e){busy(false);error(e);}});
        }catch(Exception e){ui.post(()->{busy(false);error(e);});}});
    }
    private String postKey(JSONObject post) { return post.has("id")?post.optString("id"):post.optString("image"); }
    private String postEndpoint() { return lectureMode?"/api_root/Post/":"/api/posts/"; }
    // Chapter 5 p.19 event handlers; ExecutorService replaces deprecated AsyncTask.
    public void onClickDownload(View view) { load(base+postEndpoint(),false); }
    public void onClickUpload(View view) { openEditor(null); }
    private void render() {
        ++generation;List<JSONObject> displayed=new ArrayList<>();
        for(JSONObject post:posts) if(!favoriteOnly||favorites.contains(postKey(post))) displayed.add(post);
        if(displayed.isEmpty()) displayed.add(null);
        cards.setAdapter(new ImageAdapter(displayed,this::createCard));
    }
    private View createCard(JSONObject post) {
        if(post==null){TextView empty=label(favoriteOnly?"☆ 저장한 사진이 없습니다.":"아직 불러온 사진이 없습니다.\n동기화로 일상의 기록을 만나보세요.",16,GREEN);empty.setPadding(dp(10),dp(35),0,dp(35));return empty;}
        long current=generation;String id=postKey(post);
            LinearLayout card=column();card.setPadding(dp(12),dp(12),dp(12),dp(12));card.setBackgroundColor(Color.WHITE);
            ImageView image=new ImageView(this);image.setContentDescription(post.optString("title"));image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            card.addView(image,new LinearLayout.LayoutParams(-1,dp(200)));
            worker.execute(()->{try{Bitmap bitmap=downloadImage(post.getString("image"));ui.post(()->{if(!isDestroyed()&&generation==current)image.setImageBitmap(bitmap);});}
                catch(Exception e){ui.post(()->{if(generation==current)image.setContentDescription("사진 연결 실패: "+post.optString("title"));});}});
            TextView title=label(post.optString("title"),20,INK);title.setPadding(0,dp(10),0,dp(5));card.addView(title);
            card.addView(label(post.optString("author")+" · "+post.optString("created_at").split("T")[0],11,GREEN));
            TextView text=label(post.optString("text"),14,INK);text.setPadding(0,dp(8),0,dp(8));card.addView(text);
            LinearLayout tools=new LinearLayout(this);Button star=button(favorites.contains(id)?"★ 저장됨":"☆ 저장",()->{
                if(!favorites.add(id))favorites.remove(id);prefs.edit().putStringSet("favorites",new HashSet<>(favorites)).apply();render();});tools.addView(star);
            if(!token.isEmpty()&&username.equals(post.optString("author"))){tools.addView(button("수정",()->openEditor(post)));tools.addView(button("삭제",()->confirmDelete(post)));}card.addView(tools);
        return card;
    }
    private void settings() {
        LinearLayout form=column();form.setPadding(dp(20),dp(10),dp(20),0);
        form.addView(label("에뮬레이터: http://10.0.2.2:8000\n실기기: adb reverse 후 http://127.0.0.1:8000\n클라우드: https://사용자명.pythonanywhere.com",12,GREEN));
        EditText server=field("서버 주소");server.setText(base);server.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);form.addView(server);
        CheckBox contract=new CheckBox(this);contract.setText("강의 API 사용 (JSON Array)");contract.setChecked(lectureMode);form.addView(contract);
        EditText user=field("사용자명");user.setSingleLine();user.setText(username);form.addView(user);
        EditText password=field("비밀번호 (로그인 시 입력)");password.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);form.addView(password);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("서버 / 로그인").setView(form).setNegativeButton("취소",null).setNeutralButton("주소 저장",null).setPositiveButton("로그인",null).create();
        dialog.setOnShowListener(d->{
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->{try{saveServer(server.getText().toString());lectureMode=contract.isChecked();prefs.edit().putBoolean("lecture",lectureMode).apply();dialog.dismiss();status.setText("서버 주소 저장 완료 · 동기화하세요");}catch(Exception e){error(e);}});
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{try{
                saveServer(server.getText().toString());lectureMode=contract.isChecked();prefs.edit().putBoolean("lecture",lectureMode).apply();String name=user.getText().toString().trim();String secret=password.getText().toString();
                if(name.isEmpty()||secret.isEmpty())throw new IOException("사용자명과 비밀번호를 입력하세요.");
                JSONObject body=new JSONObject();body.put("username",name);body.put("password",secret);dialog.getButton(-1).setEnabled(false);
                worker.execute(()->{try{JSONObject data=new JSONObject(request("POST",base+"/api/token/",body.toString().getBytes(StandardCharsets.UTF_8),"application/json",false));
                    ui.post(()->{token=data.optString("token");username=name;prefs.edit().putString("token",token).putString("username",username).apply();dialog.dismiss();render();status.setText(getString(R.string.login_done,name));});
                }catch(Exception e){ui.post(()->{dialog.getButton(-1).setEnabled(true);error(e);});}});
            }catch(Exception e){error(e);}});
        });dialog.show();
    }
    private void saveServer(String value) throws Exception {
        String cleaned=value.trim().replaceAll("/+$", "");URI uri=new URI(cleaned);
        if(uri.getHost()==null||uri.getUserInfo()!=null||uri.getQuery()!=null||uri.getFragment()!=null||(!"".equals(uri.getPath()))||!("http".equals(uri.getScheme())||"https".equals(uri.getScheme())))throw new IOException("http(s)://호스트:포트 형식으로 입력하세요.");
        if(!cleaned.equals(base)){token="";username="";posts.clear();nextUrl=null;previousUrl=null;prefs.edit().remove("token").remove("username").remove("cache").apply();render();}
        base=cleaned;prefs.edit().putString("server",base).apply();
    }
    private void saveDraft(){if(titleInput!=null&&editor!=null&&editor.isShowing()){draftTitle=titleInput.getText().toString();draftText=textInput.getText().toString();}}
    private void openEditor(JSONObject post){
        if(token.isEmpty()){status.setText("사진을 올리려면 설정에서 먼저 로그인하세요.");settings();return;}
        boolean edit=post!=null;LinearLayout form=column();form.setPadding(dp(20),dp(8),dp(20),0);
        titleInput=field("제목 (필수, 최대 100자)");titleInput.setText(edit?post.optString("title"):draftTitle);form.addView(titleInput);
        textInput=field("이야기 (최대 2,000자)");textInput.setMinLines(2);textInput.setText(edit?post.optString("text"):draftText);form.addView(textInput);
        if(!edit){choose=button(selectedImage==null?"사진 선택 (JPEG / PNG / WEBP)":"사진 선택 완료 ✓",()->{
            saveDraft();Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT);pick.setType("image/*");pick.addCategory(Intent.CATEGORY_OPENABLE);pick.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);startActivityForResult(pick,42);
        });form.addView(choose);form.addView(label("사진 10MB 이하 · 사진과 제목을 입력해 업로드",12,GREEN));}
        editor=new AlertDialog.Builder(this).setTitle(edit?"기록 수정":"새로운 순간 올리기").setView(form).setNegativeButton("취소",(d,w)->{if(!edit)saveDraft();}).setPositiveButton(edit?"저장":"업로드",null).create();
        editor.setOnShowListener(d->editor.getButton(-1).setOnClickListener(v->{
            String title=titleInput.getText().toString().trim(),text=textInput.getText().toString();
            if(title.isEmpty()||title.length()>100||text.length()>2000){titleInput.setError("제목 1~100자, 이야기 2,000자 이하로 입력하세요.");return;}
            if(!edit&&selectedImage==null){Toast.makeText(this,"사진을 먼저 선택하세요.",Toast.LENGTH_SHORT).show();return;}
            Uri image=selectedImage;editor.getButton(-1).setEnabled(false);status.setText(edit?"수정 중…":"사진 업로드 중…");
            worker.execute(()->{try{
                if(edit){JSONObject body=new JSONObject();body.put("title",title);body.put("text",text);request("PATCH",base+postEndpoint()+post.optInt("id")+"/",body.toString().getBytes(StandardCharsets.UTF_8),"application/json",true);}
                else uploadPost(title,text,image);
                ui.post(()->{editor.dismiss();if(!edit){selectedImage=null;draftTitle="";draftText="";}load(base+postEndpoint(),true);});
            }catch(Exception e){ui.post(()->{editor.getButton(-1).setEnabled(true);error(e);});}});
        }));editor.show();
    }
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request==42&&result==RESULT_OK&&data!=null){selectedImage=data.getData();if(selectedImage!=null){try{getContentResolver().takePersistableUriPermission(selectedImage,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}if(choose!=null)choose.setText("사진 선택 완료 ✓");}}}
    /** Evaluation #8: user-entered Post fields + selected image -> multipart POST. */
    private void uploadPost(String title,String text,Uri image) throws Exception {
        byte[] bytes;try(InputStream in=getContentResolver().openInputStream(image);ByteArrayOutputStream out=new ByteArrayOutputStream()){
            if(in==null)throw new IOException("사진을 열 수 없습니다.");byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1){out.write(buffer,0,n);if(out.size()>10*1024*1024)throw new IOException("사진은 10MB 이하여야 합니다.");}bytes=out.toByteArray();}
        String mime=getContentResolver().getType(image);String extension="image/png".equals(mime)?"png":"image/webp".equals(mime)?"webp":"jpg";
        String boundary="PhotoBlog"+UUID.randomUUID();ByteArrayOutputStream payload=new ByteArrayOutputStream();
        write(payload,"--"+boundary+"\r\nContent-Disposition: form-data; name=\"title\"\r\n\r\n"+title+"\r\n");
        write(payload,"--"+boundary+"\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\n"+text+"\r\n");
        write(payload,"--"+boundary+"\r\nContent-Disposition: form-data; name=\"image\"; filename=\"photo."+extension+"\"\r\nContent-Type: "+(mime==null?"application/octet-stream":mime)+"\r\n\r\n");
        payload.write(bytes);write(payload,"\r\n--"+boundary+"--\r\n");request("POST",base+postEndpoint(),payload.toByteArray(),"multipart/form-data; boundary="+boundary,true);
    }
    private void write(OutputStream out,String value)throws IOException{out.write(value.getBytes(StandardCharsets.UTF_8));}
    private void confirmDelete(JSONObject post){new AlertDialog.Builder(this).setTitle("이 사진을 삭제할까요?").setMessage(post.optString("title")).setNegativeButton("취소",null).setPositiveButton("삭제",(d,w)->worker.execute(()->{try{request("DELETE",base+postEndpoint()+post.optInt("id")+"/",null,null,true);ui.post(()->load(base+postEndpoint(),false));}catch(Exception e){ui.post(()->error(e));}})).show();}
    private HttpURLConnection connection(String url) throws Exception {
        URL address=new URL(url), origin=new URL(base);
        if(!address.getProtocol().equals(origin.getProtocol())||!address.getHost().equals(origin.getHost())||address.getPort()!=origin.getPort())throw new IOException("서버와 다른 출처의 URL입니다.");
        HttpURLConnection c=(HttpURLConnection)address.openConnection();c.setConnectTimeout(10000);c.setReadTimeout(20000);c.setInstanceFollowRedirects(false);return c;
    }
    private String request(String method,String url,byte[] body,String type,boolean authenticated)throws Exception{
        HttpURLConnection c=connection(url);try{c.setRequestMethod(method);c.setRequestProperty("Accept","application/json");if(authenticated)c.setRequestProperty("Authorization","Token "+token);
            if(body!=null){c.setDoOutput(true);c.setRequestProperty("Content-Type",type);c.setFixedLengthStreamingMode(body.length);try(OutputStream out=c.getOutputStream()){out.write(body);}}
            int code=c.getResponseCode();InputStream stream=code>=400?c.getErrorStream():c.getInputStream();String result="";if(stream!=null)try(InputStream in=stream;ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);result=out.toString("UTF-8");}
            if(code<200||code>=300)throw new IOException("HTTP "+code+" · "+result.substring(0,Math.min(220,result.length())));return result;
        }finally{c.disconnect();}
    }
    private Bitmap downloadImage(String url)throws Exception{
        HttpURLConnection c=connection(url);try{if(c.getResponseCode()!=200)throw new IOException("이미지 응답 오류");byte[] bytes;try(InputStream in=c.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] buf=new byte[8192];int n;while((n=in.read(buf))!=-1){out.write(buf,0,n);if(out.size()>12*1024*1024)throw new IOException("이미지가 너무 큽니다.");}bytes=out.toByteArray();}
            BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);options.inSampleSize=1;while(Math.max(options.outWidth,options.outHeight)/options.inSampleSize>1200)options.inSampleSize*=2;options.inJustDecodeBounds=false;return BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);
        }finally{c.disconnect();}
    }
    private void error(Exception e){if(isDestroyed())return;status.setText(getString(R.string.error_message,e.getMessage()));Toast.makeText(this,e.getMessage(),Toast.LENGTH_LONG).show();}
    @Override protected void onDestroy(){worker.shutdownNow();super.onDestroy();}
}
