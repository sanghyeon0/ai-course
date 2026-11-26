from pathlib import Path
import sys,shutil,json
root=Path(sys.argv[1]); page=Path(sys.argv[2]); out=Path(sys.argv[3]); web=root/'app/src/main/assets/web'
def replace(s,a,b):
 assert a in s,a[:100];return s.replace(a,b,1)
def edit(p,fn):
 s=p.read_text(encoding='utf-8');p.write_text(fn(s),encoding='utf-8')
def main(s):
 s=s.replace('RoomFitAndroid/3.9.7','RoomFitAndroid/4.0.0').replace('&v=397','&v=400').replace('AR 직접 실행 · 3.9.7','AR 직접 실행 · 4.0')
 s=replace(s,'    private void showDirectARMenu(){','''    private static final String WEBXR_DEFAULT="https://sanghyeon0.github.io/ai-course/roomfit-webxr/";
    private String webXRUrl(){return getSharedPreferences("roomfit-webxr",0).getString("url",WEBXR_DEFAULT);}
    private void configureWebXR(){
        android.widget.EditText input=new android.widget.EditText(this);
        input.setSingleLine(true);input.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_URI);input.setText(webXRUrl());
        new AlertDialog.Builder(this).setTitle("WebXR HTTPS 주소").setMessage("배포한 룸핏 WebXR 페이지 주소를 입력하세요. 기본 주소는 GitHub Pages 배포 후 작동합니다.")
            .setView(input).setPositiveButton("저장",(d,w)->{String val=input.getText().toString().trim();Uri u=Uri.parse(val);if(!"https".equals(u.getScheme())||u.getHost()==null||u.getUserInfo()!=null||u.getFragment()!=null){toast("HTTPS 주소만 입력하세요.");return;}getSharedPreferences("roomfit-webxr",0).edit().putString("url",val).apply();toast("WebXR 주소 저장 완료");}).setNeutralButton("기본값",(d,w)->getSharedPreferences("roomfit-webxr",0).edit().remove("url").apply()).setNegativeButton("취소",null).show();
    }
    private void launchWebXR(String raw){
        try{
            org.json.JSONArray arr=new org.json.JSONArray(raw);if(arr.length()>5)throw new IllegalArgumentException();
            java.util.ArrayList<String> ids=new java.util.ArrayList<>();for(int i=0;i<arr.length();i++){String id=arr.getString(i);if(!id.matches("[a-z0-9-]{1,80}"))throw new IllegalArgumentException();ids.add(id);}
            Uri url=Uri.parse(webXRUrl()).buildUpon().fragment("items="+android.text.TextUtils.join(",",ids)).build();
            if(!"https".equals(url.getScheme())||url.getHost()==null)throw new IllegalArgumentException();
            startActivity(new Intent(Intent.ACTION_VIEW,url).setPackage("com.android.chrome"));reportAR("Chrome WebXR 페이지를 열었습니다. 브라우저에서 AR 시작을 누르세요.");
        }catch(ActivityNotFoundException ex){new AlertDialog.Builder(this).setTitle("Chrome이 필요합니다").setMessage("Chrome을 설치한 후 다시 시도하세요.").setPositiveButton("설치",(d,w)->external(Uri.parse("https://play.google.com/store/apps/details?id=com.android.chrome"))).setNegativeButton("닫기",null).show();}
        catch(Exception ex){reportAR("WebXR 연결 실패: "+ex.getClass().getSimpleName());toast("WebXR 주소 또는 선택 가구를 확인하세요.");}
    }
    private void readWebXRSelection(){
        web.evaluateJavascript("typeof window.roomfitWebXRSelection==='function'?JSON.stringify(window.roomfitWebXRSelection()):null",value->{try{Object result=new org.json.JSONTokener(value).nextValue();if(!(result instanceof String)||new org.json.JSONArray((String)result).length()==0){toast("3단계에서 가구를 선택하세요.");return;}launchWebXR((String)result);}catch(Exception ex){toast("가구 선택 정보를 읽지 못했습니다.");}});
    }
    private void showDirectARMenu(){''')
 s=replace(s,'''            .setItems(new String[]{"선택한 가구 Google AR 실행","Google 공식 호랑이 모델 테스트","선택한 가구 앱 내 AR 실행","Google Play AR 서비스 확인"},(dlg,i)->{
                if(i==0)readSelectedScene(false);
                else if(i==1)openGoogleViewer(SAMPLE_MODEL,"Google 공식 테스트 모형");
                else if(i==2)readSelectedScene(true);
                else external(Uri.parse("https://play.google.com/store/apps/details?id=com.google.ar.core"));''','''            .setItems(new String[]{"선택한 가구 Chrome WebXR","Chrome WebXR 샘플 테스트","선택한 가구 앱 내 AR 실행","WebXR 주소 설정","Google Play AR 서비스 확인"},(dlg,i)->{
                if(i==0)readWebXRSelection();
                else if(i==1)launchWebXR("[]");
                else if(i==2)readSelectedScene(true);
                else if(i==3)configureWebXR();
                else external(Uri.parse("https://play.google.com/store/apps/details?id=com.google.ar.core"));''')
 return replace(s,'        @JavascriptInterface public void openLockedAR(final String scene){','''        @JavascriptInterface public void openWebXR(final String ids){if(ids==null||ids.length()>1024)return;runOnUiThread(()->launchWebXR(ids));}
        @JavascriptInterface public void openLockedAR(final String scene){''')
