#!/usr/bin/env python3
"""Install the RoomFit 3.3 mobile wizard + navigation without changing AR code."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
web = root / 'app/src/main/assets/web'
h = web / 'roomfit3.html'
s = h.read_text(encoding='utf-8')
assert '<link rel="stylesheet" href="/roomfit3.css">' in s
assert '<script src="/roomfit3.js"></script>' in s
if '/roomfit33-ui.css' not in s:
    s = s.replace('<link rel="stylesheet" href="/roomfit3.css">',
                  '<link rel="stylesheet" href="/roomfit3.css"><link rel="stylesheet" href="/roomfit33-ui.css">')
if '/roomfit33-ui.js' not in s:
    s = s.replace('<script src="/roomfit3.js"></script>',
                  '<script src="/roomfit3.js"></script><script src="/roomfit33-ui.js"></script>')
s = s.replace('<title>룸핏 3.2 |','<title>룸핏 3.3 |')
h.write_text(s, encoding='utf-8')
build = root / 'app/build.gradle'
b = build.read_text(encoding='utf-8')
import re
b = re.sub(r'\bversionCode\s+\d+', 'versionCode 330', b)
b = re.sub(r"\bversionName\s+['\"][^'\"]+['\"]", "versionName '3.3.0'", b)
build.write_text(b,encoding='utf-8')
main=root/'app/src/main/java/kr/ac/roomfit/app/MainActivity.java'
a=main.read_text(encoding='utf-8')
a = re.sub(r'RoomFitAndroid/\d+\.\d+(?:\.\d+)?', 'RoomFitAndroid/3.3.0', a)
main.write_text(a,encoding='utf-8')
for f in ['roomfit33-ui.js','roomfit33-ui.css']:
    assert (web/f).is_file(),f
print('RoomFit 3.3 mobile UI patch installed; original AR source preserved.')