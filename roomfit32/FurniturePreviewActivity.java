package kr.ac.roomfit.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** Independent GLB furniture viewer; does not need ARCore tracking or a camera. */
public final class FurniturePreviewActivity extends Activity {
    private GLSurfaceView surface;
    private Viewer renderer;
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setStatusBarColor(0xff16382b);
        String productId=getIntent().getStringExtra("productId");
        String itemName=getIntent().getStringExtra("itemName");
        String kind=getIntent().getStringExtra("kind");
        float w=getIntent().getFloatExtra("width",.5f);
        float d=getIntent().getFloatExtra("depth",.5f);
        float h=getIntent().getFloatExtra("height",.5f);
        if(productId==null)productId="";
        if(kind==null)kind="table";
        if(itemName==null)itemName="가구";
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(0xfff3f5f1);
        setContentView(root);
        TextView title=new TextView(this);
        title.setText("가구 3D 미리보기  ·  카메라 불필요\n"+itemName);
        title.setTextSize(17);title.setTextColor(Color.WHITE);title.setPadding(20,22,16,18);
        title.setBackgroundColor(0xff16382b);root.addView(title);
        renderer=new Viewer(productId,kind,w,d,h);
        surface=new GLSurfaceView(this);
        surface.setEGLContextClientVersion(2);
        surface.setEGLConfigChooser(8,8,8,8,16,0);
        surface.setRenderer(renderer);
        root.addView(surface,new LinearLayout.LayoutParams(-1,0,1));
        TextView help=new TextView(this);
        help.setText(String.format(java.util.Locale.KOREA,"손가락으로 좌우 회전 · 두 손가락 확대/축소\n가로 %.0f × 깊이 %.0f × 높이 %.0f cm · 참고 모델이며 실물과 차이가 있을 수 있습니다.",w*100,d*100,h*100));
        help.setGravity(Gravity.CENTER);help.setTextColor(0xff23543d);help.setPadding(12,12,12,12);
        root.addView(help);
        LinearLayout buttons=new LinearLayout(this);
        Button reset=new Button(this);reset.setText("회전·확대 초기화");reset.setOnClickListener(v->{renderer.yaw=28;renderer.zoom=1;});
        buttons.addView(reset,new LinearLayout.LayoutParams(0,-2,1));
        Button back=new Button(this);back.setText("AR 배치로 돌아가기");back.setOnClickListener(v->finish());
        buttons.addView(back,new LinearLayout.LayoutParams(0,-2,1));root.addView(buttons);
        surface.setOnTouchListener(new View.OnTouchListener(){
            private float lastX,prevDistance;
            @Override public boolean onTouch(View v,MotionEvent e){
                if(e.getPointerCount()>=2){
                    float dx=e.getX(0)-e.getX(1),dy=e.getY(0)-e.getY(1);
                    float dist=(float)Math.hypot(dx,dy);
                    if(e.getActionMasked()==MotionEvent.ACTION_MOVE&&prevDistance>5)
                        renderer.zoom=Math.max(.55f,Math.min(3.8f,renderer.zoom*prevDistance/Math.max(5,dist)));
                    prevDistance=dist;
                }else{
                    if(e.getActionMasked()==MotionEvent.ACTION_MOVE)
                        renderer.yaw+=(e.getX()-lastX)*.6f;
                    prevDistance=0;
                    lastX=e.getX();
                }
                return true;
            }
        });
    }
    @Override protected void onPause(){if(surface!=null)surface.onPause();super.onPause();}
    @Override protected void onResume(){super.onResume();if(surface!=null)surface.onResume();}

    private final class Viewer implements GLSurfaceView.Renderer {
        final String id,kind;
        float w,d,h;volatile float yaw=28f,zoom=1f;
        GlbRenderer mesh;int fallbackProgram;
        FloatBuffer cube;
        final float[] proj=new float[16],view=new float[16],pv=new float[16],base=new float[16],model=new float[16],mvp=new float[16];
        final float[] color={.36f,.65f,.51f};
        Viewer(String id,String kind,float w,float d,float h){this.id=id;this.kind=kind;this.w=w;this.d=d;this.h=h;}
        @Override public void onSurfaceCreated(GL10 gl,EGLConfig config){
            GLES20.glClearColor(.94f,.97f,.94f,1f);
            GLES20.glEnable(GLES20.GL_DEPTH_TEST);
            try{
                ProductAssetStore.Entry entry=new ProductAssetStore(FurniturePreviewActivity.this).load(id);
                if(entry!=null){w=entry.model.width();d=entry.model.depth();h=entry.model.height();mesh=new GlbRenderer(entry.model);}
            }catch(Exception ex){android.util.Log.w("RoomFit3D","Using schematic furniture",ex);mesh=null;}
            fallbackProgram=link(
                "attribute vec3 aPos;uniform mat4 uMvp;void main(){gl_Position=uMvp*vec4(aPos,1.);}",
                "precision mediump float;uniform vec3 uColor;void main(){gl_FragColor=vec4(uColor,1.);}");
            cube=makeCube();
        }
        @Override public void onSurfaceChanged(GL10 gl,int width,int height){
            GLES20.glViewport(0,0,width,height);
            Matrix.perspectiveM(proj,0,45f,Math.max(.01f,(float)width/Math.max(1,height)),.005f,100f);
        }
        @Override public void onDrawFrame(GL10 gl){
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT|GLES20.GL_DEPTH_BUFFER_BIT);
            float radius=Math.max(.18f,Math.max(Math.max(w,d),h));
            float distance=radius*2.4f*zoom;
            Matrix.setLookAtM(view,0, distance*.25f, h*.47f+distance*.37f, distance,
                0,h*.45f,0, 0,1,0);
            Matrix.multiplyMM(pv,0,proj,0,view,0);
            Matrix.setIdentityM(base,0);
            Matrix.rotateM(base,0,yaw,0,1,0);
            if(mesh!=null){
                try {mesh.draw(pv,base,w,1f);return;}
                catch(RuntimeException ex){android.util.Log.e("RoomFit3D","GLB preview failed",ex);mesh=null;}
            }
            for(FurnitureShape.Part part:FurnitureShape.parts(kind,w,d,h)){
                System.arraycopy(base,0,model,0,16);
                Matrix.translateM(model,0,part.x,part.y,part.z);
                Matrix.scaleM(model,0,part.w,part.h,part.d);
                Matrix.multiplyMM(mvp,0,pv,0,model,0);
                GLES20.glUseProgram(fallbackProgram);
                int loc=GLES20.glGetAttribLocation(fallbackProgram,"aPos");
                GLES20.glEnableVertexAttribArray(loc);
                cube.position(0);
                GLES20.glVertexAttribPointer(loc,3,GLES20.GL_FLOAT,false,0,cube);
                GLES20.glUniformMatrix4fv(GLES20.glGetUniformLocation(fallbackProgram,"uMvp"),1,false,mvp,0);
                GLES20.glUniform3fv(GLES20.glGetUniformLocation(fallbackProgram,"uColor"),1,
                    part.material==2?new float[]{.2f,.25f,.24f}:part.material==1?new float[]{.82f,.85f,.82f}:color,0);
                GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,36);
                GLES20.glDisableVertexAttribArray(loc);
            }
        }
        private FloatBuffer makeCube(){
            float[] corners={-.5f,-.5f,-.5f,.5f,-.5f,-.5f,.5f,.5f,-.5f,-.5f,.5f,-.5f,
                            -.5f,-.5f,.5f,.5f,-.5f,.5f,.5f,.5f,.5f,-.5f,.5f,.5f};
            int[] triangles={0,2,1,0,3,2,4,5,6,4,6,7,0,4,7,0,7,3,
                             1,2,6,1,6,5,3,7,6,3,6,2,0,1,5,0,5,4};
            FloatBuffer result=ByteBuffer.allocateDirect(36*3*4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            for(int i:triangles){result.put(corners,i*3,3);}result.position(0);return result;
        }
        private int shader(int type,String src){
            int n=GLES20.glCreateShader(type);GLES20.glShaderSource(n,src);GLES20.glCompileShader(n);
            int[] ok={0};GLES20.glGetShaderiv(n,GLES20.GL_COMPILE_STATUS,ok,0);
            if(ok[0]==0)throw new IllegalStateException(GLES20.glGetShaderInfoLog(n));return n;
        }
        private int link(String vert,String frag){
            int p=GLES20.glCreateProgram();
            GLES20.glAttachShader(p,shader(GLES20.GL_VERTEX_SHADER,vert));
            GLES20.glAttachShader(p,shader(GLES20.GL_FRAGMENT_SHADER,frag));
            GLES20.glLinkProgram(p);int[] ok={0};GLES20.glGetProgramiv(p,GLES20.GL_LINK_STATUS,ok,0);
            if(ok[0]==0)throw new IllegalStateException(GLES20.glGetProgramInfoLog(p));return p;
        }
    }
}
