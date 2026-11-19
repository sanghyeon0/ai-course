#!/usr/bin/env python3
"""RoomFit 3.2.1: render provisional AR furniture even when Depth is uncertain."""
from pathlib import Path
import sys

p=Path(sys.argv[1])/"app/src/main/java/kr/ac/roomfit/app/LockedArActivity.java"
s=p.read_text(encoding="utf-8")
assert "RoomFit 3.2" not in s and "private boolean validPlacement(" in s
s=s.replace("import android.opengl.Matrix;","import android.opengl.Matrix;\nimport android.util.Log;",1)
a=s.index("        private boolean validPlacement(")
b=s.index("        private void handleTransform(",a)
s=s[:a]+'''        private boolean validPlacement(Frame frame,Camera camera,Pose pose,Item item,float yaw){
            if(footprintConflict(pose,item,yaw)){
                warn("🔴 다른 AR 가구와 겹칩니다. 위치를 바꿔주세요.");
                return false;
            }
            // A preview must remain visible while coverage is being scanned.
            // BLOCKED and UNKNOWN are not approvals: shooting remains disabled.
            boolean floorVerified=!roomfit3Mode||onObservedFloor(pose,item,yaw);
            if(depthSupported){
                DepthPlacementChecker.Result check=DepthPlacementChecker.inspect(frame,camera,yawPose(pose,yaw),item.width,item.depth,item.height,width,height);
                lastDepthVerdict=check.verdict;
                depthBlocked=check.verdict==ObstacleMath.Verdict.BLOCKED?1:0;
                depthUnknown=(!floorVerified||check.verdict==ObstacleMath.Verdict.UNKNOWN)?1:0;
                if(check.verdict==ObstacleMath.Verdict.BLOCKED)
                    warn("🔴 장애물 겹침 가능성 · 가구는 미리보기만 표시됩니다.");
                else if(!floorVerified||check.verdict!=ObstacleMath.Verdict.CLEAR)
                    warn("🟠 인식 정보 부족 · 가구 미리보기 표시, 촬영은 제한됩니다.");
                else warn("🟢 가구 미리보기 배치 · 주변 공간을 직접 확인하세요.");
            }else{
                lastDepthVerdict=ObstacleMath.Verdict.UNSUPPORTED;
                warn(!floorVerified?"🟠 미확인 바닥 위치 · 가구 미리보기입니다.":"🟠 Depth 미지원 · 장애물 검사 없는 미리보기입니다.");
            }
            return true;
        }
'''+s[b:]
old='''                if(it.anchor==null || it.anchor.getTrackingState()!=TrackingState.TRACKING)continue;
                DepthPlacementChecker.Result result=DepthPlacementChecker.inspect('''
new='''                if(it.anchor==null || it.anchor.getTrackingState()!=TrackingState.TRACKING)continue;
                if(!onObservedFloor(placedPose(it),it,it.yaw)){unknown++;continue;}
                DepthPlacementChecker.Result result=DepthPlacementChecker.inspect('''
assert old in s
s=s.replace(old,new,1)
old='''                                    if(!fitsObservedFloor((Plane)track,hit.getHitPose(),item,.02f)){
                                        warn("🟠 감지된 바닥 경계를 벗어납니다. 가구 전체가 바닥 안에 들어오도록 이동해주세요.");break;
                                    }
                                    if(!validPlacement(frame,camera,hit.getHitPose(),item,item.yaw))break;'''
assert old in s
s=s.replace(old,'''                                    // A floor hit is sufficient for a provisional preview.
                                    // Full footprint and Depth are checked before capture.
                                    if(!validPlacement(frame,camera,hit.getHitPose(),item,item.yaw))break;''',1)
old='''                        drawFootprint(placedPose(selectedItem),selectedItem,new float[]{.21f,.83f,.52f});'''
assert old in s
s=s.replace(old,'''                        drawFootprint(placedPose(selectedItem),selectedItem,
                            lastDepthVerdict==ObstacleMath.Verdict.BLOCKED?new float[]{.98f,.22f,.22f}:
                            lastDepthVerdict==ObstacleMath.Verdict.UNKNOWN?new float[]{.98f,.65f,.17f}:new float[]{.21f,.83f,.52f});''',1)
old='''        private void drawItem(Item it,float[] transform,float light){if(it.mesh!=null){it.mesh.draw(pv,transform,it.width,light);return;}float[] white='''
assert old in s
s=s.replace(old,'''        private void drawItem(Item it,float[] transform,float light){if(it.mesh!=null){try{it.mesh.draw(pv,transform,it.width,light);return;}catch(RuntimeException ex){Log.e("RoomFitAR","3D model rendering failed for "+it.name,ex);it.mesh=null;it.modelFailed=true;}}float[] white=''',1)
old='''            }catch(Exception ex){captureRequested=false;updateStatus("AR 상태: "+ex.getClass().getSimpleName()+" · 화면을 천천히 움직여주세요.",false);}'''
assert old in s
s=s.replace(old,'''            }catch(Exception ex){Log.e("RoomFitAR","AR frame failed",ex);captureRequested=false;updateStatus("AR 상태: "+ex.getClass().getSimpleName()+" · 화면을 천천히 움직여주세요.",false);}''',1)
p.write_text(s,encoding="utf-8")
print("Applied RoomFit 3.2.1 provisional AR preview fix",p)
