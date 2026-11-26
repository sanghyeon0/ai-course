#!/usr/bin/env python3
"""RoomFit 3.8: replace overloaded AR with one barebones native AR camera."""
from pathlib import Path
import sys,re
root=Path(sys.argv[1])

source=Path(__file__).resolve().parent/'SimpleFurnitureArActivity.java'
target=root/'app/src/main/java/kr/ac/roomfit/app/SimpleFurnitureArActivity.java'
assert source.exists()
target.write_text(source.read_text(encoding='utf-8'),encoding='utf-8')

manifest=root/'app/src/main/AndroidManifest.xml'
s=manifest.read_text(encoding='utf-8')
assert '<activity android:name=".LockedArActivity"' in s
s=s.replace('<activity android:name=".LockedArActivity"',
            '<activity android:name=".SimpleFurnitureArActivity" android:exported="false" android:screenOrientation="portrait"/>\n        <activity android:name=".LockedArActivity"',1)
s=re.sub(r'android:versionCode="\d+"','android:versionCode="380"',s)
s=re.sub(r'android:versionName="[^"]+"','android:versionName="3.8.0"',s)
manifest.write_text(s,encoding='utf-8')

main=root/'app/src/main/java/kr/ac/roomfit/app/MainActivity.java'
s=main.read_text(encoding='utf-8')
old='new Intent(MainActivity.this,LockedArActivity.class).putExtra("scene",scene)'
assert old in s
s=s.replace(old,'new Intent(MainActivity.this,SimpleFurnitureArActivity.class).putExtra("scene",scene)',1)
s=s.replace('RoomFitAndroid/3.3.0','RoomFitAndroid/3.8.0')
main.write_text(s,encoding='utf-8')

web=root/'app/src/main/assets/web/roomfit34-ui.js'
s=web.read_text(encoding='utf-8')
assert "$('step3').appendChild(retry);" in s
s=s.replace("$('step3').appendChild(retry);", "/* Removed additional 3D preview and legacy AR troubleshooting controls. */")
s=s.replace(" $('rf34-back-preview').addEventListener('click',()=>go(4));", "")
s=s.replace("ROOMFIT 3.5","ROOMFIT 3.8")
old="function go(n){closeDrawer();if(n<1||n>6)return;if(n>=4&&n<=5&&choiceCount()===0){alert('3단계에서 먼저 가구를 하나 이상 선택해 주세요.');displayStage(3);return;}displayStage(n);}"
assert old in s
new="""function go(n){closeDrawer();if(n<1||n>6)return;if(n>=4&&n<=5&&choiceCount()===0){alert('3단계에서 먼저 가구를 하나 이상 선택해 주세요.');displayStage(3);return;}const from=current;if(!displayStage(n))return; if(from===4&&n===5&&window.RoomfitNative?.openLockedAR){$('open-ar')?.click();}}"""
s=s.replace(old,new,1)
s=s.replace('카메라나 AR 인식 없이 선택한 가구를 회전·확대할 수 있습니다.','선택한 가구를 3D로 확인하고 다음을 누르면 바로 AR 카메라가 열립니다.')
s=s.replace('5단계 · AR 배치로 이동 →','5단계 · AR 카메라 바로 열기 →')
web.write_text(s,encoding='utf-8')

html=root/'app/src/main/assets/web/roomfit3.html'
s=html.read_text(encoding='utf-8')
a='<section id="step3" class="step" hidden>'
start=s.index(a)
end=s.index('</section>',start)+len('</section>')
section=s[start:end]
section=re.sub(r'<div class="panel"><div class="status-icon">.*?</div><div class="panel">', '<div class="panel">', section, count=1,flags=re.S)
section=section.replace('03 / LIVE CAMERA','05 / BASIC AR')
section=section.replace('카메라로 방을 확인해요.','선택한 가구를 AR로 띄워요.')
section=section.replace('카메라로 바닥을 살피고, 가구를 이동·회전하거나 빈 위치 후보를 찾아보세요.','AR 카메라가 실행되면 선택한 가구가 표시됩니다. 화면을 터치하면 위치를 바꿀 수 있습니다.')
section=section.replace('카메라 AR 실행하기','AR 카메라 다시 열기')
section=section.replace('ARCore 지원 안드로이드 기기에서 실행합니다. Depth 미지원 기기에서는 장애물 검사·빈 공간 후보를 사용할 수 없습니다. 웹 미리보기는 실제 카메라 AR을 지원하지 않습니다.','크기와 배치 위치는 참고용입니다. 장애물 탐지·빈 공간 추천·자동 측정 기능은 없습니다.')
s=s[:start]+section+s[end:]
html.write_text(s,encoding='utf-8')

js=root/'app/src/main/assets/web/roomfit3.js'
s=js.read_text(encoding='utf-8')
s=s.replace('AR 화면에서 바닥을 여러 방향에서 살펴보세요. 가구는 터치로 놓거나 이동하고, 이동·회전 버튼으로 보정할 수 있습니다. 안전 경고를 확인해주세요.','AR 화면에서 선택한 가구가 표시됩니다. 화면을 터치하면 위치를 다시 놓을 수 있습니다. 크기는 참고용입니다.')
js.write_text(s,encoding='utf-8')

build=root/'app/build.gradle'
s=build.read_text(encoding='utf-8')
s=re.sub(r'\bversionCode\s+\d+','versionCode 380',s)
s=re.sub(r"\bversionName\s+['\"][^'\"]+['\"]", "versionName '3.8.0'",s)
build.write_text(s,encoding='utf-8')

print('RoomFit 3.8: minimal native AR, direct 4->5, no duplicate 3D in AR')