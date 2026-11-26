#!/usr/bin/env python3
"""RoomFit 3.7: last-resort AR placement after verified TRACKING.
Keep five-stage UI, render actual product GLB, keep all size values advisory.
"""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
p=root/"app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java"
s=p.read_text(encoding="utf-8")
def replace(old,new):
    global s
    if old not in s: raise AssertionError("Expected existing source: "+old[:100])
    s=s.replace(old,new,1)

replace("룸핏 3.6 · AR 추적 진단","룸핏 3.7 · 가구 AR 배치")
replace("        surface.setOnTouchListener((v,e)->{if(e.getAction()==MotionEvent.ACTION_UP){renderer.tap=new PointF(e.getX(),e.getY());return true;}return true;});",
'''        // Keep tap coordinates normalized: the GLSurfaceView and GL framebuffer
        // can have different dimensions after insets and display rotations.
        surface.setOnTouchListener((v,e)->{
            if(e.getActionMasked()==MotionEvent.ACTION_UP){
                renderer.tap=new PointF(
                    Math.max(0f,Math.min(1f,e.getX()/Math.max(1f,v.getWidth()))),
                    Math.max(0f,Math.min(1f,e.getY()/Math.max(1f,v.getHeight()))));
                renderer.tapReceived++;
            }
            return true;
        });''')
replace('''            bottom.addView(preview3d);
            Button retry=new Button(this);''',
'''            bottom.addView(preview3d);
            Button quickPlace=new Button(this);
            quickPlace.setText("📍 가구 바로 표시 (바닥 인식 없이 임시 배치)");
            quickPlace.setTextSize(12);
            quickPlace.setOnClickListener(v->{
                // Only the GL rendering thread may touch the ARCore session.
                surface.queueEvent(()->renderer.quickPlaceRequested=true);
            });
            bottom.addView(quickPlace);
            Button retry=new Button(this);''')
replace('''        private volatile String trackingStateText="WAITING",trackingFailureText="NONE",lastFrameError="";''',
'''        private volatile String trackingStateText="WAITING",trackingFailureText="NONE",lastFrameError="";
        private volatile long tapReceived=0;
        private long tapsProcessed=0,planeHitCount=0,instantHitCount=0,approximateCount=0;
        private volatile String lastPlacementMode="NONE";
        private volatile boolean quickPlaceRequested=false;''')
replace('''                "TextureBound: "+(textureBoundId>0)+" GLTexture="+texture+"\\n"+
                "LastError: "+lastFrameError;''',
'''                "TextureBound: "+(textureBoundId>0)+" GLTexture="+texture+"\\n"+
                "TapsReceived: "+tapReceived+" TapsProcessed: "+tapsProcessed+"\\n"+
                "PlaneHits: "+planeHitCount+" InstantHits: "+instantHitCount+" Approximate: "+approximateCount+"\\n"+
                "LastPlacementMode: "+lastPlacementMode+"\\n"+
                "LastError: "+lastFrameError;''')
# Explicit fallback anchored in front of camera; warn because this is NOT floor-fitting.
replace('''        private void warn(String text){placementWarning=text;warningUntil=System.currentTimeMillis()+4000;}''',
'''        private void warn(String text){placementWarning=text;warningUntil=System.currentTimeMillis()+6500;}

        private void placeApproximatelyInFront(Camera camera,String origin) {
            if(camera.getTrackingState()!=TrackingState.TRACKING){
                warn("AR 추적을 시작한 뒤 다시 눌러주세요.");
                lastPlacementMode="REJECTED_NOT_TRACKING";
                return;
            }
            // A free world anchor lets a model render even when plane- and
            // instant-placement hit tests return empty. This is approximate:
            // neither the floor position nor the model scale is measured.
            Pose estimate=camera.getPose().compose(Pose.makeTranslation(0f,-.40f,-1.30f));
            float[] xyz=estimate.getTranslation();
            Pose upright=new Pose(xyz,new float[]{0f,0f,0f,1f});
            Anchor next=session.createAnchor(upright);
            Item it=items.get(selected);
            if(it.anchor!=null)it.anchor.detach();
            it.anchor=next;it.provisional=true;
            it.dx=it.dz=it.yaw=0f;
            approximateCount++;lastPlacementMode="CAMERA_RELATIVE_APPROXIMATE_"+origin;
            warn("🟠 임시 위치에 가구를 표시했습니다. 바닥·거리 인식이 아니며 실제 위치와 크기가 다를 수 있습니다.");
            Log.i("RoomFitAR","Approximate furniture placement: "+it.name+" source="+origin);
        }''')
