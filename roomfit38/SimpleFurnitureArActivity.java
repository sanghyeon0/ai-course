package kr.ac.roomfit.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.PointF;
import android.opengl.GLES11Ext;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.opengl.Matrix;
import android.os.Bundle;
import android.util.Log;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.View;
import android.view.WindowManager;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.google.ar.core.Anchor;
import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.Config;
import com.google.ar.core.Coordinates2d;
import com.google.ar.core.Frame;
import com.google.ar.core.HitResult;
import com.google.ar.core.Plane;
import com.google.ar.core.Pose;
import com.google.ar.core.Session;
import com.google.ar.core.Trackable;
import com.google.ar.core.TrackingState;

import org.json.JSONArray;
import org.json.JSONObject;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.FloatBuffer;
import java.util.ArrayList;
import java.util.List;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** Minimal ARCore furniture renderer: one item, one anchor, no Depth, scanning, AI or obstacle rules. */
public final class SimpleFurnitureArActivity extends Activity {
    private static final String TAG = "RoomFitBasicAR";
    private final ArrayList<Furniture> furniture = new ArrayList<>();
    private GLSurfaceView surface;
    private Renderer renderer;
    private TextView status, description;
    private Session session;
    private boolean installRequested = false, surfaceRunning = false, permissionRequested = false;
    private int resumeGeneration = 0;

    private static class Furniture {
        final String id, name, kind;
        final float width, depth, height;
        ProductAssetStore.Entry asset;
        GlbRenderer mesh;
        Furniture(JSONObject p) {
            id = p.optString("id", "");
            name = p.optString("name", "가구");
            kind = p.optString("kind", "table");
            width = (float) p.optDouble("width", 60) / 100f;
            depth = (float) p.optDouble("depth", 60) / 100f;
            height = (float) p.optDouble("height", 60) / 100f;
        }
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        try {
            String raw = getIntent().getStringExtra("scene");
            if (raw == null || raw.length() > 32000) throw new Exception("scene missing");
            JSONArray selected = new JSONObject(raw).getJSONArray("items");
            if (selected.length() < 1 || selected.length() > 12) throw new Exception("no items");
            ProductAssetStore store = new ProductAssetStore(this);
            for (int i = 0; i < selected.length(); i++) {
                Furniture f = new Furniture(selected.getJSONObject(i));
                if (!(f.width > 0 && f.depth > 0 && f.height > 0) ||
                    f.width > 6 || f.depth > 6 || f.height > 6) throw new Exception("dimension");
                try { f.asset = store.load(f.id); }
                catch (Exception ignored) { Log.w(TAG, "Could not load optional model " + f.id); }
                furniture.add(f);
            }
        } catch (Exception ex) {
            new AlertDialog.Builder(this).setMessage("가구 정보를 불러오지 못했습니다. 3단계에서 가구를 선택해 주세요.")
                .setPositiveButton("닫기", (d, which) -> finish()).show();
            return;
        }
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        root.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        setContentView(root);

        surface = new GLSurfaceView(this);
        surface.setEGLContextClientVersion(2);
        surface.setEGLConfigChooser(8, 8, 8, 8, 16, 0);
        surface.setPreserveEGLContextOnPause(true);
        renderer = new Renderer();
        surface.setRenderer(renderer);
        root.addView(surface, new FrameLayout.LayoutParams(-1, -1));
        surface.setOnTouchListener((v, e) -> {
            if (e.getActionMasked() == MotionEvent.ACTION_UP) {
                float x = e.getX() / Math.max(1f, v.getWidth());
                float y = e.getY() / Math.max(1f, v.getHeight());
                renderer.tap = new PointF(Math.min(1, Math.max(0, x)), Math.min(1, Math.max(0, y)));
            }
            return true;
        });

