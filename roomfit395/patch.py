from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(path,fn):
 p=root/path
 p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
def sub(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b,1)
def ar(s):
 s=sub(s,'import com.google.ar.core.HitResult;','import com.google.ar.core.HitResult;\nimport com.google.ar.core.InstantPlacementPoint;')
 s=sub(s,'룸핏 3.9.1 · 기본 가구 AR','룸핏 3.9.5 · 내부 가구 AR')
 s=sub(s,'밝은 바닥을 비추고 터치하세요. 바닥을 못 찾으면 추적된 특징점에 가구를 고정합니다.','미리보기는 화면 기준입니다. 밝은 바닥을 비추고 눌러 실제 공간에 고정하세요.')
 s=sub(s,'place.setText("가구 놓기 / 위치 다시 지정");','place.setText("바닥에 가구 놓기 / 다시 배치");')
 s=sub(s,'bottom.addView(place);','''bottom.addView(place);
        Button reset = new Button(this);
        reset.setText("화면 미리보기로 돌아가기");
        reset.setOnClickListener(v -> surface.queueEvent(() -> {renderer.releaseAnchor();renderer.spawnRequested=false;renderer.tap=null;}));
        bottom.addView(reset);''')
 s=sub(s,'cfg.setDepthMode(Config.DepthMode.DISABLED);','cfg.setDepthMode(Config.DepthMode.DISABLED);\n                cfg.setInstantPlacementMode(Config.InstantPlacementMode.LOCAL_Y_UP);')
 s=sub(s,'private boolean pointAnchored=false;','private boolean pointAnchored=false;\n        private InstantPlacementPoint instantPoint;')
 s=sub(s,'previewPose = null;\n            pointAnchored = false;','previewPose = null;\n            pointAnchored = false;\n            instantPoint=null;')
 s=sub(s,'report("AR 카메라 추적 대기 ("+camera.getTrackingState()+"/"+camera.getTrackingFailureReason()+") · 밝은 바닥을 천천히 비춰주세요.");','drawScreenPreview();\n                    report("화면 미리보기 · 공간 고정 아님 · 추적 대기 ("+camera.getTrackingFailureReason()+")");')
 s=sub(s,'HitResult chosen=floor!=null?floor:feature;','''HitResult chosen=floor!=null?floor:feature;
                    InstantPlacementPoint approximate=null;
                    if(chosen==null){
                        try{
                            for(HitResult hit:frame.hitTestInstantPlacement(sx,sy,1.8f)){
                                if(hit.getTrackable() instanceof InstantPlacementPoint && hit.getTrackable().getTrackingState()==TrackingState.TRACKING){
                                    chosen=hit;approximate=(InstantPlacementPoint)hit.getTrackable();break;
                                }
                            }
                        }catch(Exception ex){Log.w(TAG,"Instant placement not ready",ex);}
                    }''')
 s=sub(s,'setAnchor(chosen.createAnchor(),pointMode);\n                            anchorKind=pointMode?', 'setAnchor(chosen.createAnchor(),pointMode);\n                            instantPoint=approximate;\n                            anchorKind=approximate!=null?"빠른 배치 · 거리 추정":pointMode?')
 s=sub(s,'placementInfo=pointMode?','placementInfo=approximate!=null?"빠른 배치 · 거리 및 바닥 높이는 추정값입니다.":pointMode?')
 s=sub(s,'String msg=System.currentTimeMillis()<placementInfoUntil?placementInfo:\n                        anchorKind+" · 카메라를 움직여 위치를 확인하세요 · 가구 크기는 참고용";','''String msg=instantPoint!=null?
                        "빠른 배치 · "+(instantPoint.getTrackingMethod()==InstantPlacementPoint.TrackingMethod.FULL_TRACKING?"3D 추적 전환됨":"거리 추정 중")+" · 바닥 확인 필요":
                        System.currentTimeMillis()<placementInfoUntil?placementInfo:
                        anchorKind+" · 카메라를 움직여 위치를 확인하세요 · 가구 크기는 참고용";''')
 s=sub(s,'report("AR Anchor 추적 대기 · 가구가 잠시 보이지 않습니다. 휴대폰을 움직여주세요.");','drawScreenPreview();\n                    report("화면 미리보기 · 공간 고정 추적 대기 · 다시 배치하세요.");')
 s=sub(s,'String msg=System.currentTimeMillis()<placementInfoUntil?placementInfo:\n                        "AR 추적 정상 · 바닥을 터치하거나 \'가구 놓기\'를 눌러주세요 ("+framesTracked+"프레임)";','''drawScreenPreview();
                    String msg=System.currentTimeMillis()<placementInfoUntil?"화면 미리보기 · "+placementInfo:
                        "화면 미리보기 (공간 고정 아님) · 바닥을 비추고 가구 놓기를 누르세요.";''')
 a=s.index('        private void drawFurniture(Furniture item) {')
 b=s.index('            // A recognizable table/chair/lamp fallback',a)
 s=s[:a]+'''        private void drawScreenPreview(){
            Furniture item=furniture.get(selected);
            // Camera-space diagnostic only. No world position or floor accuracy claimed.
            Matrix.perspectiveM(pv,0,53f,(float)width/height,.05f,40f);
            Matrix.setIdentityM(base,0);
            float extent=Math.max(item.height,Math.max(item.width,item.depth));
            float scale=.8f/Math.max(.1f,extent);
            Matrix.translateM(base,0,0,-item.height*scale*.5f,-2.6f);
            Matrix.rotateM(base,0,18f,0,1,0);
            Matrix.scaleM(base,0,scale,scale,scale);
            GLES20.glClear(GLES20.GL_DEPTH_BUFFER_BIT);
            GLES20.glEnable(GLES20.GL_DEPTH_TEST);
            GLES20.glDepthMask(true);
            drawFurniture(item);
        }
        private void drawFurniture(Furniture item) {
            // Always use the built-in geometry: no external GLB, textures or asset loader.
            GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);
            GLES20.glDisable(GLES20.GL_CULL_FACE);
            GLES20.glDisable(GLES20.GL_BLEND);
            GLES20.glDepthMask(true);
'''+s[b:]
 s=sub(s,'GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 36);\n                GLES20.glDisableVertexAttribArray(pos);','GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 36);\n                GLES20.glDisableVertexAttribArray(pos);\n                int err=GLES20.glGetError();\n                if(err!=GLES20.GL_NO_ERROR){Log.e(TAG,"Furniture GL error "+err);throw new IllegalStateException("GL "+err);}')
 return s
