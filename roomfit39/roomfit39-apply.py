#!/usr/bin/env python3
"""RoomFit 3.9: restore old working Google Scene Viewer and use floor-only native anchors.
Run after the RoomFit 3.8 patch. Does not copy any original signing keys.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
java=root/"app/src/main/java/kr/ac/roomfit/app"
stable=Path(__file__).resolve().parent/"RoomFitStableAR.java"
assert stable.is_file()
(java/"RoomFitStableAR.java").write_text(stable.read_text(encoding="utf-8"),encoding="utf-8")

# Default stage-5 AR: exactly the original external Google Scene Viewer approach,
# with GLB assets served from public HTTPS (publish by workflow).
main=java/"MainActivity.java"
m=main.read_text(encoding="utf-8")
old='startActivityForResult(new Intent(MainActivity.this,SimpleFurnitureArActivity.class).putExtra("scene",scene),LOCKED_AR);'
assert old in m
m=m.replace(old,'RoomFitStableAR.open(MainActivity.this,scene,()->launchNativeFloorAR(scene));',1)
anchor='    public final class NativeBridge {'
assert anchor in m
m=m.replace(anchor,'''    private void launchNativeFloorAR(String scene){
        startActivityForResult(new Intent(this,SimpleFurnitureArActivity.class).putExtra("scene",scene),LOCKED_AR);
    }
'''+anchor,1)
anchor='        @JavascriptInterface public void restoreLockedAR()'
assert anchor in m
m=m.replace(anchor,'''        @JavascriptInterface public void openNativeFloorAR(final String scene){
            if(scene==null||scene.length()>32000)return;
            runOnUiThread(()->{
                try {new org.json.JSONObject(scene);launchNativeFloorAR(scene);}
                catch(Exception ex){toast("앱 내 바닥 고정 AR을 열지 못했습니다.");}
            });
        }
'''+anchor,1)
m=m.replace("RoomFitAndroid/3.8.0","RoomFitAndroid/3.9.0")
main.write_text(m,encoding="utf-8")

# Remove camera-relative fake placement. A model is considered anchored only
# when an actual horizontal plane hit is present. Never recreate the anchor
# from camera pose while rendering.
ar=java/"SimpleFurnitureArActivity.java"
s=ar.read_text(encoding="utf-8")
s=s.replace("룸핏 3.8 · 기본 가구 AR","룸핏 3.9 · 바닥 고정 AR")
s=s.replace('place.setText("가구 띄우기 / 다시 놓기");','place.setText("바닥에 가구 고정 / 다시 놓기");')
s=s.replace('status.setText("AR 카메라를 시작합니다…");','status.setText("바닥을 천천히 비추고 화면을 터치해 가구를 고정하세요.");')
old='''                // Always show a selected item when tracking becomes available.
                // A plane hit will give a true floor anchor. Without one, a clearly
                // labelled camera-relative AR anchor provides a visible reference.
                PointF point = tap; tap = null;
                boolean requested = spawnRequested; spawnRequested = false;
                if (point != null) {
                    HitResult hit = null;
                    for (HitResult found : frame.hitTest(point.x * width, point.y * height)) {
                        Trackable track = found.getTrackable();
                        if (track instanceof Plane &&
                            ((Plane) track).getType() == Plane.Type.HORIZONTAL_UPWARD_FACING &&
                            ((Plane) track).isPoseInPolygon(found.getHitPose())) { hit = found; break; }
                    }
                    if (hit != null) { setAnchor(hit.createAnchor(), false); }
                    else setAnchor(estimateAnchor(camera), true);
                } else if (anchor == null || requested) setAnchor(estimateAnchor(camera), true);'''
new='''                // Never pin a camera-relative estimate: it floats / drifts
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
                }'''
assert old in s
s=s.replace(old,new,1)
old='''                Pose pose = anchor != null ? anchor.getPose() : previewPose;
                if (pose != null) {
                    pose.toMatrix(base, 0);
                    Furniture item = furniture.get(selected);
                    drawFurniture(item);
                    report("가구 표시 중 · 바닥을 터치하면 위치 변경 (크기는 참고값)");
                }'''
new='''                if(anchor != null && anchor.getTrackingState()==TrackingState.TRACKING){
                    anchor.getPose().toMatrix(base,0);
                    Furniture item=furniture.get(selected);
                    drawFurniture(item);
                    report("🟢 바닥에 고정된 가구 · 카메라를 움직여 고정 상태를 확인하세요. 크기는 참고값");
                } else if(anchor!=null){
                    report("바닥 고정 추적 일시 정지 · 카메라를 천천히 움직여주세요.");
                } else {
                    report("가구 고정 전 · 바닥을 인식시킨 후 바닥을 터치하세요.");
                }'''
assert old in s
s=s.replace(old,new,1)
# Remove the misleading approximation routine and simplify anchor setup.
a=s.index('        private Anchor estimateAnchor(Camera camera) {')
b=s.index('        private void setAnchor(',a)
s=s[:a]+s[b:]
s=s.replace('''            report(approximate ? "임시 위치에 가구 표시 · 크기와 바닥 위치는 참고용" :
                "바닥에 가구 배치됨 · 크기는 참고용");''',
'''            report("🟢 실제 인식된 바닥에 가구를 고정했습니다. 가구 치수는 참고용입니다.");''')
ar.write_text(s,encoding="utf-8")

# Keep 4->5 wizard navigation; the original open-ar click now invokes Scene Viewer.
web=root/"app/src/main/assets/web"
flow=web/"roomfit3.html"
h=flow.read_text(encoding="utf-8")
h=h.replace('룸핏 3.4 |','룸핏 3.9 |')
h=h.replace('AR 카메라 다시 열기','예전 방식 · Google AR 바닥 고정 보기',1)
h=h.replace('AR 카메라가 실행되면 선택한 가구가 표시됩니다. 화면을 터치하면 위치를 바꿀 수 있습니다.',
'''예전에 사용하던 Google AR 뷰어로 선택한 가구를 바닥에 고정해요. AR 뷰어는 한 번에 가구 하나를 보여줍니다.''',1)
old='<button id="open-ar" class="primary full">예전 방식 · Google AR 바닥 고정 보기</button>'
assert old in h
h=h.replace(old,old+'''<button id="open-native-floor-ar" class="soft full" type="button" style="margin-top:10px">앱 내부에서 바닥 고정하기 (Google AR이 열리지 않을 때)</button>''')
h=h.replace('크기와 배치 위치는 참고용입니다. 장애물 탐지·빈 공간 추천·자동 측정 기능은 없습니다.',
'''실제 바닥을 인식해야 위치가 고정됩니다. 가구 크기는 참고값이며, 장애물 검사와 자동 치수 측정은 제공하지 않습니다.''')
flow.write_text(h,encoding="utf-8")

js=web/"roomfit3.js"
t=js.read_text(encoding="utf-8")
# Declare an additional native bridge entry via existing scene builder, keeping
# original selected furniture and metadata exactly the same.
old='''try{window.RoomfitNative.openLockedAR(JSON.stringify(scene));'''
assert old in t
t=t.replace(old,'''try{
  if(window.roomfitNativeFloorOnly){
    window.roomfitNativeFloorOnly=false;
    window.RoomfitNative.openNativeFloorAR(JSON.stringify(scene));
  }else window.RoomfitNative.openLockedAR(JSON.stringify(scene));''',1)
old="$('open-ar').addEventListener('click',ar);"
assert old in t
t=t.replace(old,old+'''$('open-native-floor-ar').addEventListener('click',()=>{
  window.roomfitNativeFloorOnly=true;ar();
});''',1)
js.write_text(t,encoding="utf-8")
styled=web/"roomfit34-ui.js"
u=styled.read_text(encoding="utf-8")
u=u.replace('ROOMFIT 3.8','ROOMFIT 3.9')
styled.write_text(u,encoding="utf-8")

build=root/"app/build.gradle"
b=build.read_text(encoding="utf-8")
b=re.sub(r"\bversionCode\s+\d+","versionCode 390",b)
b=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]","versionName '3.9.0'",b)
build.write_text(b,encoding="utf-8")
manifest=root/"app/src/main/AndroidManifest.xml"
v=manifest.read_text(encoding="utf-8")
v=re.sub(r'android:versionCode="\d+"','android:versionCode="390"',v)
v=re.sub(r'android:versionName="[^"]+"','android:versionName="3.9.0"',v)
manifest.write_text(v,encoding="utf-8")
print("RoomFit 3.9: Google Scene Viewer restored, native AR floor-only anchoring enabled")
