#!/usr/bin/env python3
"""RoomFit 3.9.2: directly reuse the exact original AR intent and model API.

Original code provenance: user-uploaded RoomFit-Android-Source (1).zip,
MainActivity.launchAR + furniture-3d.js nativeFurnitureARLink.
No custom ARCore renderer and no copied signing secrets.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]); main=root/'app/src/main/java/kr/ac/roomfit/app/MainActivity.java'
s=main.read_text(encoding='utf-8')
assert 'private static final String ORIGIN = "https://roomfit-lifestyle-sanghyun.glossy-otter-9481.chatgpt.site";' in s
assert 'private void launchAR(String uri)' in s
old='''        @JavascriptInterface public void openLockedAR(final String scene){if(scene==null||scene.length()>32000)return;runOnUiThread(()->{try{new org.json.JSONObject(scene);launchNativeFloorAR(scene);}catch(Exception ex){toast("배치 화면을 열지 못했어요.");}});}'''
assert old in s, 'Native bridge entry changed'
new='''        @JavascriptInterface public void openLockedAR(final String scene){
            if(scene==null||scene.length()>32000)return;
            runOnUiThread(()->launchUploadedOriginalAR(scene));
        }'''
s=s.replace(old,new,1)
marker='    private void launchNativeFloorAR(String scene){'
assert marker in s
launcher='''    /** Reuses the user's original, working WebView -> Google Scene Viewer intent
     * path and the exact /api/furniture-model/{kind}.glb service. No ARCore
     * rendering, camera-relative anchors, or replacement Google GLB URL.
     * This requires the user's original remote service to remain accessible.
     */
    private void launchUploadedOriginalAR(String scene){
        try {
            org.json.JSONArray arr=new org.json.JSONObject(scene).getJSONArray("items");
            if(arr.length()==0){toast("선택한 가구가 없습니다.");return;}
            if(arr.length()==1){launchOneOriginalModel(arr.getJSONObject(0));return;}
            final String[] names=new String[arr.length()];
            for(int i=0;i<arr.length();i++)names[i]=arr.getJSONObject(i).optString("name","가구 "+(i+1));
            new AlertDialog.Builder(this).setTitle("AR로 볼 가구 선택 · 한 번에 한 개")
                .setItems(names,(dialog,i)->{
                    try{launchOneOriginalModel(arr.getJSONObject(i));}
                    catch(Exception e){toast("가구 모델을 준비하지 못했어요.");}
                }).setNegativeButton("취소",null).show();
        }catch(Exception e){toast("원본 AR 실행 오류: "+e.getClass().getSimpleName());}
    }
    private void launchOneOriginalModel(org.json.JSONObject item){
        String kind=item.optString("kind","box").toLowerCase(java.util.Locale.US);
        // The original service generates simple size-reference models in these 8 types.
        if(!java.util.Arrays.asList("desk","chair","bed","storage","table","lamp","rug","box").contains(kind)){
            new AlertDialog.Builder(this).setTitle("원본 AR 모델 형식")
                .setMessage("원본 AR 서버에서는 이 종류의 전용 모형이 없어 기본 상자 모형으로 크기를 표시합니다.")
                .setPositiveButton("계속",(d,w)->launchOriginalKind(item,"box"))
                .setNegativeButton("취소",null).show();
            return;
        }
        launchOriginalKind(item,kind);
    }
    private void launchOriginalKind(org.json.JSONObject item,String kind){
        try {
            double w=item.getDouble("width"),d=item.getDouble("depth"),h=item.getDouble("height");
            if(!Double.isFinite(w)||!Double.isFinite(d)||!Double.isFinite(h)||w<1||d<1||h<1||w>600||d>600||h>600){toast("가구 크기 정보가 올바르지 않습니다.");return;}
            String title=item.optString("name","룸핏 가구");
            // This is the ORIGINAL application's API shape, not a GitHub raw GLB.
            String model=new Uri.Builder().scheme("https").authority(HOST)
                .path("/api/furniture-model/"+kind+".glb")
                .appendQueryParameter("w",String.valueOf(w))
                .appendQueryParameter("d",String.valueOf(d))
                .appendQueryParameter("h",String.valueOf(h))
                .appendQueryParameter("tone","wood").build().toString();
            // Exact original JS intent shape from furniture-3d.js.
            String intent="intent://arvr.google.com/scene-viewer/1.0?file="+Uri.encode(model)+
                "&mode=ar_preferred&resizable=false#Intent;scheme=https;"+
                "package=com.google.android.googlequicksearchbox;"+
                "action=android.intent.action.VIEW;end;";
            launchAR(intent);
        }catch(Exception e){toast("원본 AR 모델 연결 실패: "+e.getClass().getSimpleName());}
    }
'''
s=s.replace(marker,launcher+marker,1)
s=s.replace('RoomFitAndroid/3.9.1','RoomFitAndroid/3.9.2')
main.write_text(s,encoding='utf-8')

# The existing wizard already opens RoomfitNative.openLockedAR() on step 4 -> 5.
# Replace misleading experimental instructions; leave the actual 5 stages intact.
web=root/'app/src/main/assets/web'
js=web/'roomfit3.js';t=js.read_text(encoding='utf-8')
t=t.replace('AR 화면에서 바닥을 터치해 가구를 놓으세요. 바닥이 검출되지 않으면 특징점 배치를 시도합니다. 크기는 참고용입니다.',
            '업로드해 주신 원본 방식의 Google AR 뷰어를 실행합니다. 바닥 인식 후 놓아주세요. 가구 크기는 참고용입니다.')
js.write_text(t,encoding='utf-8')
html=web/'roomfit3.html';u=html.read_text(encoding='utf-8')
u=u.replace('룸핏 3.9 |','룸핏 3.9.2 |')
u=u.replace('앱 내부에서 바닥 고정하기 (Google AR이 열리지 않을 때)', '앱 내부 AR 시험판 (원본 AR이 열리지 않을 때)')
html.write_text(u,encoding='utf-8')

build=root/'app/build.gradle';b=build.read_text(encoding='utf-8')
b=re.sub(r'\bversionCode\s+\d+','versionCode 392',b)
b=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]","versionName '3.9.2'",b)
build.write_text(b,encoding='utf-8')
manifest=root/'app/src/main/AndroidManifest.xml';m=manifest.read_text(encoding='utf-8')
m=re.sub(r'android:versionCode="\d+"','android:versionCode="392"',m)
m=re.sub(r'android:versionName="[^"]+"','android:versionName="3.9.2"',m)
manifest.write_text(m,encoding='utf-8')
assert 'launchUploadedOriginalAR(scene)' in s and 'arvr.google.com/scene-viewer/1.0?file=' in s
print('Original AR launch path reused. Original remote GLB service required.')