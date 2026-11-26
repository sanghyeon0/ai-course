from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(path,fn):
 p=root/path
 p.write_text(fn(p.read_text(encoding='utf-8')),encoding='utf-8')
def sub(s,a,b):
 assert a in s,a[:100]
 return s.replace(a,b,1)
def js(s):
 s=sub(s,'window.roomfitOpenAR=()=>ar(false);','''window.roomfitOpenAR=()=>ar(false);
window.roomfitARScene=()=>JSON.stringify({roomfit3:true,roomfit2:false,items:selected.map(m=>({id:m.id,name:m.name,kind:m.kind||'box',width:Number(m.dimensionsCm[0]),depth:Number(m.dimensionsCm[1]),height:Number(m.dimensionsCm[2]),x:0,z:0,rotation:0})),style:{title:'RoomFit 3.9.4',source:'camera-depth',surface:[.68,.70,.63],fabric:[.73,.77,.70],frame:[.2,.24,.23],gain:[1,1,1]}});''')
 return s.replace('RoomFit 3.9.3','RoomFit 3.9.4')
edit('app/src/main/assets/web/roomfit3.js',js)
def ui(s):
 s=sub(s,'ROOMFIT 3.9.3','ROOMFIT 3.9.4')
 return sub(s,"if(from!==5&&n===5){if(typeof window.roomfitOpenAR==='function')window.roomfitOpenAR();else $('ar-guide').textContent='AR 연결 초기화 실패 · 앱을 다시 실행해주세요.';}","if(from!==5&&n===5){$('ar-guide').textContent='Google AR 실행을 직접 누르세요. 반응이 없으면 상단 AR 직접 실행을 이용하세요.';}")
