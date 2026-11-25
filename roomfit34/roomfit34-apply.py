#!/usr/bin/env python3
"""Upgrade RoomFit 3.3 into a five-stage workflow with usable AR diagnostics."""
from pathlib import Path
import re
import sys
root=Path(sys.argv[1]);web=root/'app/src/main/assets/web'
for fn in ['roomfit34-ui.js','roomfit34-ui.css']:
    (web/fn).write_bytes((Path(__file__).parent/fn).read_bytes())
h=web/'roomfit3.html';s=h.read_text(encoding='utf-8')
assert '<script src="/roomfit33-ui.js"></script>' in s
s=s.replace('/roomfit33-ui.js','/roomfit34-ui.js').replace('/roomfit33-ui.css','/roomfit34-ui.css')
s=s.replace('룸핏 3.3 |','룸핏 3.4 |')
h.write_text(s,encoding='utf-8')

# A one-click camera-free 3D viewer from the actual selected product, not an AR app.
main=root/'app/src/main/java/kr/ac/roomfit/app/MainActivity.java'
a=main.read_text(encoding='utf-8')
anchor='''        @JavascriptInterface public void openLockedAR(final String scene)'''
assert anchor in a
bridge='''        @JavascriptInterface public void openFurniturePreview(final String raw){
            if(raw==null||raw.length()>4000)return;
            runOnUiThread(()->{
                try{
                    org.json.JSONObject p=new org.json.JSONObject(raw);
                    String id=p.getString("id"),name=p.getString("name"),kind=p.optString("kind","table");
                    if(!id.matches("[A-Za-z0-9_.-]{1,90}")||name.isEmpty()||name.length()>160||kind.length()>32)throw new IllegalArgumentException();
                    float width=(float)p.getDouble("width")/100f,depth=(float)p.getDouble("depth")/100f,height=(float)p.getDouble("height")/100f;
                    if(!Float.isFinite(width)||!Float.isFinite(depth)||!Float.isFinite(height)||width<.01f||depth<.01f||height<.01f||width>6f||depth>6f||height>6f)throw new IllegalArgumentException();
                    Intent intent=new Intent(MainActivity.this,FurniturePreviewActivity.class);
                    intent.putExtra("productId",id);intent.putExtra("itemName",name);intent.putExtra("kind",kind);
                    intent.putExtra("width",width);intent.putExtra("depth",depth);intent.putExtra("height",height);
                    startActivity(intent);
                }catch(Exception ex){toast("가구 3D 미리보기를 열지 못했어요.");}
            });
        }

'''
a=a.replace(anchor,bridge+anchor,1)
main.write_text(a,encoding='utf-8')

ar=root/'app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java';a=ar.read_text(encoding='utf-8')
assert 'Button preview3d=new Button(this);' in a
marker='''            bottom.addView(preview3d);
        }
        if(roomfit3Mode)'''
assert marker in a
replacement='''            bottom.addView(preview3d);
            LinearLayout quick=new LinearLayout(this);
            quick.setOrientation(LinearLayout.HORIZONTAL);
            Button previewTop=new Button(this);previewTop.setText("👁 3D 미리보기");previewTop.setTextSize(11);
            previewTop.setOnClickListener(v->preview3d.performClick());
            quick.addView(previewTop,new LinearLayout.LayoutParams(0,dp(40),1));
            Button retryTracking=new Button(this);retryTracking.setText("↻ AR 추적 다시 시작");retryTracking.setTextSize(11);
            retryTracking.setOnClickListener(v->{
                new AlertDialog.Builder(this).setTitle("AR 카메라 다시 시작")
                    .setMessage("위치 추적이 멈췄다면 다시 시작할 수 있어요. 임시 배치한 가구 위치는 초기화됩니다.")
                    .setNegativeButton("취소",null)
                    .setPositiveButton("다시 시작",(dialog,which)->recreate()).show();
            });
            quick.addView(retryTracking,new LinearLayout.LayoutParams(0,dp(40),1));
            top.addView(quick);
        }
        if(roomfit3Mode)'''
a=a.replace(marker,replacement,1)
# Updated instructions based on known AR limitations (do not claim device support without checking).
a=a.replace('방을 여러 방향에서 비춰 Depth 정보를 확보하세요. 가구를 선택하고 바닥을 터치하면 장애물 겹침을 점검합니다. 카메라 사각지대는 검사할 수 없습니다.',
 '''1. 넓고 밝은 바닥을 비추며 천천히 움직이세요. 2. 화면을 터치해 배치하세요. 인식이 안 되면 「AR 추적 다시 시작」 또는 「3D 미리보기」를 누르세요. 인식되지 않은 장애물은 검사할 수 없습니다.''')
needle='''                    updateStatus("AR 위치 추적 대기 ("+camera.getTrackingState().name()+"/"+camera.getTrackingFailureReason().name()+") · 넓은 바닥을 비춰주세요 · 아래 3D 미리보기는 사용 가능",false);'''
assert needle in a
a=a.replace(needle,'''                    String why=camera.getTrackingFailureReason().name();
                    String action="NONE".equals(why)?"ARCore 위치 인식 준비 중입니다. 밝은 바닥·벽면을 천천히 비춰주세요.":
                        "INSUFFICIENT_LIGHT".equals(why)?"너무 어두워요. 조명이 밝은 곳으로 이동하세요.":
                        "EXCESSIVE_MOTION".equals(why)?"휴대폰을 느리게 움직여주세요.":
                        "INSUFFICIENT_FEATURES".equals(why)?"무늬가 있는 바닥이나 벽면을 비춰주세요.":
                        "CAMERA_UNAVAILABLE".equals(why)?"카메라를 사용하는 앱을 종료하고 다시 시도하세요.":
                        "ARCore 추적을 시작할 수 없습니다. 화면의 재시도 버튼을 눌러주세요.";
                    updateStatus("AR 추적 대기 · "+why+" · "+action+" 3D 미리보기는 바로 사용할 수 있습니다.",false);''',1)
# This is an AR render loop; never silently claim collision checking has succeeded if it has not.
needle='''                String action= !ready?"각 가구를 선택하고 바닥을 터치하세요":'''
assert needle in a
a=a.replace(needle,'''                if(roomfit3Mode&&count==0&&placementWarning.isEmpty())stateText="AR 추적 연결됨 · 가구를 선택한 뒤 바닥을 터치하세요. 바닥이 인식되지 않으면 잠시 이동하거나 3D 미리보기를 이용하세요.";
                String action= !ready?"각 가구를 선택하고 바닥을 터치하세요":''',1)
# Distinguish AR app version from the historical 3.2.2 engine.
a=a.replace('룸핏 3.2.2 · AR 배치 + 3D 미리보기','룸핏 3.4 · AR 배치 + 3D 미리보기')
a=a.replace('meta.put("roomfitVersion","3.2.2")','meta.put("roomfitVersion","3.4.0")')
ar.write_text(a,encoding='utf-8')

build=root/'app/build.gradle';s=build.read_text(encoding='utf-8')
s=re.sub(r'\bversionCode\s+\d+','versionCode 340',s)
s=re.sub(r'\bversionName\s+[\'"][^\'\"]+[\'"]',"versionName '3.4.0'",s)
build.write_text(s,encoding='utf-8')
manifest=root/'app/src/main/AndroidManifest.xml';s=manifest.read_text(encoding='utf-8')
s=re.sub(r'android:versionCode="\d+"','android:versionCode="340"',s)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="3.4.0"',s)
manifest.write_text(s,encoding='utf-8')
print('RoomFit 3.4 five-stage UI & AR diagnostic preview installed',root)