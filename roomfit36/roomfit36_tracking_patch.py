#!/usr/bin/env python3
"""RoomFit 3.6: ARCore camera texture lifecycle, tracking diagnostics.

Does not fabricate a tracked 3D pose when ARCore is paused.
"""
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
p = root/'app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java'
s = p.read_text(encoding='utf-8')

def replace(old, new):
    global s
    assert old in s, 'Expected base source missing: ' + old[:100]
    s = s.replace(old, new, 1)

replace('import android.content.Intent;', '''import android.content.Intent;
import android.content.ClipData;
import android.content.ClipboardManager;''')
replace('private Session session;', '''private volatile Session session;
    private volatile int resumeGeneration=0;''')
replace('룸핏 3.5 · 간단 AR 배치', '룸핏 3.6 · AR 추적 진단')
replace('retry.setText("↻ AR 카메라 다시 시작");', 'retry.setText("↻ AR 세션 완전 초기화");')
replace('retry.setOnClickListener(v->recreate());bottom.addView(retry);', '''retry.setOnClickListener(v->recreate());bottom.addView(retry);
            Button copyDiag=new Button(this);
            copyDiag.setText("AR 진단 복사 · 문제 발생 시 공유");copyDiag.setTextSize(11);
            copyDiag.setOnClickListener(v->{
                String report=renderer.diagnosticText();
                ClipboardManager cm=(ClipboardManager)getSystemService(CLIPBOARD_SERVICE);
                if(cm!=null){cm.setPrimaryClip(ClipData.newPlainText("RoomFit AR diagnostics",report));
                    Toast.makeText(this,"AR 진단을 복사했어요. 대화창에 붙여넣어 주세요.",Toast.LENGTH_LONG).show();}
            });bottom.addView(copyDiag);''')
replace('session.resume();surface.onResume();surfaceRunning=true;', 'session.resume();resumeGeneration++;surface.onResume();surfaceRunning=true;')
replace('''        private int backgroundProgram,cubeProgram,texture,width=1,height=1;''', '''        private int backgroundProgram,cubeProgram,texture,width=1,height=1;
        private Session textureBoundSession=null;
        private int textureBoundGeneration=-1,textureBoundId=-1;
        private int geometryRotation=-1,geometryWidth=-1,geometryHeight=-1;
        private volatile long startedAt=0,trackingLastAt=0;
        private volatile long latestCameraTimestamp=0;
        private volatile long uniqueFrameCount=0,zeroTimestampCount=0,drawCallCount=0;
        private volatile String trackingStateText="WAITING",trackingFailureText="NONE",lastFrameError="";
        private long lastDiagnosticUpdate=0;
        String diagnosticText(){
            long elapsed=startedAt==0?0:(System.currentTimeMillis()-startedAt)/1000;
            return "RoomFit 3.6 AR tracking report\\n"+
                "Device: "+android.os.Build.MANUFACTURER+" "+android.os.Build.MODEL+"\\n"+
                "Android: "+android.os.Build.VERSION.RELEASE+"\\n"+
                "Session: "+(session==null?"null":"created")+" generation="+resumeGeneration+"\\n"+
                "Tracking: "+trackingStateText+" / "+trackingFailureText+"\\n"+
                "ElapsedSeconds: "+elapsed+"\\n"+
                "CameraFrames: "+uniqueFrameCount+" zeroTimestamps="+zeroTimestampCount+"\\n"+
                "GLDrawCalls: "+drawCallCount+" lastCameraTimestampNs="+latestCameraTimestamp+"\\n"+
                "TextureBound: "+(textureBoundId>0)+" GLTexture="+texture+"\\n"+
                "LastError: "+lastFrameError;
        }
        private void updateTrackingStatus(String msg,boolean ready){
            long now=System.currentTimeMillis();
            if(now-lastDiagnosticUpdate<700 && !ready)return;
            lastDiagnosticUpdate=now;
            updateStatus(msg,ready);
        }''')
replace('''            GLES20.glClearColor(.1f,.12f,.1f,1);int[] textures=new int[1];''', '''            textureBoundSession=null;textureBoundGeneration=-1;textureBoundId=-1;
            geometryRotation=-1;geometryWidth=-1;geometryHeight=-1;
            GLES20.glClearColor(.1f,.12f,.1f,1);int[] textures=new int[1];''')