edit('app/src/main/assets/web/roomfit34-ui.js',ui)
def java(s):
 s=sub(s,'RoomFitAndroid/3.9.3','RoomFitAndroid/3.9.4')
 s=sub(s,'web.getSettings().setDomStorageEnabled(true);','web.getSettings().setDomStorageEnabled(true);\n        web.getSettings().setCacheMode(android.webkit.WebSettings.LOAD_NO_CACHE);')
 s=sub(s,'root.addView(progress,pp);','''root.addView(progress,pp);
        android.widget.Button directAR=new android.widget.Button(this);
        directAR.setText("AR 직접 실행");
        directAR.setTextSize(12);
        directAR.setAllCaps(false);
        directAR.setTextColor(Color.WHITE);
        android.graphics.drawable.GradientDrawable arBg=new android.graphics.drawable.GradientDrawable();
        arBg.setColor(Color.rgb(28,113,76));arBg.setCornerRadius(14*getResources().getDisplayMetrics().density);
        directAR.setBackground(arBg);
        FrameLayout.LayoutParams arButton=new FrameLayout.LayoutParams((int)(116*getResources().getDisplayMetrics().density),(int)(44*getResources().getDisplayMetrics().density),Gravity.TOP|Gravity.END);
        arButton.topMargin=(int)(10*getResources().getDisplayMetrics().density);
        arButton.rightMargin=(int)(12*getResources().getDisplayMetrics().density);
        root.addView(directAR,arButton);
        directAR.setElevation(8*getResources().getDisplayMetrics().density);
        directAR.setOnClickListener(v->showDirectARMenu());''')
 s=s.replace('/roomfit3.html?app=android','/roomfit3.html?app=android&v=394')
 s=sub(s,'runOnUiThread(()->{\n                reportAR("Android AR 요청 수신 완료");','runOnUiThread(()->{\n                toast("AR 버튼 입력 수신 완료");\n                reportAR("Android AR 요청 수신 완료");')
 a=s.index('            if(!modelPath(Uri.parse(model)))')
 b=s.index('    private void reportAR(',a)
 s=s[:a]+'''            if(!modelPath(Uri.parse(model)))throw new IllegalArgumentException("model URL");
            checkModelThenLaunch(model,title,item);
        }catch(Exception e){reportAR("가구 모델 연결 실패: "+e.getClass().getSimpleName());toast("가구 모델 정보를 확인하세요.");}
    }
    private void showDirectARMenu(){
        new AlertDialog.Builder(this).setTitle("AR 직접 실행 · 3.9.4")
            .setItems(new String[]{"선택한 가구 Google AR 실행","Google 공식 호랑이 모델 테스트","선택한 가구 앱 내 AR 실행","Google Play AR 서비스 확인"},(dlg,i)->{
                if(i==0)readSelectedScene(false);
                else if(i==1)openGoogleViewer("https://storage.googleapis.com/ar-answers-in-search-models/static/Tiger/model.glb","Google 공식 테스트 모형");
                else if(i==2)readSelectedScene(true);
                else external(Uri.parse("https://play.google.com/store/apps/details?id=com.google.ar.core"));
            }).setNegativeButton("닫기",null).show();
    }
    private void readSelectedScene(boolean nativeFloor){
        if(web==null)return;
        web.evaluateJavascript("typeof window.roomfitARScene==='function' ? window.roomfitARScene() : null",value->{
            try{
                Object parsed=new org.json.JSONTokener(value==null?"null":value).nextValue();
                if(!(parsed instanceof String))throw new IllegalStateException("WebView 연결 없음");
                String scene=(String)parsed;
                if(scene.length()>32000)throw new IllegalArgumentException("선택 데이터 오류");
                if(new org.json.JSONObject(scene).getJSONArray("items").length()==0){
                    new AlertDialog.Builder(this).setTitle("선택된 가구 없음").setMessage("3단계에서 가구를 선택한 후 다시 시도하세요. 공식 모델 테스트는 가구 선택 없이 가능합니다.").setPositiveButton("확인",null).show();return;
                }
                if(nativeFloor)launchNativeFloorAR(scene);else launchUploadedOriginalAR(scene);
            }catch(Exception e){
                new AlertDialog.Builder(this).setTitle("가구 데이터 연결 실패").setMessage("웹 화면의 가구 선택 정보를 읽지 못했습니다. Google 공식 모델 테스트로 기기 AR부터 확인하세요.").setPositiveButton("확인",null).show();
            }
        });
    }
    private void checkModelThenLaunch(String model,String title,org.json.JSONObject item){
        reportAR("가구 모델 서버 확인 중…");
        final android.app.ProgressDialog progress=android.app.ProgressDialog.show(this,"AR 모델 확인","가구 모델 서버에 연결하고 있습니다.",true,false);
        new Thread(()->{
            String error=null;
            java.net.HttpURLConnection conn=null;
            try{
                conn=(java.net.HttpURLConnection)new java.net.URL(model).openConnection();
                conn.setConnectTimeout(7000);conn.setReadTimeout(7000);
                conn.setInstanceFollowRedirects(false);
                int code=conn.getResponseCode();
                if(code!=200)error="서버 HTTP "+code;
                else try(InputStream in=conn.getInputStream()){
                    byte[] hdr=new byte[4];int off=0,n;
                    while(off<4&&(n=in.read(hdr,off,4-off))>0)off+=n;
                    if(off!=4||hdr[0]!='g'||hdr[1]!='l'||hdr[2]!='T'||hdr[3]!='F')error="응답이 GLB 가구 파일이 아닙니다.";
                }
            }catch(Exception ex){error="모델 서버 연결 실패: "+ex.getClass().getSimpleName();}
            finally{if(conn!=null)conn.disconnect();}
            final String failure=error;
            runOnUiThread(()->{
                if(isFinishing()||isDestroyed())return;
                progress.dismiss();
                if(failure==null){openGoogleViewer(model,title);return;}
                reportAR(failure);
                new AlertDialog.Builder(this).setTitle("Google AR 가구 서버 오류").setMessage(failure+"\\n기기 AR은 공식 모형으로 별도 테스트할 수 있습니다. 선택 가구는 앱 내 AR로도 시도할 수 있습니다.")
                    .setPositiveButton("앱 내 AR",(dlg,which)->{
                        try{
                            org.json.JSONObject sc=new org.json.JSONObject();
                            sc.put("roomfit3",true);sc.put("items",new org.json.JSONArray().put(item));
                            launchNativeFloorAR(sc.toString());
                        }catch(Exception e){toast("앱 내 AR 실행 실패");}
                    })
                    .setNeutralButton("공식 모형 테스트",(dlg,which)->openGoogleViewer("https://storage.googleapis.com/ar-answers-in-search-models/static/Tiger/model.glb","Google 공식 테스트 모형"))
                    .setNegativeButton("닫기",null).show();
            });
        }).start();
    }
    private void openGoogleViewer(String model,String title){
        try{
            Uri viewer=new Uri.Builder().scheme("https").authority("arvr.google.com").path("/scene-viewer/1.0")
                .appendQueryParameter("file",model).appendQueryParameter("mode","ar_only")
                .appendQueryParameter("resizable","false").appendQueryParameter("title",title).build();
            startActivity(new Intent(Intent.ACTION_VIEW,viewer).setPackage("com.google.ar.core").addCategory(Intent.CATEGORY_BROWSABLE));
            reportAR("Google Play AR 서비스 실행 요청 완료 · 모델 표시 여부를 확인하세요.");
        }catch(Exception first){
            try{
                Uri viewer=new Uri.Builder().scheme("https").authority("arvr.google.com").path("/scene-viewer/1.0")
                    .appendQueryParameter("file",model).appendQueryParameter("mode","ar_preferred")
                    .appendQueryParameter("resizable","false").appendQueryParameter("title",title).build();
                startActivity(new Intent(Intent.ACTION_VIEW,viewer).setPackage("com.google.android.googlequicksearchbox").addCategory(Intent.CATEGORY_BROWSABLE));
                reportAR("Google 앱 실행 요청 완료 · 모델 표시 여부를 확인하세요.");
            }catch(Exception second){
                reportAR("Google AR 실행 실패: "+second.getClass().getSimpleName());
                new AlertDialog.Builder(this).setTitle("Google AR 실행 실패")
                    .setMessage("Google 앱과 AR 서비스가 실행 요청을 처리하지 못했습니다. 설치 및 업데이트 상태를 확인하세요.")
                    .setPositiveButton("AR 서비스 확인",(dlg,which)->external(Uri.parse("https://play.google.com/store/apps/details?id=com.google.ar.core")))
                    .setNegativeButton("닫기",null).show();
            }
        }
    }
'''+s[b:]
 return s
edit('app/src/main/java/kr/ac/roomfit/app/MainActivity.java',java)
edit('app/build.gradle',lambda s:sub(sub(s,'versionCode 393','versionCode 394'),"versionName '3.9.3'","versionName '3.9.4'"))
edit('app/src/main/AndroidManifest.xml',lambda s:sub(sub(s,'android:versionCode="393"','android:versionCode="394"'),'android:versionName="3.9.3"','android:versionName="3.9.4"'))
print('RoomFit 3.9.4 native diagnostic menu installed')