        LinearLayout top = new LinearLayout(this);
        top.setOrientation(LinearLayout.VERTICAL);
        top.setPadding(dp(16), dp(12), dp(16), dp(12));
        top.setBackgroundColor(0xe31e4536);
        TextView title = new TextView(this);
        title.setText("룸핏 3.8 · 기본 가구 AR");
        title.setTextSize(18);
        title.setTextColor(Color.WHITE);
        top.addView(title);
        status = new TextView(this);
        status.setText("AR 카메라를 시작합니다…");
        status.setTextColor(0xffe0f3e7);status.setTextSize(12);
        top.addView(status);
        root.addView(top, new FrameLayout.LayoutParams(-1, -2, Gravity.TOP));

        LinearLayout bottom = new LinearLayout(this);
        bottom.setOrientation(LinearLayout.VERTICAL);
        bottom.setPadding(dp(12), dp(8), dp(12), dp(12));
        bottom.setBackgroundColor(0xf7f8f8f6);
        Spinner chooser = new Spinner(this);
        ArrayList<String> names = new ArrayList<>();
        for (Furniture f : furniture) names.add(f.name);
        chooser.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, names));
        chooser.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override public void onNothingSelected(android.widget.AdapterView<?> parent) {}
            @Override public void onItemSelected(android.widget.AdapterView<?> parent, View view, int pos, long id) {
                if (surface != null) surface.queueEvent(() -> renderer.changeSelection(pos));
                showDimensions(pos);
            }
        });
        bottom.addView(chooser);
        description = new TextView(this);
        description.setTextSize(12);
        description.setTextColor(0xff355445);
        description.setPadding(dp(6), dp(8), dp(6), dp(8));
        bottom.addView(description);
        showDimensions(0);
        Button place = new Button(this);
        place.setText("가구 띄우기 / 다시 놓기");
        place.setOnClickListener(v -> surface.queueEvent(() -> renderer.spawnRequested = true));
        bottom.addView(place);
        TextView warning = new TextView(this);
        warning.setText("⚠ AR 표시 위치와 가구 크기는 참고용입니다. 실제 공간에서 직접 확인하세요.");
        warning.setTextSize(11);
        warning.setTextColor(0xff70472d);
        bottom.addView(warning);
        root.addView(bottom, new FrameLayout.LayoutParams(-1, -2, Gravity.BOTTOM));
    }

    private void showDimensions(int pos) {
        if (description == null || pos < 0 || pos >= furniture.size()) return;
        Furniture f = furniture.get(pos);
        description.setText(String.format(java.util.Locale.KOREA,
            "%s · 가로 %.0f × 깊이 %.0f × 높이 %.0f cm", f.name,
            f.width * 100, f.depth * 100, f.height * 100));
    }
    private int dp(int n) { return Math.round(n * getResources().getDisplayMetrics().density); }
    private void updateStatus(String message) {
        if (status != null && !message.equals(status.getText().toString())) runOnUiThread(() -> status.setText(message));
    }

    @Override protected void onResume() {
        super.onResume();
        if (surface == null) return;
        if (checkSelfPermission(Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            if (!permissionRequested) { permissionRequested = true;
                requestPermissions(new String[]{Manifest.permission.CAMERA}, 39); }
            return;
        }
        try {
            if (session == null) {
                if (ArCoreApk.getInstance().requestInstall(this, !installRequested) == ArCoreApk.InstallStatus.INSTALL_REQUESTED) {
                    installRequested = true; return;
                }
                session = new Session(this);
                Config cfg = new Config(session);
                cfg.setPlaneFindingMode(Config.PlaneFindingMode.HORIZONTAL);
                cfg.setDepthMode(Config.DepthMode.DISABLED);
                cfg.setLightEstimationMode(Config.LightEstimationMode.DISABLED);
                session.configure(cfg);
            }
            session.resume();
            resumeGeneration++;
            surface.onResume(); surfaceRunning = true;
        } catch (Exception ex) {
            Log.e(TAG, "ARCore session error", ex);
            new AlertDialog.Builder(this).setTitle("AR 카메라 실행 실패")
                .setMessage(ex.getClass().getSimpleName() + "\nGoogle Play AR 서비스와 카메라 권한을 확인하세요.")
                .setPositiveButton("닫기", (d, which) -> finish()).show();
        }
    }
    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == 39) {
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) recreate();
            else { Toast.makeText(this, "AR 카메라 권한이 필요합니다.", Toast.LENGTH_LONG).show(); finish(); }
        }
    }
    @Override protected void onPause() {
        if (surfaceRunning) { surface.onPause(); surfaceRunning = false; }
        if (session != null) session.pause();
        super.onPause();
    }
    @Override protected void onDestroy() {
        if (session != null) {
            if (renderer != null) renderer.releaseAnchor();
            session.close(); session = null;
        }
        super.onDestroy();
    }

    private final class Renderer implements GLSurfaceView.Renderer {
        private int cameraTexture, backgroundProgram, furnitureProgram, width = 1, height = 1;
        private Session lastSession;
        private int boundGeneration = -1;
        private FloatBuffer quadPosition, quadTex, vertices;
        private Anchor anchor;
        private Pose previewPose;
        private int selected = 0;
        private volatile boolean spawnRequested = false;
        private volatile PointF tap;
        private long lastStatusAt = 0;
        private int lastErrorCode = 0;
        private final float[] view = new float[16], projection = new float[16], pv = new float[16];
        private final float[] model = new float[16], mvp = new float[16], base = new float[16];

        @Override public void onSurfaceCreated(GL10 gl, EGLConfig config) {
            GLES20.glClearColor(0f, 0f, 0f, 1f);
            int[] textures = new int[1];
            GLES20.glGenTextures(1, textures, 0);
            cameraTexture = textures[0];
            GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, cameraTexture);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
            GLES20.glTexParameteri(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
            lastSession = null;
            boundGeneration = -1;
            backgroundProgram = createProgram("attribute vec2 aPos;attribute vec2 aUv;varying vec2 uv;void main(){gl_Position=vec4(aPos,0.,1.);uv=aUv;}",
                "#extension GL_OES_EGL_image_external : require\nprecision mediump float;varying vec2 uv;uniform samplerExternalOES camera;void main(){gl_FragColor=texture2D(camera,uv);}");
            furnitureProgram = createProgram("attribute vec3 aPos;uniform mat4 uMvp;void main(){gl_Position=uMvp*vec4(aPos,1.);}",
                "precision mediump float;uniform vec3 uColor;void main(){gl_FragColor=vec4(uColor,1.);}");
            quadPosition = asBuffer(new float[]{-1,-1,1,-1,-1,1,1,1});
            quadTex = asBuffer(new float[8]);
            vertices = asBuffer(unitCube());
            for (Furniture item : furniture) {
                if (item.asset != null) {
                    try { item.mesh = new GlbRenderer(item.asset.model); }
                    catch (Exception ex) { item.mesh = null; Log.w(TAG, "Mesh init failure " + item.name, ex); }
                }
            }
        }
        @Override public void onSurfaceChanged(GL10 gl, int w, int h) {
            width = Math.max(1, w); height = Math.max(1, h);
            GLES20.glViewport(0, 0, width, height);
        }
        private void changeSelection(int pos) {
            if (pos < 0 || pos >= furniture.size()) return;
            selected = pos; releaseAnchor(); spawnRequested = true;
        }
        private void releaseAnchor() {
            if (anchor != null) { anchor.detach(); anchor = null; }
            previewPose = null;
        }
        @Override public void onDrawFrame(GL10 gl) {
            GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
            Session current = session;
            if (current == null) return;
            try {
                if (current != lastSession || boundGeneration != resumeGeneration) {
                    current.setCameraTextureName(cameraTexture);
                    lastSession = current; boundGeneration = resumeGeneration;
                }
                current.setDisplayGeometry(getWindowManager().getDefaultDisplay().getRotation(), width, height);
                Frame frame = current.update();
                if (frame.getTimestamp() == 0) return;
                drawCamera(frame);
                Camera camera = frame.getCamera();
                if (camera.getTrackingState() != TrackingState.TRACKING) {
                    report("AR 공간 인식 중 · 휴대폰을 천천히 움직여 주세요.");
                    return;
                }
                // Always show a selected item when tracking becomes available.
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
                } else if (anchor == null || requested) setAnchor(estimateAnchor(camera), true);
                camera.getViewMatrix(view, 0);
                camera.getProjectionMatrix(projection, 0, .05f, 40f);
                Matrix.multiplyMM(pv, 0, projection, 0, view, 0);
                GLES20.glClear(GLES20.GL_DEPTH_BUFFER_BIT);
                GLES20.glEnable(GLES20.GL_DEPTH_TEST);
                GLES20.glDepthFunc(GLES20.GL_LEQUAL);
                GLES20.glDepthMask(true);
                GLES20.glDisable(GLES20.GL_CULL_FACE);
                GLES20.glDisable(GLES20.GL_BLEND);
                Pose pose = anchor != null ? anchor.getPose() : previewPose;
                if (pose != null) {
                    pose.toMatrix(base, 0);
                    Furniture item = furniture.get(selected);
                    drawFurniture(item);
                    report("가구 표시 중 · 바닥을 터치하면 위치 변경 (크기는 참고값)");
                }
            } catch (Exception ex) {
                Log.e(TAG, "AR frame failed", ex);
                report("AR 화면 오류: " + ex.getClass().getSimpleName());
            }
        }
        private Anchor estimateAnchor(Camera camera) {
            Furniture f = furniture.get(selected);
            float distance = Math.max(1.1f, Math.min(3.2f, f.width * 2.25f));
            Pose near = camera.getPose().compose(Pose.makeTranslation(0f, -.30f, -distance));
            float[] t = near.getTranslation();
            return session.createAnchor(new Pose(t, new float[]{0,0,0,1}));
        }
        private void setAnchor(Anchor next, boolean approximate) {
            if (anchor != null) anchor.detach();
            anchor = next;
            previewPose = next.getPose();
            report(approximate ? "임시 위치에 가구 표시 · 크기와 바닥 위치는 참고용" :
                "바닥에 가구 배치됨 · 크기는 참고용");
        }
        private void report(String text) {
            long now = System.currentTimeMillis();
            if (now - lastStatusAt > 420) { lastStatusAt = now; updateStatus(text); }
        }
        private void drawCamera(Frame frame) {
            FloatBuffer ndc = quadPosition;
            ndc.position(0); quadTex.position(0);
            frame.transformCoordinates2d(Coordinates2d.OPENGL_NORMALIZED_DEVICE_COORDINATES,
                ndc, Coordinates2d.TEXTURE_NORMALIZED, quadTex);
            quadPosition.position(0); quadTex.position(0);
            GLES20.glDisable(GLES20.GL_DEPTH_TEST); GLES20.glDepthMask(false);
            GLES20.glUseProgram(backgroundProgram);
            int a = GLES20.glGetAttribLocation(backgroundProgram, "aPos");
            int uv = GLES20.glGetAttribLocation(backgroundProgram, "aUv");
            GLES20.glEnableVertexAttribArray(a); GLES20.glEnableVertexAttribArray(uv);
            GLES20.glVertexAttribPointer(a, 2, GLES20.GL_FLOAT, false, 0, quadPosition);
            GLES20.glVertexAttribPointer(uv, 2, GLES20.GL_FLOAT, false, 0, quadTex);
            GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
            GLES20.glBindTexture(GLES11Ext.GL_TEXTURE_EXTERNAL_OES, cameraTexture);
            GLES20.glUniform1i(GLES20.glGetUniformLocation(backgroundProgram, "camera"), 0);
            GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP, 0, 4);
            GLES20.glDisableVertexAttribArray(a); GLES20.glDisableVertexAttribArray(uv);
            GLES20.glDepthMask(true);
        }
        private void drawFurniture(Furniture item) {
            if (item.mesh != null) {
                try { item.mesh.draw(pv, base, item.width, 1f); return; }
                catch (Exception ex) { Log.w(TAG, "GLB draw failed; using schematic model", ex); item.mesh = null; }
            }
            // A recognizable table/chair/lamp fallback (not an empty or invisible primitive).
            for (FurnitureShape.Part part : FurnitureShape.parts(item.kind, item.width, item.depth, item.height)) {
                System.arraycopy(base, 0, model, 0, 16);
                Matrix.translateM(model, 0, part.x, part.y, part.z);
                Matrix.scaleM(model, 0, part.w, part.h, part.d);
                Matrix.multiplyMM(mvp, 0, pv, 0, model, 0);
                GLES20.glUseProgram(furnitureProgram);
                int pos = GLES20.glGetAttribLocation(furnitureProgram, "aPos");
                GLES20.glEnableVertexAttribArray(pos);
                vertices.position(0);
                GLES20.glVertexAttribPointer(pos, 3, GLES20.GL_FLOAT, false, 0, vertices);
                float[] color = part.material == 1 ? new float[]{.87f,.90f,.88f} :
                                part.material == 2 ? new float[]{.27f,.30f,.29f} : new float[]{.43f,.65f,.51f};
                GLES20.glUniform3fv(GLES20.glGetUniformLocation(furnitureProgram,"uColor"), 1, color, 0);
                GLES20.glUniformMatrix4fv(GLES20.glGetUniformLocation(furnitureProgram,"uMvp"), 1, false, mvp, 0);
                GLES20.glDrawArrays(GLES20.GL_TRIANGLES, 0, 36);
                GLES20.glDisableVertexAttribArray(pos);
            }
        }
        private FloatBuffer asBuffer(float[] values) {
            FloatBuffer b = ByteBuffer.allocateDirect(values.length * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            b.put(values); b.position(0); return b;
        }
        private int compile(int type, String code) {
            int shader = GLES20.glCreateShader(type);
            GLES20.glShaderSource(shader, code); GLES20.glCompileShader(shader);
            int[] pass = {0}; GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, pass, 0);
            if (pass[0] == 0) throw new RuntimeException(GLES20.glGetShaderInfoLog(shader));
            return shader;
        }
        private int createProgram(String vertex, String fragment) {
            int program = GLES20.glCreateProgram();
            GLES20.glAttachShader(program, compile(GLES20.GL_VERTEX_SHADER, vertex));
            GLES20.glAttachShader(program, compile(GLES20.GL_FRAGMENT_SHADER, fragment));
            GLES20.glLinkProgram(program);
            int[] pass = {0}; GLES20.glGetProgramiv(program, GLES20.GL_LINK_STATUS, pass, 0);
            if (pass[0] == 0) throw new RuntimeException(GLES20.glGetProgramInfoLog(program));
            return program;
        }
        private float[] unitCube() {
            float[][] p = {{-.5f,-.5f,-.5f},{.5f,-.5f,-.5f},{.5f,.5f,-.5f},{-.5f,.5f,-.5f},
                {-.5f,-.5f,.5f},{.5f,-.5f,.5f},{.5f,.5f,.5f},{-.5f,.5f,.5f}};
            int[] ix = {0,2,1,0,3,2,4,5,6,4,6,7,0,4,7,0,7,3,1,2,6,1,6,5,
                3,7,6,3,6,2,0,1,5,0,5,4};
            float[] a = new float[108]; int out = 0;
            for (int v : ix) for (int j=0;j<3;j++) a[out++] = p[v][j];
            return a;
        }
    }
}