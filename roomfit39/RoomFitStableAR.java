package kr.ac.roomfit.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;

/**
 * Scene Viewer integration adapted from the user's RoomFit-Android (October 2026).
 * Unlike camera-relative fallback anchors, Scene Viewer owns AR plane detection
 * and position stabilization. The model must be publicly hosted HTTPS .glb.
 */
public final class RoomFitStableAR {
    private static final String TAG="RoomFitStableAR";
    private static final String MODELS =
        "https://raw.githubusercontent.com/sanghyeon0/ai-course/roomfit-3.9-floor-anchored-ar/public-models/";
    private RoomFitStableAR(){}

    public static boolean open(Activity activity, String scene, Runnable nativeFallback){
        try{
            JSONArray arr=new JSONObject(scene).getJSONArray("items");
            if(arr.length()==0)throw new IllegalArgumentException("가구를 먼저 선택해 주세요.");
            ArrayList<JSONObject> products=new ArrayList<>();
            ArrayList<String> titles=new ArrayList<>();
            for(int i=0;i<arr.length();i++){
                JSONObject item=arr.getJSONObject(i);
                if(item.optString("id").matches("[a-zA-Z0-9-]{1,80}")){
                    products.add(item);
                    titles.add(item.optString("name","가구 "+(i+1)));
                }
            }
            if(products.isEmpty())throw new IllegalArgumentException("선택한 가구가 없습니다.");
            // The Google Scene Viewer AR app displays one GLB at a time.
            if(products.size()==1){
                launch(activity,products.get(0),nativeFallback);
            }else{
                new AlertDialog.Builder(activity).setTitle("바닥에 고정할 가구 선택")
                    .setItems(titles.toArray(new String[0]),(d,which)->
                        launch(activity,products.get(which),nativeFallback))
                    .setNegativeButton("닫기",null).show();
            }
            return true;
        }catch(Exception ex){
            Log.e(TAG,"Cannot prepare scene",ex);
            Toast.makeText(activity,"가구 AR 실행 준비 오류: "+ex.getClass().getSimpleName(),Toast.LENGTH_LONG).show();
            return false;
        }
    }
    private static String modelFile(Activity activity,String id)throws Exception{
        // Use exactly the GLB asset mapping bundled in the user's RoomFit catalogue.
        try(InputStream input=activity.getAssets().open("web/product-models.json")){
            byte[] bytes=new byte[input.available()];
            int n=0;while(n<bytes.length){int r=input.read(bytes,n,bytes.length-n);if(r<0)break;n+=r;}
            JSONObject catalog=new JSONObject(new String(bytes,0,n,StandardCharsets.UTF_8));
            JSONObject product=catalog.optJSONObject(id);
            if(product==null)throw new IllegalArgumentException("모델 정보 없음: "+id);
            String path=product.optString("url","");
            if(!path.matches("/product-models/[a-z0-9-]+\\.glb"))
                throw new IllegalArgumentException("지원하지 않는 모델 경로");
            return path.substring(path.lastIndexOf('/')+1);
        }
    }
    private static void launch(Activity activity,JSONObject p,Runnable nativeFallback){
        String id=p.optString("id","");
        String name=p.optString("name","룸핏 가구");
        try{
            String asset=modelFile(activity,id);
            String model=MODELS+asset;
            // Google's documented ar_only launch: native Scene Viewer does
            // its own floor detection and anchors the model to a tracked plane.
            Uri data=new Uri.Builder().scheme("https").authority("arvr.google.com")
                .path("/scene-viewer/1.0").appendQueryParameter("file",model)
                .appendQueryParameter("mode","ar_only")
                .appendQueryParameter("resizable","false")
                .appendQueryParameter("title",name.length()>60?name.substring(0,60):name).build();
            // Reproduce the user's older working RoomFit Android app:
            // invoke Google's Scene Viewer through the Google app first.
            Uri preferred=data.buildUpon().clearQuery().appendQueryParameter("file",model)
                .appendQueryParameter("mode","ar_preferred")
                .appendQueryParameter("resizable","false")
                .appendQueryParameter("title",name.length()>60?name.substring(0,60):name).build();
            try{
                activity.startActivity(new Intent(Intent.ACTION_VIEW,preferred)
                    .setPackage("com.google.android.googlequicksearchbox"));
            }catch(ActivityNotFoundException missingGoogleApp){
                // Some devices expose the AR service as the Scene Viewer entry.
                activity.startActivity(new Intent(Intent.ACTION_VIEW,data)
                    .setPackage("com.google.ar.core"));
            }
        }catch(Exception error){
            Log.e(TAG,"Scene Viewer failed",error);
            new AlertDialog.Builder(activity).setTitle("Google AR 뷰어를 열지 못했습니다")
                .setMessage("Google 앱과 Google Play AR 서비스 설치 여부 또는 인터넷 연결을 확인해 주세요. 예전 방식과 동일하게 AR 뷰어가 인터넷에서 GLB 파일을 받아야 합니다.\n\n대신 앱 내부에서 바닥을 인식한 후 가구를 고정할 수 있습니다.")
                .setPositiveButton("앱 내 바닥 고정으로 전환",(d,w)->nativeFallback.run())
                .setNegativeButton("닫기",null).show();
        }
    }
}