edit('app/src/main/java/kr/ac/roomfit/app/SimpleFurnitureArActivity.java',ar)
def main(s):
 s=s.replace('RoomFitAndroid/3.9.4','RoomFitAndroid/3.9.5').replace('AR 직접 실행 · 3.9.4','AR 직접 실행 · 3.9.5').replace('&v=394','&v=395')
 return s
edit('app/src/main/java/kr/ac/roomfit/app/MainActivity.java',main)
def js(s):
 return s.replace('RoomFit 3.9.4','RoomFit 3.9.5').replace("window.roomfitOpenAR=()=>ar(false);","window.roomfitOpenAR=()=>ar(true);").replace("$('open-ar').addEventListener('click',()=>ar(false));$('open-native-floor-ar').addEventListener('click',()=>ar(true));","$('open-ar').addEventListener('click',()=>ar(true));$('open-native-floor-ar').addEventListener('click',()=>ar(false));")
edit('app/src/main/assets/web/roomfit3.js',js)
def ui(s):
 return s.replace('ROOMFIT 3.9.4','ROOMFIT 3.9.5').replace('Google AR 실행을 직접 누르세요. 반응이 없으면 상단 AR 직접 실행을 이용하세요.','룸핏 내부 AR 실행을 누르세요. 가구 미리보기와 실제 공간 고정을 구분합니다.')
edit('app/src/main/assets/web/roomfit34-ui.js',ui)
def html(s):
 return s.replace('>Google AR 실행</button>','>룸핏 내부 AR 실행</button>').replace('>앱 내 AR 시험판 (대체 경로)</button>','>Google AR (선택 테스트)</button>').replace('휴대폰 카메라가 바닥이나 특징점을 인식하면 가구를 그 위치에 고정합니다. 실제 치수는 확인하세요.','가구 기본 모형을 화면에 표시하고, 바닥 또는 특징점을 인식하면 공간에 고정합니다. 화면 미리보기는 실제 배치가 아닙니다.')
edit('app/src/main/assets/web/roomfit3.html',html)
edit('app/build.gradle',lambda s:sub(sub(s,'versionCode 394','versionCode 395'),"versionName '3.9.4'","versionName '3.9.5'"))
edit('app/src/main/AndroidManifest.xml',lambda s:sub(sub(s,'android:versionCode="394"','android:versionCode="395"'),'android:versionName="3.9.4"','android:versionName="3.9.5"'))
print('RoomFit 3.9.5 native preview and anchored placement applied')
