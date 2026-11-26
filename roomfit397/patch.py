from pathlib import Path
import sys,hashlib
root=Path(sys.argv[1])
def sub(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b,1)
def edit(path,fn,digest):
 p=root/path
 p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Uploaded source mismatch: '+path
def main(s):
 s=s.replace('RoomFitAndroid/3.9.6','RoomFitAndroid/3.9.7').replace('&v=396','&v=397').replace('AR 직접 실행 · 3.9.6','AR 직접 실행 · 3.9.7')
 s=sub(s,'''            try{
                startActivity(intent);
                reportAR((GOOGLE_APP.equals(route[0])?"Google 앱":"Google Play AR 서비스")+" 실행 요청 완료 · 모델 표시 여부를 확인하세요.");
                return true;
            }catch(ActivityNotFoundException|SecurityException ex){
                android.util.Log.w("RoomFitAR",route[0]+" 로 Scene Viewer 실행 불가",ex);
            }''','''            try{
                sceneViewerLaunchedAt=android.os.SystemClock.elapsedRealtime();sceneViewerPaused=false;
                startActivity(intent);
                final long launchedAt=sceneViewerLaunchedAt;
                // 아무 화면도 뜨지 않으면(onPause 없음) 2초 뒤 안내한다.
                if(web!=null)web.postDelayed(()->{if(launchedAt==sceneViewerLaunchedAt&&!sceneViewerPaused&&!isFinishing()){sceneViewerLaunchedAt=0;showSceneViewerClosed();}},2000);
                reportAR((GOOGLE_APP.equals(route[0])?"Google 앱":"Google Play AR 서비스")+" 실행 요청 완료 · 모델 표시 여부를 확인하세요.");
                return true;
            }catch(ActivityNotFoundException|SecurityException ex){
                sceneViewerLaunchedAt=0;
                android.util.Log.w("RoomFitAR",route[0]+" 로 Scene Viewer 실행 불가",ex);
            }''')
 return sub(s,'''    @Override protected void onSaveInstanceState(Bundle state){web.saveState(state);super.onSaveInstanceState(state);}''',r'''    /** 3.9.7: Google AR이 열렸다가 바로 닫히거나 아예 안 뜨는 경우를 감지한다. */
    private long sceneViewerLaunchedAt=0;
    private boolean sceneViewerPaused=false;
    @Override protected void onPause(){super.onPause();if(sceneViewerLaunchedAt!=0)sceneViewerPaused=true;}
    @Override protected void onResume(){
        super.onResume();
        if(sceneViewerLaunchedAt==0||!sceneViewerPaused)return;
        long away=android.os.SystemClock.elapsedRealtime()-sceneViewerLaunchedAt;
        sceneViewerLaunchedAt=0;
        if(away<3000)showSceneViewerClosed();
    }
    private void showSceneViewerClosed(){
        reportAR("Google AR 뷰어가 바로 닫혔습니다.");
        new AlertDialog.Builder(this).setTitle("Google AR이 바로 닫혔어요")
            .setMessage("룸핏은 Google AR 뷰어에 실행을 요청했지만, 휴대폰의 Google 앱이 화면을 띄우지 않았어요. 보통 Google 앱이나 Google Play AR 서비스가 오래됐거나, 기기가 Google AR 뷰어를 지원하지 않을 때 생겨요.\n\n룸핏 자체 AR로 바로 볼 수 있어요.")
            .setPositiveButton("앱 내 AR로 보기",(d,w)->readSelectedScene(true))
            .setNeutralButton("Google 앱 업데이트",(d,w)->external(Uri.parse("https://play.google.com/store/apps/details?id="+GOOGLE_APP)))
            .setNegativeButton("닫기",null).show();
    }
    @Override protected void onSaveInstanceState(Bundle state){web.saveState(state);super.onSaveInstanceState(state);}''')
edit('app/src/main/java/kr/ac/roomfit/app/MainActivity.java',main,'2897a4cb689224a43721e4c8e6878ed82e1f83f4a0176ada166ac8baf02e9d82')
edit('app/src/main/java/kr/ac/roomfit/app/SimpleFurnitureArActivity.java',lambda s:sub(s,'룸핏 3.9.6 · 내부 가구 AR','룸핏 3.9.7 · 내부 가구 AR'),'077d5f65bd64e73fefa033308ef450d61fe896c25bfe038160db6b02d4670399')
edit('app/build.gradle',lambda s:sub(sub(s,'versionCode 396','versionCode 397'),"versionName '3.9.6'","versionName '3.9.7'"),'c307dc7a8c2c631b4c9983a3b4150bcc9d6fee973900e64627796e5ad237ee4d')
edit('app/src/main/AndroidManifest.xml',lambda s:sub(sub(s,'android:versionCode="396"','android:versionCode="397"'),'android:versionName="3.9.6"','android:versionName="3.9.7"'),'5c863d35e57e21e0684723bbd9f8908f94c4db27a3a1cad200a773c2e4b394b0')
print('All four changed app files match uploaded RoomFit 3.9.7 SHA256')