replace('''            try{
                active.setDisplayGeometry(getWindowManager().getDefaultDisplay().getRotation(),width,height);
                active.setCameraTextureName(texture);
                Frame frame=active.update();
                if(frame.getTimestamp()==0)return;
                drawBackground(frame);
                Camera camera=frame.getCamera();
                if(camera.getTrackingState()!=TrackingState.TRACKING){
                    captureRequested=false;
                    updateStatus("AR 인식 대기 · "+camera.getTrackingFailureReason().name()+" · 밝은 바닥을 천천히 비춰주세요. ⚠ 크기는 참고값입니다.",false);
                    return;
                }''', '''            try{
                drawCallCount++;
                if(startedAt==0)startedAt=System.currentTimeMillis();
                // ARCore official Hello AR: bind texture once per GL texture / resumed session.
                // Rebinding every frame can invalidate the previous texture contents.
                int generation=resumeGeneration;
                if(textureBoundSession!=active||textureBoundGeneration!=generation||textureBoundId!=texture){
                    active.setCameraTextureName(texture);
                    textureBoundSession=active;textureBoundGeneration=generation;textureBoundId=texture;
                    geometryRotation=-1;
                    startedAt=System.currentTimeMillis();
                    uniqueFrameCount=0;zeroTimestampCount=0;latestCameraTimestamp=0;
                    trackingStateText="WAITING";trackingFailureText="NONE";
                    Log.i("RoomFitAR","AR texture bound once: generation="+generation+" texture="+texture);
                }
                int rotation=getWindowManager().getDefaultDisplay().getRotation();
                if(rotation!=geometryRotation||geometryWidth!=width||geometryHeight!=height){
                    active.setDisplayGeometry(rotation,width,height);
                    geometryRotation=rotation;geometryWidth=width;geometryHeight=height;
                }
                Frame frame=active.update();
                long timestamp=frame.getTimestamp();
                if(timestamp==0){
                    zeroTimestampCount++;
                    updateTrackingStatus("AR 카메라 프레임 대기 · 현재 "+zeroTimestampCount+"회 · 앱을 재시작해 보세요.",false);
                    return;
                }
                if(timestamp!=latestCameraTimestamp){latestCameraTimestamp=timestamp;uniqueFrameCount++;}
                drawBackground(frame);
                Camera camera=frame.getCamera();
                trackingStateText=camera.getTrackingState().name();
                trackingFailureText=camera.getTrackingFailureReason().name();
                if(camera.getTrackingState()!=TrackingState.TRACKING){
                    captureRequested=false;
                    long elapsed=(System.currentTimeMillis()-startedAt)/1000;
                    String guide=elapsed>12
                        ?"추적이 오래 지연됐습니다. AR 세션 완전 초기화 또는 진단 복사"
                        :"바닥과 주변 물체를 천천히 비춰주세요";
                    updateTrackingStatus("AR "+trackingStateText+"/"+trackingFailureText+
                        " · "+elapsed+"초 · 카메라 프레임 "+uniqueFrameCount+"개 · "+guide+
                        " · ⚠ 크기는 참고값",false);
                    return;
                }
                trackingLastAt=System.currentTimeMillis();''')
replace('''            }catch(Exception ex){
                Log.e("RoomFitAR","Simple AR frame failed",ex);''', '''            }catch(Exception ex){
                lastFrameError=ex.getClass().getSimpleName()+": "+String.valueOf(ex.getMessage());
                Log.e("RoomFitAR","AR diagnostic frame failed",ex);''')
replace('''meta.put("roomfitVersion","3.5.0")''','''meta.put("roomfitVersion","3.6.0")''')
# Render actual diagnostic state; don't claim successful tracking without a device test.
p.write_text(s, encoding='utf-8')

build=root/'app/build.gradle'
b=build.read_text(encoding='utf-8')
b=re.sub(r'\bversionCode\s+\d+','versionCode 360',b)
b=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]", "versionName '3.6.0'", b)
build.write_text(b,encoding='utf-8')
manifest=root/'app/src/main/AndroidManifest.xml'
m=manifest.read_text(encoding='utf-8')
m=re.sub(r'android:versionCode="\d+"','android:versionCode="360"',m)
m=re.sub(r'android:versionName="[^"]+"','android:versionName="3.6.0"',m)
manifest.write_text(m,encoding='utf-8')
print('RoomFit 3.6 tracking diagnostics and frame texture lifecycle patch OK')