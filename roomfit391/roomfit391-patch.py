#!/usr/bin/env python3
"""RoomFit 3.9.1: route stage 5 to native AR; use plane/point hits instead of blank scene.

The user-supplied older app started Scene Viewer from a WebView model-viewer intent.
The 3.9 direct Google-app intent does not open on their device, so do not use it as
primary path. This fixes silent plane-only hit-test failures and adds bounded
on-screen diagnostics without changing the existing five-stage UI.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
j=root/'app/src/main/java/kr/ac/roomfit/app'
web=root/'app/src/main/assets/web'

def change(file,old,new,once=True):
    txt=file.read_text(encoding='utf-8')
    assert old in txt, f'Missing expected code in {file.name}: {old[:110]!r}'
    txt=txt.replace(old,new,1 if once else -1)
    file.write_text(txt,encoding='utf-8')

main=j/'MainActivity.java'
change(main,'RoomFitStableAR.open(MainActivity.this,scene,()->launchNativeFloorAR(scene));','launchNativeFloorAR(scene);')
change(main,'RoomFitAndroid/3.9.0','RoomFitAndroid/3.9.1')

ar=j/'SimpleFurnitureArActivity.java'
change(ar,'import com.google.ar.core.Plane;', 'import com.google.ar.core.Plane;\nimport com.google.ar.core.Point;')
change(ar,'룸핏 3.9 · 바닥 고정 AR','룸핏 3.9.1 · 기본 가구 AR')
change(ar,'바닥에 가구 고정 / 다시 놓기','가구 놓기 / 위치 다시 지정')
change(ar,'바닥을 천천히 비추고 화면을 터치해 가구를 고정하세요.','밝은 바닥을 비추고 터치하세요. 바닥을 못 찾으면 추적된 특징점에 가구를 고정합니다.')
change(ar,'private Pose previewPose;', '''private Pose previewPose;
        private String anchorKind="미배치";
        private boolean pointAnchored=false;
        private long framesTracked=0;
        private String placementInfo="가구 놓기 버튼 또는 바닥을 터치하세요";
        private long placementInfoUntil=0;''')
# Avoid throwing away the first tap on item selection.
change(ar,'selected = pos; releaseAnchor(); spawnRequested = true;',
       'selected = pos; releaseAnchor(); spawnRequested = false;')
change(ar,'''            previewPose = null;
        }
        @Override public void onDrawFrame(GL10 gl)''', '''            previewPose = null;
            pointAnchored = false;
            anchorKind="미배치";
        }
        @Override public void onDrawFrame(GL10 gl)''')
old='''                // Never pin a camera-relative estimate: it floats / drifts
                // because it is not associated with an observed surface.
                // Prefer the hit-result's tracked Plane anchor, like Scene Viewer.
                PointF point = tap; tap = null;
                boolean requested = spawnRequested; spawnRequested = false;
                if (point != null || requested) {
                    float touchX=point!=null?point.x*width:width*0.50f;
                    float touchY=point!=null?point.y*height:height*0.58f;
                    HitResult hit=null;
                    for(HitResult found:frame.hitTest(touchX,touchY)){
                        Trackable track=found.getTrackable();
                        if(track instanceof Plane &&
                            track.getTrackingState()==TrackingState.TRACKING &&
                            ((Plane)track).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING &&
                            ((Plane)track).isPoseInPolygon(found.getHitPose())){
                            hit=found;break;
                        }
                    }
                    if(hit!=null){
                        setAnchor(hit.createAnchor(),false);
                    }else{
                        report("바닥 인식 중 · 밝은 바닥을 여러 방향에서 비춘 뒤 다시 터치하세요.");
                    }
                }
'''
new='''                // Important: a live camera and TRACKING state do not guarantee
                // a Plane hit. Carpet and narrow floors often track points first.
                // Never discard the user tap silently. Choose a true Plane anchor,
                // otherwise a tracked feature Point anchor; neither follows camera.
                framesTracked++;
                PointF point=tap; tap=null;
                boolean requested=spawnRequested; spawnRequested=false;
                if(point!=null || requested){
                    float sx=point!=null?point.x*width:width*.5f;
                    float sy=point!=null?point.y*height:height*.57f;
                    HitResult floor=null,feature=null;
                    // The request button checks the center and slightly below.
                    float[] candidates=requested&&point==null?
                        new float[]{sx,sy,sx,height*.72f,width*.32f,height*.62f,width*.68f,height*.62f}:
                        new float[]{sx,sy};
                    for(int i=0;i<candidates.length;i+=2){
                        for(HitResult hit:frame.hitTest(candidates[i],candidates[i+1])){
                            Trackable tr=hit.getTrackable();
                            if(tr.getTrackingState()!=TrackingState.TRACKING)continue;
                            if(tr instanceof Plane && ((Plane)tr).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING &&
                                    ((Plane)tr).isPoseInPolygon(hit.getHitPose())){
                                floor=hit;break;
                            }
                            if(feature==null && tr instanceof Point){feature=hit;}
                        }
                        if(floor!=null)break;
                    }
                    HitResult chosen=floor!=null?floor:feature;
                    if(chosen!=null){
                        try{
                            boolean pointMode=floor==null;
                            setAnchor(chosen.createAnchor(),pointMode);
                            anchorKind=pointMode?"특징점 고정 (바닥 높이 추정)":"바닥 평면 고정";
                            placementInfo=pointMode?
                                "🟠 특징점에 가구를 고정했습니다. 바닥 높이는 추정값이며 치수를 확인하세요.":
                                "🟢 실제 인식한 바닥에 가구를 고정했습니다.";
                            placementInfoUntil=System.currentTimeMillis()+6500;
                        }catch(Exception placementFailure){
                            Log.w(TAG,"Unable to anchor plane/point hit",placementFailure);
                            placementInfo="가구 고정 실패 · 휴대폰을 움직인 뒤 다시 눌러주세요.";
                            placementInfoUntil=System.currentTimeMillis()+6500;
                        }
                    }else{
                        int visiblePlanes=0,trackedPlanes=0;
                        for(Plane plane:current.getAllTrackables(Plane.class)){
                            if(plane.getType()==Plane.Type.HORIZONTAL_UPWARD_FACING){
                                visiblePlanes++;
                                if(plane.getTrackingState()==TrackingState.TRACKING)trackedPlanes++;
                            }
                        }
                        placementInfo="바닥/특징점이 아직 발견되지 않았습니다. 바닥 후보 "+trackedPlanes+"/"+visiblePlanes+
                            " · 밝고 무늬가 있는 공간을 여러 방향에서 비춘 뒤 다시 눌러주세요.";
                        placementInfoUntil=System.currentTimeMillis()+8500;
                    }
                }
'''
change(ar,old,new)
old='''                if(anchor != null && anchor.getTrackingState()==TrackingState.TRACKING){
                    anchor.getPose().toMatrix(base,0);
                    Furniture item=furniture.get(selected);
                    drawFurniture(item);
                    report("🟢 바닥에 고정된 가구 · 카메라를 움직여 고정 상태를 확인하세요. 크기는 참고값");
                } else if(anchor!=null){
                    report("바닥 고정 추적 일시 정지 · 카메라를 천천히 움직여주세요.");
                } else {
                    report("가구 고정 전 · 바닥을 인식시킨 후 바닥을 터치하세요.");
                }'''
new='''                if(anchor != null && anchor.getTrackingState()==TrackingState.TRACKING){
                    if(pointAnchored){
                        // A feature Point's orientation can be tilted. Keep the
                        // model upright in world coordinates while tracking its
                        // actual anchored position (not the phone's position).
                        float[] xyz=anchor.getPose().getTranslation();
                        Matrix.setIdentityM(base,0);
                        Matrix.translateM(base,0,xyz[0],xyz[1],xyz[2]);
                    }else anchor.getPose().toMatrix(base,0);
                    Furniture item=furniture.get(selected);
                    drawFurniture(item);
                    String msg=System.currentTimeMillis()<placementInfoUntil?placementInfo:
                        anchorKind+" · 카메라를 움직여 위치를 확인하세요 · 가구 크기는 참고용";
                    report(msg);
                }else if(anchor!=null){
                    report("AR Anchor 추적 대기 · 가구가 잠시 보이지 않습니다. 휴대폰을 움직여주세요.");
                }else{
                    String msg=System.currentTimeMillis()<placementInfoUntil?placementInfo:
                        "AR 추적 정상 · 바닥을 터치하거나 '가구 놓기'를 눌러주세요 ("+framesTracked+"프레임)";
                    report(msg);
                }'''
change(ar,old,new)
old='''            anchor = next;
            previewPose = next.getPose();
            report("🟢 실제 인식된 바닥에 가구를 고정했습니다. 가구 치수는 참고용입니다.");'''
new='''            anchor = next;
            pointAnchored=approximate;
            previewPose = next.getPose();
            report(approximate?"🟠 특징점 고정 · 바닥 높이는 추정값입니다.":
                "🟢 바닥 평면 고정 · 실제 치수는 확인하세요.");'''
change(ar,old,new)
# Fix non-tracking feedback to distinguish from placement failure.
change(ar,'report("AR 공간 인식 중 · 휴대폰을 천천히 움직여 주세요.");',
       'report("AR 카메라 추적 대기 ("+camera.getTrackingState()+"/"+camera.getTrackingFailureReason()+") · 밝은 바닥을 천천히 비춰주세요.");')
# The user still wants simple AR, not more controls.
ar.write_text(ar.read_text(encoding='utf-8'),encoding='utf-8')

html=web/'roomfit3.html'
txt=html.read_text(encoding='utf-8')
txt=txt.replace('예전 방식 · Google AR 바닥 고정 보기','앱 안에서 가구 AR로 띄우기')
txt=txt.replace('예전에 사용하던 Google AR 뷰어로 선택한 가구를 바닥에 고정해요. AR 뷰어는 한 번에 가구 하나를 보여줍니다.',
                '휴대폰 카메라가 바닥이나 특징점을 인식하면 가구를 그 위치에 고정합니다. 실제 치수는 확인하세요.')
txt=txt.replace('앱 내부에서 바닥 고정하기 (Google AR이 열리지 않을 때)','AR 카메라 다시 열기')
# Keep the second button for the existing JS event handler, but no duplicate UI.
txt=txt.replace('id="open-native-floor-ar" class="soft full" type="button" style="margin-top:10px"',
                'id="open-native-floor-ar" class="soft full" type="button" style="display:none"')
txt=txt.replace('룸핏 3.9 |','룸핏 3.9.1 |')
html.write_text(txt,encoding='utf-8')

for filename in ['roomfit34-ui.js','roomfit3.js']:
    p=web/filename
    s=p.read_text(encoding='utf-8')
    s=s.replace('ROOMFIT 3.9','ROOMFIT 3.9.1')
    if filename=='roomfit3.js':
        s=s.replace('AR 화면에서 선택한 가구가 표시됩니다. 화면을 터치하면 위치를 다시 놓을 수 있습니다. 크기는 참고용입니다.',
                    'AR 화면에서 바닥을 터치해 가구를 놓으세요. 바닥이 검출되지 않으면 특징점 배치를 시도합니다. 크기는 참고용입니다.')
    p.write_text(s,encoding='utf-8')

build=root/'app/build.gradle';txt=build.read_text(encoding='utf-8')
txt=re.sub(r'\bversionCode\s+\d+','versionCode 391',txt)
txt=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]","versionName '3.9.1'",txt)
build.write_text(txt,encoding='utf-8')
manifest=root/'app/src/main/AndroidManifest.xml';s=manifest.read_text(encoding='utf-8')
s=re.sub(r'android:versionCode="\d+"','android:versionCode="391"',s)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="3.9.1"',s)
manifest.write_text(s,encoding='utf-8')
print('RoomFit 3.9.1: Native AR default, Plane+Point anchoring, visible failure diagnostics.')