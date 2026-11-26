from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(path,func):
    p=root/path
    p.write_text(func(p.read_text(encoding='utf-8')),encoding='utf-8')
def sub(s,a,b):
    assert a in s, a[:100]
    return s.replace(a,b,1)
def js(s):
    a=s.index('function ar(){')
    b=s.index('function download(){',a)
    s=s[:a]+'''let arAckTimer=null;
window.roomfitARStatus=message=>{clearTimeout(arAckTimer);$('ar-guide').textContent=String(message);};
function ar(nativeFloor=false){
 const status=message=>{$('ar-guide').textContent=message;};
 clearTimeout(arAckTimer);status('AR 버튼 입력 확인 · 실행 준비 중…');
 if(!selected.length){status('가구를 먼저 선택해주세요.');alert('가구를 먼저 선택해주세요.');return;}
 const bridge=window.RoomfitNative;
 const method=nativeFloor?'openNativeFloorAR':'openLockedAR';
 if(!bridge||typeof bridge[method]!=='function'){status('Android AR 연결이 없습니다. 설치된 룸핏 앱에서 실행해주세요.');return;}
 try{
  const items=selected.map(m=>({id:m.id,name:m.name,kind:m.kind||'box',width:Number(m.dimensionsCm[0]),depth:Number(m.dimensionsCm[1]),height:Number(m.dimensionsCm[2]),x:0,z:0,rotation:0}));
  if(items.some(m=>[m.width,m.depth,m.height].some(v=>!Number.isFinite(v)||v<1||v>600)))throw Error('가구 치수 오류');
  const scene={roomfit3:true,roomfit2:false,items,style:{title:'RoomFit 3.9.3',source:'camera-depth',surface:[.68,.70,.63],fabric:[.73,.77,.70],frame:[.2,.24,.23],gain:[1,1,1]},context:{source:'roomfit31-depth-guided',priceMode:'demonstration',selectedCount:items.length}};
  status('Android AR 실행 요청 중…');
  arAckTimer=setTimeout(()=>status('Android 응답 없음 · 앱을 다시 열거나 앱 내 AR 시험판을 눌러주세요.'),5000);
  bridge[method](JSON.stringify(scene));
 }catch(err){clearTimeout(arAckTimer);status('AR 시작 실패: '+(err.message||'알 수 없는 오류'));}
}
window.roomfitOpenAR=()=>ar(false);
'''+s[b:]
    a=s.index("$('open-ar').addEventListener('click',ar)")
    b=s.index("$('save-result').addEventListener",a)
    return s[:a]+"$('open-ar').addEventListener('click',()=>ar(false));$('open-native-floor-ar').addEventListener('click',()=>ar(true));"+s[b:]
edit('app/src/main/assets/web/roomfit3.js',js)
def ui(s):
    s=sub(s,'ROOMFIT 3.9.1','ROOMFIT 3.9.3')
    s=sub(s,'if(n===4)step3d.hidden=false;','step3d.hidden=n!==4;')
    s=sub(s,"if(from===4&&n===5&&window.RoomfitNative?.openLockedAR){$('open-ar')?.click();}","if(from!==5&&n===5){if(typeof window.roomfitOpenAR==='function')window.roomfitOpenAR();else $('ar-guide').textContent='AR 연결 초기화 실패 · 앱을 다시 실행해주세요.';}")
    return s
edit('app/src/main/assets/web/roomfit34-ui.js',ui)
def html(s):
    s=sub(s,'<button id="open-ar" class="primary full">앱 안에서 가구 AR로 띄우기</button>','<button id="open-ar" type="button" class="primary full">Google AR 실행</button>')
    s=sub(s,'<button id="open-native-floor-ar" class="soft full" type="button" style="display:none">AR 카메라 다시 열기</button>','<button id="open-native-floor-ar" class="soft full" type="button">앱 내 AR 시험판 (대체 경로)</button>')
    return sub(s,'<p id="ar-guide" class="fine">','<p id="ar-guide" class="fine" role="status" aria-live="polite">')
