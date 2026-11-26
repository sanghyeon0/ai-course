from pathlib import Path
import sys,hashlib
root=Path(sys.argv[1])
def sub(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b,1)
def edit(path,fn,digest):
 p=root/path
 s=fn(p.read_text(encoding='utf-8'))
 p.write_text(s,encoding='utf-8')
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Uploaded source mismatch: '+path
def main(s):
 s=s.replace('RoomFitAndroid/3.9.5','RoomFitAndroid/3.9.6').replace('&v=395','&v=396').replace('AR 직접 실행 · 3.9.5','AR 직접 실행 · 3.9.6')
 s=sub(s,'''            intent.setComponent(null);intent.setSelector(null);intent.addCategory(Intent.CATEGORY_BROWSABLE);
            intent.removeExtra("browser_fallback_url");
            startActivity(intent);''','''            // 웹에서 온 intent://도 검증한 모델 주소만 뽑아 공통 실행 경로로 보낸다.
            openGoogleViewer(file,data.getQueryParameter("title"));''')
 s=s.replace('openGoogleViewer("https://storage.googleapis.com/ar-answers-in-search-models/static/Tiger/model.glb","Google 공식 테스트 모형")','openGoogleViewer(SAMPLE_MODEL,"Google 공식 테스트 모형")')
 a=s.index('    private void openGoogleViewer(String model,String title){')
 b=s.index('    private void reportAR(',a)
 s=s[:a]+'''    static final String GOOGLE_APP="com.google.android.googlequicksearchbox";
    static final String AR_SERVICES="com.google.ar.core";
    static final String SAMPLE_MODEL="https://storage.googleapis.com/ar-answers-in-search-models/static/Tiger/model.glb";

    /**
     * 3.9.6: Google AR(Scene Viewer) 실행 경로를 하나로 통일.
     * Google 공식 문서의 명시적 인텐트 형태 그대로 보낸다.
     *  1) Google 앱 + mode=ar_preferred (예전에 작동하던 경로, AR 불가 기기는 3D로 표시)
     *  2) Google Play AR 서비스 + mode=ar_only
     * 3.9.5까지는 AR 서비스를 먼저 부르면서 CATEGORY_BROWSABLE을 붙였다. 이 카테고리를
     * 선언하지 않은 화면은 인텐트가 매칭되지 않아 실행이 실패하므로 붙이지 않는다.
     * @return 실행 요청이 어느 한 앱에라도 전달되면 true
     */
    private boolean startSceneViewer(String model,String title){
        String t=(title==null||title.isEmpty())?"RoomFit":title.substring(0,Math.min(60,title.length()));
        String[][] routes={{GOOGLE_APP,"ar_preferred"},{AR_SERVICES,"ar_only"}};
        for(String[] route:routes){
            Uri viewer=new Uri.Builder().scheme("https").authority("arvr.google.com").path("/scene-viewer/1.0")
                .appendQueryParameter("file",model).appendQueryParameter("mode",route[1])
                .appendQueryParameter("resizable","false").appendQueryParameter("title",t).build();
            Intent intent=new Intent(Intent.ACTION_VIEW,viewer).setPackage(route[0]);
            try{
                startActivity(intent);
                reportAR((GOOGLE_APP.equals(route[0])?"Google 앱":"Google Play AR 서비스")+" 실행 요청 완료 · 모델 표시 여부를 확인하세요.");
                return true;
            }catch(ActivityNotFoundException|SecurityException ex){
                android.util.Log.w("RoomFitAR",route[0]+" 로 Scene Viewer 실행 불가",ex);
            }
        }
        reportAR("Google AR 실행 실패: Google 앱과 AR 서비스 모두 실행 요청을 받지 못했습니다.");
        return false;
    }
    private void openGoogleViewer(String model,String title){
        if(startSceneViewer(model,title))return;
        new AlertDialog.Builder(this).setTitle("Google AR 실행 실패")
            .setMessage("Google 앱과 Google Play AR 서비스가 실행 요청을 처리하지 못했습니다. 두 앱의 설치·업데이트 상태를 확인하세요.\\n\\n지금은 앱 내 AR(오른쪽 위 'AR 직접 실행' → '선택한 가구 앱 내 AR 실행')로 확인할 수 있습니다.")
            .setPositiveButton("AR 서비스 확인",(dlg,which)->external(Uri.parse("https://play.google.com/store/apps/details?id="+AR_SERVICES)))
            .setNeutralButton("Google 앱 확인",(dlg,which)->external(Uri.parse("https://play.google.com/store/apps/details?id="+GOOGLE_APP)))
            .setNegativeButton("닫기",null).show();
    }
'''+s[b:]
 a=s.index('            runOnUiThread(()->{',s.index('final Uri file=Uri.parse(model);'))
 b=s.index('        /** Google documentation sample',a)
 s=s[:a]+'''            runOnUiThread(()->openGoogleViewer(model,title));
        }
'''+s[b:]
 a=s.index('        @JavascriptInterface public void testSampleAR()')
 b=s.index('        @JavascriptInterface public void checkModelConnection',a)
 s=s[:a]+'''        @JavascriptInterface public void testSampleAR(){runOnUiThread(()->openGoogleViewer(SAMPLE_MODEL,"RoomFit AR sample test"));}
'''+s[b:]
 s=sub(s,'        private boolean installed(String name)', '''        private String appVersion(){try{return getPackageManager().getPackageInfo(getPackageName(),0).versionName;}catch(Exception ex){return "?";}}
        private boolean installed(String name)''')
 s=sub(s,'.setTitle("AR 연결 확인 · 앱 1.7.2")','.setTitle("AR 연결 확인 · 앱 "+appVersion())')
 return s
edit('app/src/main/java/kr/ac/roomfit/app/MainActivity.java',main,'320865a20eaf874699013d3bf1bd32927d576b9453c3b59c52567c5d87ff4063')
edit('app/src/main/java/kr/ac/roomfit/app/SimpleFurnitureArActivity.java',lambda s:sub(s,'룸핏 3.9.5 · 내부 가구 AR','룸핏 3.9.6 · 내부 가구 AR'),'6ecc73aff823e83af9bbcf1c44efa013f43bdb226428e4e8dae7bb8081e8429a')
edit('app/build.gradle',lambda s:sub(sub(s,'versionCode 395','versionCode 396'),"versionName '3.9.5'","versionName '3.9.6'"),'b7c7dfcc28bf41a1d5bd9b80530b04fd5d05e3263bee26ab94ed10d654dfb8c6')
edit('app/src/main/AndroidManifest.xml',lambda s:sub(sub(s,'android:versionCode="395"','android:versionCode="396"'),'android:versionName="3.9.5"','android:versionName="3.9.6"'),'bd68217ea9420cd2f1efa88e8a2b78b6f2a664198622d12506d51c0c31fc3543')
print('All four modified files match uploaded RoomFit 3.9.6 byte-for-byte')
