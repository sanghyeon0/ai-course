#!/usr/bin/env python3
"""RoomFit 3.5: basic AR tap-to-place + reference-size warning; keep five-stage UI."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1])
p=root/'app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java'
s=p.read_text(encoding='utf-8')
assert '룸핏 3.4 · AR 배치 + 3D 미리보기' in s
assert 'DepthPlacementChecker.inspect(frame' in s

s=s.replace('룸핏 3.4 · AR 배치 + 3D 미리보기','룸핏 3.5 · 간단 AR 배치')
s=s.replace('1. 넓고 밝은 바닥을 비추며 천천히 움직이세요. 2. 화면을 터치해 배치하세요. 인식이 안 되면 「AR 추적 다시 시작」 또는 「3D 미리보기」를 누르세요. 인식되지 않은 장애물은 검사할 수 없습니다.','밝은 바닥을 비추고 터치하면 선택한 가구를 표시합니다. ⚠ 표시된 크기는 참고용으로 실제 가구와 다를 수 있습니다.')
s=s.replace('scanNote.setText("바닥과 거리 정보 탐색 준비 중")','scanNote.setText("⚠ 실측 경고: 표시된 가구 치수는 참고값입니다. 실제 공간을 직접 측정하세요.")')
a=s.index('            LinearLayout quick=new LinearLayout(this);')
b=s.index('        }\n        if(roomfit3Mode){dimensions=',a)
s=s[:a]+'''            Button retry=new Button(this);
            retry.setText("↻ AR 카메라 다시 시작");retry.setTextSize(11);
            retry.setOnClickListener(v->recreate());bottom.addView(retry);
'''+s[b:]
a=s.index('        LinearLayout tools=new LinearLayout(this);')
b=s.index('        if(roomfit2Mode){',a)
s=s[:a]+s[b:]
s=s.replace('가구 선택 → 바닥 터치로 놓기·이동, 방향 버튼으로 15° 회전, 화살표로 5cm 이동, 빈 위치 찾기로 후보 탐색. 위험·불확실한 이동은 차단합니다. 감지 범위 밖은 반드시 직접 확인하세요.','가구를 선택하고 화면을 터치하면 배치됩니다. 거리·장애물 자동 검사 기능은 사용하지 않습니다. 실제 공간과 가구 크기를 직접 측정하세요.')
s=s.replace('controlsLayout=new FrameLayout.LayoutParams(-1,dp(240),Gravity.BOTTOM)','controlsLayout=new FrameLayout.LayoutParams(-1,dp(230),Gravity.BOTTOM)')
s=s.replace('등록 모델 치수 기준이며 실측 오차가 있을 수 있습니다.','⚠ 크기 주의: 등록된 참고 치수이며 실측과 차이날 수 있습니다. 반드시 실제 공간과 가구를 직접 확인하세요.')
s=s.replace('depthSupported=roomfit3Mode&&session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);if(depthSupported)config.setDepthMode(Config.DepthMode.AUTOMATIC);session.configure(config);','depthSupported=false;config.setDepthMode(Config.DepthMode.DISABLED);session.configure(config);')

a=s.index('        @Override public void onDrawFrame(GL10 gl){')
b=s.index('        private void drawBackground(Frame frame)',a)
s=s[:a]+'''        @Override public void onDrawFrame(GL10 gl){
            if(saving)return;
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
            Session active=session;
            if(active==null)return;
            try{
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
                }
                PointF point=tap;
                tap=null;
                if(point!=null){
                    HitResult selectedHit=null;
                    for(HitResult hit:frame.hitTest(point.x,point.y)){
                        Trackable t=hit.getTrackable();
                        if(t instanceof Plane&&((Plane)t).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)t).isPoseInPolygon(hit.getHitPose())){
                            selectedHit=hit;break;
                        }
                    }
                    boolean provisional=false;
                    if(selectedHit==null&&roomfit3Mode){
                        List<HitResult> approx=frame.hitTestInstantPlacement(point.x,point.y,1.2f);
                        if(!approx.isEmpty()){selectedHit=approx.get(0);provisional=true;}
                    }
                    if(selectedHit!=null){
                        Item it=items.get(selected);
                        Anchor next=selectedHit.createAnchor();
                        if(it.anchor!=null)it.anchor.detach();
                        it.anchor=next;it.provisional=provisional;
                        it.dx=it.dz=it.yaw=0;
                        warn(provisional?"임시 가구 배치 · 위치·크기 정확하지 않을 수 있습니다.":"가구 배치됨 · 실제 가구 크기는 직접 확인하세요.");
                    }else warn("바닥 위치 인식 실패 · 밝은 바닥을 비춘 뒤 다시 터치하세요.");
                }
                camera.getViewMatrix(view,0);
                camera.getProjectionMatrix(projection,0,.05f,30);
                Matrix.multiplyMM(pv,0,projection,0,view,0);
                GLES20.glEnable(GLES20.GL_DEPTH_TEST);
                GLES20.glDepthMask(true);
                float light=frame.getLightEstimate().getState()==LightEstimate.State.VALID?
                    clamp(frame.getLightEstimate().getPixelIntensity(),.65f,1.2f):1;
                int count=0;
                for(Item it:items){
                    if(it.anchor==null||it.anchor.getTrackingState()!=TrackingState.TRACKING)continue;
                    count++;it.anchor.getPose().toMatrix(base,0);
                    Matrix.translateM(base,0,it.dx,0,it.dz);
                    Matrix.rotateM(base,0,it.yaw,0,1,0);
                    drawItem(it,base,light);
                }
                boolean ready=count==items.size();
                String message=System.currentTimeMillis()<warningUntil?placementWarning:"가구를 선택한 뒤 바닥을 터치하세요.";
                updateStatus(message+" · "+count+"/"+items.size()+"개 배치 · ⚠ 크기 참고용 (실측 확인 필수)",ready);
                if(captureRequested){
                    captureRequested=false;
                    if(ready){saveFrame(frame,camera);return;}
                    updateStatus("사진을 저장하려면 목록의 가구를 모두 배치하세요. ⚠ 크기는 참고용입니다.",false);
                }
                if(count==0){
                    for(HitResult hit:frame.hitTest(width/2f,height/2f)){
                        Trackable t=hit.getTrackable();
                        if(t instanceof Plane&&((Plane)t).getType()==Plane.Type.HORIZONTAL_UPWARD_FACING&&((Plane)t).isPoseInPolygon(hit.getHitPose())){
                            hit.getHitPose().toMatrix(base,0);
                            drawPart(new FurnitureShape.Part(.10f,.003f,.10f,0,.002f,0,0),base,new float[]{.3f,.8f,.5f},1);
                            break;
                        }
                    }
                }
            }catch(Exception ex){
                Log.e("RoomFitAR","Simple AR frame failed",ex);
                captureRequested=false;
                updateStatus("AR 오류: "+ex.getClass().getSimpleName()+" · 3D 미리보기로 확인할 수 있습니다.",false);
            }
        }
'''+s[b:]
s=s.replace('meta.put("roomfitVersion","3.4.0")','meta.put("roomfitVersion","3.5.0")')
s=s.replace('meta.put("automaticDetectionLimits","visible depth only; not a full-room safety measurement")','meta.put("automaticDetectionLimits","No depth/collision detection. Dimensions are reference only.")')
s=s.replace('meta.put("depthVerdict",roomfit3Mode?lastDepthVerdict.name():"NOT_CHECKED")','meta.put("depthVerdict","NOT_CHECKED")')
assert 'Config.DepthMode.DISABLED' in s
p.write_text(s,encoding='utf-8')

js=root/'app/src/main/assets/web/roomfit34-ui.js'
t=js.read_text(encoding='utf-8')
t=t.replace("'AR 배치'","'간단 AR 배치'",1).replace('ROOMFIT 3.4','ROOMFIT 3.5')
t=t.replace('ARCore가 위치 추적을 시작하지 못하면 가구가 실제 공간에 고정되지 않습니다.','AR에서는 가구 크기 안내만 제공합니다. 장애물 및 거리 자동 검사는 사용하지 않습니다. ARCore가 위치 추적을 시작하지 못하면 가구가 실제 공간에 고정되지 않습니다.')
t=t.replace('AR 공간 인식과 치수·장애물 검사는 정확도를 보장하지 않습니다.','AR에서는 크기 참고 정보만 표시하며 장애물·거리 검사를 하지 않습니다.')
js.write_text(t,encoding='utf-8')

build=root/'app/build.gradle';t=build.read_text(encoding='utf-8')
t=re.sub(r'\bversionCode\s+\d+','versionCode 350',t)
t=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]","versionName '3.5.0'",t)
build.write_text(t,encoding='utf-8')
manifest=root/'app/src/main/AndroidManifest.xml';t=manifest.read_text(encoding='utf-8')
t=re.sub(r'android:versionCode="\d+"','android:versionCode="350"',t)
t=re.sub(r'android:versionName="[^"]+"','android:versionName="3.5.0"',t)
manifest.write_text(t,encoding='utf-8')
print("RoomFit 3.5: 5-step UI retained; simple AR with only size warnings")
