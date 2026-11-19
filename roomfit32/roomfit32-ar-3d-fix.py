#!/usr/bin/env python3
"""RoomFit 3.2.2: standalone 3D preview and ARCore Instant Placement fallback."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
src=root/"app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java"
s=src.read_text(encoding="utf-8")
assert "public final class LockedArActivity" in s
assert "private boolean validPlacement(" in s
assert "private final class Scene" in s
assert "roomfit3Mode" in s

# Allow 3D viewing without ARCore camera position tracking.
needle='''        if(roomfit3Mode){dimensions=new TextView(this);'''
assert needle in s
s=s.replace(needle,'''        if(roomfit3Mode){
            Button preview3d=new Button(this);
            preview3d.setText("👁 선택 가구 3D 미리보기 (AR 인식 없이 확인)");
            preview3d.setTextSize(12);
            preview3d.setOnClickListener(v->{
                int selectedPosition=Math.max(0,Math.min(items.size()-1,picker.getSelectedItemPosition()));
                Item it=items.get(selectedPosition);
                Intent intent=new Intent(this,FurniturePreviewActivity.class);
                intent.putExtra("productId",it.product.optString("id",""));
                intent.putExtra("itemName",it.name);
                intent.putExtra("kind",it.kind);
                intent.putExtra("width",it.width);
                intent.putExtra("depth",it.depth);
                intent.putExtra("height",it.height);
                startActivity(intent);
            });
            bottom.addView(preview3d);
        }
        if(roomfit3Mode){dimensions=new TextView(this);''',1)
needle='''config.setLightEstimationMode(Config.LightEstimationMode.AMBIENT_INTENSITY);depthSupported='''
assert needle in s
s=s.replace(needle,'''config.setLightEstimationMode(Config.LightEstimationMode.AMBIENT_INTENSITY);
            if(roomfit3Mode)config.setInstantPlacementMode(Config.InstantPlacementMode.LOCAL_Y_UP);
            depthSupported=''',1)
needle='''boolean modelFailed=false;'''
assert needle in s
s=s.replace(needle,'''boolean modelFailed=false,provisional=false;''',1)
needle='''if(!onObservedFloor(placedPose(it),it,it.yaw)){unknown++;continue;}'''
assert needle in s
s=s.replace(needle,'''if(it.provisional || !onObservedFloor(placedPose(it),it,it.yaw)){unknown++;continue;}''',1)
needle='''                PointF point=tap;tap=null;if(point!=null){for(HitResult hit:frame.hitTest(point.x,point.y)){Trackable track=hit.getTrackable();if(track instanceof Plane&&((Plane)track).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)track).isPoseInPolygon(hit.getHitPose())){if(roomfit3Mode){'''
assert needle in s
s=s.replace(needle,'''                PointF point=tap;tap=null;if(point!=null){
                  ArrayList<HitResult> hits=new ArrayList<>(frame.hitTest(point.x,point.y));
                  boolean hasPlane=false;
                  for(HitResult hit:hits){
                      Trackable t=hit.getTrackable();
                      if(t instanceof Plane&&((Plane)t).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)t).isPoseInPolygon(hit.getHitPose())){
                          hasPlane=true;break;
                      }
                  }
                  if(roomfit3Mode&&!hasPlane){
                      // Instant Placement estimates depth and scale until a real plane is tracked.
                      hits.addAll(frame.hitTestInstantPlacement(point.x,point.y,1.25f));
                  }
                  for(HitResult hit:hits){
                    Trackable track=hit.getTrackable();
                    boolean planeHit=track instanceof Plane&&((Plane)track).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)track).isPoseInPolygon(hit.getHitPose());
                    boolean instantHit=roomfit3Mode&&track instanceof InstantPlacementPoint;
                    if(planeHit||instantHit){
                        if(instantHit){
                            Item item=items.get(selected);
                            if(footprintConflict(hit.getHitPose(),item,item.yaw)){warn("🔴 다른 AR 가구와 겹칩니다.");break;}
                            lastDepthVerdict=ObstacleMath.Verdict.UNKNOWN;
                            depthUnknown=1;
                            warn("🟠 바닥 미인식 · 임시 가구 위치입니다. 넓은 바닥에서 다시 배치하세요.");
                        }
                        if(roomfit3Mode&&!instantHit){''',1)
needle='''                                Anchor next=hit.createAnchor();if(roomfit2Mode){'''
assert needle in s
s=s.replace(needle,'''                                Anchor next=hit.createAnchor();if(roomfit2Mode){''',1)
needle='''}else{Item it=items.get(selected);if(it.anchor!=null)it.anchor.detach();it.anchor=next;it.dx=it.dz=0;}break;}}}'''
assert needle in s
s=s.replace(needle,''' }else{Item it=items.get(selected);if(it.anchor!=null)it.anchor.detach();it.anchor=next;it.dx=it.dz=0;it.provisional=instantHit;}break;}}}''',1)
# For roomfit3 provisional anchors, never enable photo save; require replacing it with tracked plane.
needle='''                if(roomfit3Mode){
                    for(int a=0;a<items.size();a++)'''
assert needle in s
s=s.replace(needle,'''                if(roomfit3Mode){
                    for(Item item:items)if(item.anchor!=null&&item.provisional)depthRisk=true;
                    for(int a=0;a<items.size();a++)''',1)
needle='''                String action= !ready?"각 가구를 선택하고 바닥을 터치하세요":'''
assert needle in s
s=s.replace(needle,'''                String action= !ready?"각 가구를 선택하고 바닥을 터치하세요":''',1)
# Clarify preview-only state in status, including absence of AR tracking for tap.
needle='''if(camera.getTrackingState()!=TrackingState.TRACKING){captureRequested=false;updateStatus("바닥을 천천히 비춰주세요 · "+camera.getTrackingFailureReason().name(),false);return;}'''
assert needle in s
s=s.replace(needle,'''if(camera.getTrackingState()!=TrackingState.TRACKING){
                    captureRequested=false;
                    updateStatus("AR 위치 추적 대기 ("+camera.getTrackingState().name()+"/"+camera.getTrackingFailureReason().name()+") · 넓은 바닥을 비춰주세요 · 아래 3D 미리보기는 사용 가능",false);
                    return;
                }''',1)
# Make provisional state explicit in status.
needle='''                updateStatus(stateText+" · 배치 "+count+" / "+items.size()+" · "+action,ready&&!depthRisk);'''
assert needle in s
s=s.replace(needle,'''                boolean anyProvisional=false;
                if(roomfit3Mode)for(Item it:items)if(it.anchor!=null&&it.provisional){anyProvisional=true;break;}
                if(anyProvisional)action="가구는 임시 표시 중 · 바닥 인식 후 다시 터치해 확정하세요 (저장 불가)";
                updateStatus(stateText+" · 배치 "+count+" / "+items.size()+" · "+action,ready&&!depthRisk);''',1)
# ensure metadata labels are honest
s=s.replace('meta.put("roomfitVersion","3.1.1");','meta.put("roomfitVersion","3.2.2");')
s=s.replace('title.setText(roomfit3Mode?"룸핏 3.1 · 스마트 AR 배치"', 'title.setText(roomfit3Mode?"룸핏 3.2.2 · AR 배치 + 3D 미리보기"')
src.write_text(s,encoding="utf-8")
activity=root/"app/src/main/java/kr/ac/roomfit/app/FurniturePreviewActivity.java"
activity.write_text((Path(__file__).parent/"FurniturePreviewActivity.java").read_text(encoding="utf-8"),encoding="utf-8")
manifest=root/"app/src/main/AndroidManifest.xml"
m=manifest.read_text(encoding="utf-8")
assert '<activity android:name=".LockedArActivity"' in m
m=m.replace('<activity android:name=".LockedArActivity"', '<activity android:name=".FurniturePreviewActivity" android:exported="false" android:screenOrientation="portrait"/>\n        <activity android:name=".LockedArActivity"',1)
m=m.replace('android:versionCode="311" android:versionName="3.1.1"','android:versionCode="322" android:versionName="3.2.2"')
manifest.write_text(m,encoding="utf-8")
build=root/"app/build.gradle"
b=build.read_text(encoding="utf-8")
b=b.replace("versionCode 311","versionCode 322").replace("versionName '3.1.1'","versionName '3.2.2'").replace('versionName "3.1.1"','versionName "3.2.2"')
build.write_text(b,encoding="utf-8")
print("RoomFit 3.2.2: independent 3D viewer + Instant Placement patch applied")