replace('''                PointF point=tap;
                tap=null;
                if(point!=null){
                    HitResult selectedHit=null;
                    for(HitResult hit:frame.hitTest(point.x,point.y)){''',
'''                // Button path does not depend on a touch event reaching GLSurfaceView.
                boolean placeNow=quickPlaceRequested;
                quickPlaceRequested=false;
                if(placeNow)placeApproximatelyInFront(camera,"BUTTON");
                PointF point=tap;
                tap=null;
                if(point!=null){
                    tapsProcessed++;
                    float sx=point.x*width,sy=point.y*height;
                    HitResult selectedHit=null;
                    for(HitResult hit:frame.hitTest(sx,sy)){''')
replace('''                        if(t instanceof Plane&&((Plane)t).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)t).isPoseInPolygon(hit.getHitPose())){
                            selectedHit=hit;break;
                        }''',
'''                        if(t instanceof Plane&&((Plane)t).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)t).isPoseInPolygon(hit.getHitPose())){
                            selectedHit=hit;planeHitCount++;lastPlacementMode="TRACKED_PLANE";break;
                        }''')
replace('''                        List<HitResult> approx=frame.hitTestInstantPlacement(point.x,point.y,1.2f);
                        if(!approx.isEmpty()){selectedHit=approx.get(0);provisional=true;}''',
'''                        List<HitResult> approx=frame.hitTestInstantPlacement(sx,sy,1.2f);
                        if(!approx.isEmpty()){selectedHit=approx.get(0);provisional=true;instantHitCount++;lastPlacementMode="INSTANT_PLACEMENT";}''')
replace('''                    }else warn("바닥 위치 인식 실패 · 밝은 바닥을 비춘 뒤 다시 터치하세요.");''',
'''                    }else{
                        // No features/planes yet: show the selected furniture anyway
                        // as a clearly labeled, non-measured reference preview.
                        placeApproximatelyInFront(camera,"TAP");
                    }''')
replace('''                    if(it.anchor==null||it.anchor.getTrackingState()!=TrackingState.TRACKING)continue;''',
'''                    if(it.anchor==null||it.anchor.getTrackingState()==TrackingState.STOPPED)continue;''')
replace('''                String message=System.currentTimeMillis()<warningUntil?placementWarning:"가구를 선택한 뒤 바닥을 터치하세요.";''',
'''                boolean anyApproximate=false;
                for(Item it:items)if(it.anchor!=null&&it.provisional)anyApproximate=true;
                String message=System.currentTimeMillis()<warningUntil?placementWarning:
                    anyApproximate?"🟠 임시 AR 미리보기 · 바닥·거리 위치 확인되지 않음":
                    "가구 선택 후 바닥 터치 · 실패하면 '가구 바로 표시'를 누르세요.";''')
replace('''meta.put("roomfitVersion","3.6.0");''',
'''meta.put("roomfitVersion","3.7.0");''')
replace('''meta.put("depthVerdict","NOT_CHECKED");''',
'''meta.put("depthVerdict","NOT_CHECKED");boolean provisional=false;for(Item placedItem:items)if(placedItem.provisional)provisional=true;meta.put("placementApproximate",provisional);meta.put("placementAccuracyWarning","Camera-relative or instant placement is not a measured floor pose; actual size and clearance unverified.");''')
p.write_text(s,encoding="utf-8")
build=root/"app/build.gradle";b=build.read_text(encoding="utf-8")
b=re.sub(r"\bversionCode\s+\d+","versionCode 370",b)
b=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]","versionName '3.7.0'",b)
build.write_text(b,encoding="utf-8")
manifest=root/"app/src/main/AndroidManifest.xml";m=manifest.read_text(encoding="utf-8")
m=re.sub(r'android:versionCode="\d+"','android:versionCode="370"',m)
m=re.sub(r'android:versionName="[^"]+"','android:versionName="3.7.0"',m)
manifest.write_text(m,encoding="utf-8")
print("RoomFit 3.7 tap+button fallback patch applied; accuracy warning preserved.")