edit(root/'app/src/main/java/kr/ac/roomfit/app/MainActivity.java',main)
def js(s):
 s=s.replace('RoomFit 3.9.5','RoomFit 4.0')
 s=replace(s,'window.roomfitOpenAR=()=>ar(true);','''window.roomfitWebXRSelection=()=>selected.map(m=>m.asset).filter(x=>typeof x==='string'&&/^[a-z0-9-]{1,80}$/.test(x)).slice(0,5);
function webxr(){const ids=window.roomfitWebXRSelection();if(!ids.length){alert('가구를 먼저 선택해주세요.');return;}if(!window.RoomfitNative?.openWebXR){$('ar-guide').textContent='설치된 룸핏 4.0 앱에서 실행하세요.';return;}$('ar-guide').textContent='Chrome WebXR 연결 중…';window.RoomfitNative.openWebXR(JSON.stringify(ids));}
window.roomfitOpenAR=webxr;''')
 return replace(s,"$('open-ar').addEventListener('click',()=>ar(true));$('open-native-floor-ar').addEventListener('click',()=>ar(false));","$('open-ar').addEventListener('click',webxr);$('open-native-floor-ar').addEventListener('click',()=>ar(true));")
edit(web/'roomfit3.js',js)
edit(web/'roomfit34-ui.js',lambda s:s.replace('ROOMFIT 3.9.5','ROOMFIT 4.0').replace('룸핏 내부 AR 실행을 누르세요. 가구 미리보기와 실제 공간 고정을 구분합니다.','Chrome WebXR 실행 후 브라우저에서 AR 시작을 누르세요. 앱 내 AR은 대체 기능입니다.'))
edit(web/'roomfit3.html',lambda s:s.replace('룸핏 3.9.1 |','룸핏 4.0 |').replace('05 / BASIC AR','05 / CHROME WEBXR').replace('가구 기본 모형을 화면에 표시하고, 바닥 또는 특징점을 인식하면 공간에 고정합니다. 화면 미리보기는 실제 배치가 아닙니다.','Chrome에서 WebXR로 가구를 배치합니다. HTTPS 페이지 및 Google Play AR 서비스가 필요합니다.').replace('>룸핏 내부 AR 실행</button>','>Chrome WebXR 실행</button>').replace('>Google AR (선택 테스트)</button>','>룸핏 내부 AR (대체)</button>'))
edit(root/'app/build.gradle',lambda s:replace(replace(s,'versionCode 397','versionCode 400'),"versionName '3.9.7'","versionName '4.0.0'"))
edit(root/'app/src/main/AndroidManifest.xml',lambda s:replace(replace(replace(s,'android:versionCode="397"','android:versionCode="400"'),'android:versionName="3.9.7"','android:versionName="4.0.0"'),'<queries>','<queries>\n        <package android:name="com.android.chrome"/>'))
edit(root/'app/src/main/java/kr/ac/roomfit/app/SimpleFurnitureArActivity.java',lambda s:s.replace('룸핏 3.9.7 · 내부 가구 AR','룸핏 4.0 · 내부 가구 AR'))
out.mkdir(parents=True,exist_ok=True);shutil.copyfile(page,out/'index.html');shutil.copyfile(web/'product-models.json',out/'catalog.json');shutil.copytree(web/'product-models',out/'models',dirs_exist_ok=True)
models=json.loads((out/'catalog.json').read_text());missing=[m['asset'] for m in models.values() if not (out/'models'/f"{m['asset']}.glb").exists()];assert not missing,missing
print('RoomFit 4.0 Chrome WebXR,',len(models),'catalog entries verified')