edit('app/src/main/assets/web/roomfit3.html',html)
def java(s):
    s=sub(s,'RoomFitAndroid/3.9.2','RoomFitAndroid/3.9.3')
    s=sub(s,'if(arr.length()==0){toast("선택한 가구가 없습니다.");return;}','if(arr.length()==0){reportAR("선택한 가구가 없습니다.");toast("선택한 가구가 없습니다.");return;}')
    s=sub(s,'final String[] names=new String[arr.length()];','reportAR("AR로 볼 가구를 선택하세요.");\n            final String[] names=new String[arr.length()];')
    s=sub(s,'catch(Exception e){toast("가구 모델을 준비하지 못했어요.");}','catch(Exception e){reportAR("가구 모델 준비 실패: "+e.getClass().getSimpleName());toast("가구 모델을 준비하지 못했어요.");}')
    s=sub(s,'}).setNegativeButton("취소",null).show();\n        }catch(Exception e){toast("원본 AR 실행 오류: "+e.getClass().getSimpleName());}', '}).setNegativeButton("취소",(dlg,which)->reportAR("가구 선택이 취소되었습니다.")).setOnCancelListener(dlg->reportAR("가구 선택이 취소되었습니다.")).show();\n        }catch(Exception e){reportAR("원본 AR 실행 오류: "+e.getClass().getSimpleName());toast("원본 AR 실행 오류");}')
    s=sub(s,'{toast("가구 크기 정보가 올바르지 않습니다.");return;}','{reportAR("가구 크기 정보가 올바르지 않습니다.");toast("가구 크기 정보가 올바르지 않습니다.");return;}')
    a=s.index('            // Exact original JS intent shape')
    b=s.index('    private void launchNativeFloorAR',a)
    s=s[:a]+'''            if(!modelPath(Uri.parse(model)))throw new IllegalArgumentException("model URL");
            Uri viewer=new Uri.Builder().scheme("https").authority("arvr.google.com")
                .path("/scene-viewer/1.0").appendQueryParameter("file",model)
                .appendQueryParameter("mode","ar_preferred").appendQueryParameter("resizable","false")
                .appendQueryParameter("title",title).build();
            try {
                startActivity(new Intent(Intent.ACTION_VIEW,viewer).setPackage("com.google.android.googlequicksearchbox"));
                reportAR("Google 뷰어 실행 요청 완료 · 모델 로딩 성공 여부는 AR 화면에서 확인하세요.");
            }catch(android.content.ActivityNotFoundException | SecurityException first){
                Uri arViewer=new Uri.Builder().scheme("https").authority("arvr.google.com")
                    .path("/scene-viewer/1.0").appendQueryParameter("file",model)
                    .appendQueryParameter("mode","ar_only").appendQueryParameter("resizable","false")
                    .appendQueryParameter("title",title).build();
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW,arViewer).setPackage("com.google.ar.core"));
                    reportAR("ARCore 뷰어 실행 요청 완료 · 화면에서 모델을 확인하세요.");
                }catch(android.content.ActivityNotFoundException | SecurityException second){
                    reportAR("Google AR 뷰어 실행 실패 · Google 앱과 Google Play AR 서비스를 확인하세요.");
                    new AlertDialog.Builder(this).setTitle("Google AR 실행 실패")
                        .setMessage("두 Google AR 실행 경로를 열 수 없습니다. 앱 내 AR 시험판을 사용하거나 Google Play AR 서비스를 확인하세요.")
                        .setPositiveButton("AR 서비스 확인",(dlg,which)->external(Uri.parse("https://play.google.com/store/apps/details?id=com.google.ar.core")))
                        .setNegativeButton("닫기",null).show();
                }
            }
        }catch(Exception e){reportAR("원본 AR 모델 연결 실패: "+e.getClass().getSimpleName());toast("가구 모델 정보를 확인하세요.");}
    }
    private void reportAR(String message){
        android.util.Log.i("RoomFitAR",message);
        if(web!=null)web.evaluateJavascript("window.roomfitARStatus && window.roomfitARStatus("+org.json.JSONObject.quote(message)+")",null);
    }

'''+s[b:]
    s=sub(s,'if(scene==null||scene.length()>32000)return;\n            runOnUiThread(()->launchUploadedOriginalAR(scene));','runOnUiThread(()->{\n                reportAR("Android AR 요청 수신 완료");\n                if(scene==null||scene.length()>32000){reportAR("AR 가구 데이터가 올바르지 않습니다.");return;}\n                launchUploadedOriginalAR(scene);\n            });')
    s=sub(s,'try {new org.json.JSONObject(scene);launchNativeFloorAR(scene);}','try {reportAR("앱 내 AR 시험판 실행 요청");new org.json.JSONObject(scene);launchNativeFloorAR(scene);}')
    return s
edit('app/src/main/java/kr/ac/roomfit/app/MainActivity.java',java)
edit('app/build.gradle',lambda s:sub(sub(s,'versionCode 392','versionCode 393'),"versionName '3.9.2'","versionName '3.9.3'"))
edit('app/src/main/AndroidManifest.xml',lambda s:sub(sub(s,'android:versionCode="392"','android:versionCode="393"'),'android:versionName="3.9.2"','android:versionName="3.9.3"'))
print('RoomFit 3.9.3 patch applied')
