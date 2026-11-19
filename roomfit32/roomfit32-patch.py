#!/usr/bin/env python3
"""Upgrade an extracted RoomFit 3.1.1 project to RoomFit 3.2.
Usage: python roomfit32-patch.py <android-project-directory>
Changes only WebView assets; AR native Java sources remain unchanged.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
web = root / 'app/src/main/assets/web'
assert (web / 'roomfit3.js').is_file(), 'Expected RoomFit 3.1.1 source directory'
assert (web / 'roomfit3.html').is_file()

# The engine is stored separately so it can be tested without the DOM.
(web / 'roomfit32-recommend.js').write_bytes((Path(__file__).with_name('roomfit32-recommend.js')).read_bytes())

htmlfile = web / 'roomfit3.html'
html = htmlfile.read_text(encoding='utf-8')
assert 'ROOMFIT 3.1' in html and 'roomfit32-recommend.js' not in html, 'Source already patched or unexpected HTML version'
html = html.replace('룸핏 3.1 | AR 공간 인식', '룸핏 3.2 | 취향 추천 · AR 공간 인식').replace('ROOMFIT 3.1', 'ROOMFIT 3.2')
html = html.replace('예산에 맞는 가구를 골라요.', '예산과 취향에 맞는 가구를 골라요.')
html = html.replace('추천 조합을 비교하거나, 필요한 가구를 직접 선택할 수 있습니다.', '좋아하는 인테리어 스타일을 고르고 추천 이유와 같은 종류의 가격을 비교해 보세요.')
anchor='<div class="panel"><div class="panel-head"><strong>내 예산 맞춤 추천</strong>'
assert anchor in html
styles = '''<div class="panel"><div class="panel-head"><strong>내 인테리어 취향</strong><span class="muted">선택한 스타일 우선</span></div>
<div id="style-options" class="style-options" role="group" aria-label="인테리어 취향 선택"></div>
<p id="style-note" class="fine" aria-live="polite"></p><p class="fine">스타일 분류는 상품 이름의 키워드에 따른 시연용 추정이며, 제조사 공식 분류가 아닙니다.</p></div>
'''
html = html.replace(anchor, styles + anchor, 1)
anchor2='<div class="panel"><div class="panel-head"><strong>가구 60개 라이브러리</strong>'
assert anchor2 in html
comparison='''<div class="panel"><div class="panel-head"><strong>같은 종류 가구 가격 비교</strong><span class="muted">최대 3개</span></div>
<label class="compare-label" for="compare-category">비교할 가구 종류</label><select id="compare-category" aria-label="가격 비교 가구 종류"></select>
<div id="compare-grid" class="compare-grid" aria-live="polite"></div>
<p class="fine">가장 저렴한 후보·취향에 가까운 후보·다른 가격대 후보를 비교합니다. 54개 가구의 가격은 시연용 가정값이므로 실제 구매 가격 비교가 아닙니다.</p></div>
'''
html=html.replace(anchor2,comparison+anchor2,1)
html=html.replace('<script src="/roomfit3.js"></script>', '<script src="/roomfit32-recommend.js"></script><script src="/roomfit3.js"></script>')
htmlfile.write_text(html, encoding='utf-8')

cssfile=web/'roomfit3.css'
css=cssfile.read_text(encoding='utf-8')
assert '.style-options' not in css
css += '''\n/* RoomFit 3.2: preference chips, price comparison, recommendation explanations */
.style-options{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:8px}
.style-choice{border:1px solid #d6e4d7;background:#f8fbf7;border-radius:11px;padding:12px 8px;min-height:54px;color:#355b44;text-align:center;font-weight:750}
.style-choice[aria-pressed="true"]{border-color:#28734d;background:#e5f2e8;box-shadow:inset 0 0 0 1px #28734d;color:#16593b}
.style-choice span{font-size:11px;color:#657b69;display:block;font-weight:400;margin-top:3px}
.compare-label{display:block;font-size:12px;font-weight:650;margin-bottom:4px;color:#5f7566}
#compare-category{width:100%;padding:11px;border:1px solid #d9e3d8;border-radius:10px;background:#fff;color:#264537}
.compare-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:9px;margin-top:13px}
.compare-card{border:1px solid #dbe7dc;border-radius:12px;background:#fcfdfb;padding:12px;min-width:0}
.compare-card .compare-badge{font-size:11px;color:#2e6d4b;font-weight:750}
.compare-card h3{font-size:13px;line-height:1.4;min-height:36px;margin:6px 0 4px;word-break:keep-all}
.compare-card .compare-price{font-weight:850;color:#225b41;font-size:18px}
.compare-card small{display:block;color:#708475;font-size:11px;margin-top:4px}
.compare-card button{width:100%;margin-top:10px;padding:8px}
.recommend-reason{color:#687e6d;font-size:11px;display:block;line-height:1.4;margin-top:3px}
.style-tag{display:inline-flex;align-items:center;font-size:10px;padding:2px 5px;border-radius:8px;background:#eaf3ea;color:#3d7555;margin-top:3px}
@media(max-width:480px){.compare-grid{grid-template-columns:1fr}.compare-card h3{min-height:0}.style-choice{min-height:50px}}
'''
cssfile.write_text(css, encoding='utf-8')

jsfile=web/'roomfit3.js'
js=jsfile.read_text(encoding='utf-8')
assert 'RoomFit 3.1:' in js and 'preferredStyle' not in js, 'Source already patched or unexpected JS version'
js=js.replace('RoomFit 3.1:', 'RoomFit 3.2:')
js=js.replace("let hours=Object.fromEntries(habits.map(([k,, ,v])=>[k,v]));", "let hours=Object.fromEntries(habits.map(([k,, ,v])=>[k,v]));\nlet preferredStyle='minimal';")
js=js.replace("if(Number.isFinite(s.budget)&&s.budget>0&&s.budget<50000000)budget=s.budget;", "if(Number.isFinite(s.budget)&&s.budget>0&&s.budget<50000000)budget=s.budget;if(Object.hasOwn(Roomfit32.STYLES,s.style))preferredStyle=s.style;")
js=js.replace("JSON.stringify({hours,budget,selected:selected.map(p=>p.id)})", "JSON.stringify({hours,budget,style:preferredStyle,selected:selected.map(p=>p.id)})")
start=js.index('function pickPlan(type){')
end=js.index('function showPlans(){',start)
newpick='''function pickPlan(type){
 const left=remaining(),used=chosenKinds(),list=[],max=type==='economy'?3:5;
 for(const g of sequences(type)){
   if(list.length>=max)break;
   if(used.has(g))continue;
   const spent=list.reduce((s,y)=>s+y.price,0);
   const options=models.filter(x=>x.group===g&&x.price!=null&&x.price>0&&x.price<=left-spent);
   const candidate=Roomfit32.choose(options,preferredStyle,type);
   if(candidate)list.push(candidate);
 }
 return list;
}
function renderStyle(){
 $('style-options').innerHTML=Object.entries(Roomfit32.STYLES).map(([key,s])=>`<button type="button" class="style-choice" data-style="${key}" aria-pressed="${preferredStyle===key}">${escapeText(s.label)}<span>${escapeText(s.description)}</span></button>`).join('');
 $('style-note').textContent='선택: '+Roomfit32.STYLES[preferredStyle].label+' · 이 취향과 일치하는 이름 키워드의 모델을 추천에서 우선 고려합니다.';
}
function renderCompare(){
 const group=$('compare-category').value||'desk';
 const items=Roomfit32.compare(models,group,preferredStyle);
 $('compare-grid').innerHTML=items.map((m,i)=>{
   const label=i===0?'비교 후보 1':i===1?'비교 후보 2':'비교 후보 3';
   const dims=m.dimensionsCm.map(x=>Math.round(x)).join(' × ');
   return `<div class="compare-card"><span class="compare-badge">${label}</span><h3>${escapeText(m.name)}</h3><div class="compare-price">${money(m.price)}</div><small>${escapeText(dims)}cm</small><small>${m.priceType==='demo'?'시연용 가정 가격':'과거 참고 가격'}</small><small>${escapeText(Roomfit32.reasons(m,{style:preferredStyle,hours})[0])}</small><button class="soft" data-compare-add="${escapeText(m.asset)}">선택 목록에 추가</button></div>`;
 }).join('')||'<p class="fine">가격이 등록된 비교 후보가 없습니다.</p>';
}
'''
js=js[:start]+newpick+js[end:]
js=js.replace("['focus','생활패턴 맞춤','중요한 활동 공간을 먼저 고려']", "['focus','생활패턴·취향 맞춤','생활패턴과 스타일 일치도를 우선 고려']")
js=js.replace("['balance','다양한 가구','여러 종류를 고르게 살펴보기']", "['balance','취향형 구성','좋아하는 스타일을 고려해 여러 종류 추천']")
old="${escapeText(m.name)} · ${money(m.price)} (${m.priceType==='demo'?'시연 가격':'과거 참고가'})</li>"
new="${escapeText(m.name)} · ${money(m.price)} (${m.priceType==='demo'?'시연 가격':'과거 참고가'})<small class=\"recommend-reason\">추천 이유: ${escapeText(Roomfit32.reasons(m,{style:preferredStyle,hours}).join(' · '))}</small></li>"
assert old in js
js=js.replace(old,new)
# Add simple style tag on each catalog product without rewriting product functionality.
old2="<small>${m.priceType==='demo'?'시연 가격 · 가상 모델':m.priceType==='historical'?'과거 참고가':'가격 미등록'}</small><button"
new2="<small>${m.priceType==='demo'?'시연 가격 · 가상 모델':m.priceType==='historical'?'과거 참고가':'가격 미등록'}</small><span class=\"style-tag\">${Roomfit32.tags(m).map(k=>Roomfit32.STYLES[k].label).join(' · ')||'스타일 정보 미확인'}</span><button"
assert old2 in js
js=js.replace(old2,new2)
old3="if(n===2){showSelected();showPlans();renderCatalogue();}"
assert old3 in js
js=js.replace(old3,"if(n===2){renderStyle();showSelected();showPlans();renderCatalogue();renderCompare();}")
js=js.replace("style:{title:'RoomFit 3.1'", "style:{title:'RoomFit 3.2'")
# Style click handlers and comparison click handlers.
anchor="$('refresh').addEventListener('click',showPlans);"
assert anchor in js
newhandlers='''$('style-options').addEventListener('click',e=>{
 const b=e.target.closest('[data-style]');if(!b||!Object.hasOwn(Roomfit32.STYLES,b.dataset.style))return;
 preferredStyle=b.dataset.style;saveSettings();renderStyle();showPlans();renderCompare();renderCatalogue();
});
$('compare-category').addEventListener('change',renderCompare);
$('compare-grid').addEventListener('click',e=>{
 const b=e.target.closest('[data-compare-add]');if(!b)return;
 const m=models.find(x=>x.asset===b.dataset.compareAdd);if(m)add(m);
});
'''+anchor
js=js.replace(anchor,newhandlers)
# A dynamically generated comparison dropdown must reflect available groups.
anchor="$('category').innerHTML='<option value=\"\">전체</option>'+[...new Set(models.map(x=>x.group))]"
assert anchor in js
js=js.replace(anchor,"$('compare-category').innerHTML=[...new Set(models.map(x=>x.group))].map(k=>`<option value=\"${escapeText(k)}\">${escapeText(categories[k]||k)}</option>`).join('');$('compare-category').value='desk';"+anchor)
js=js.replace('renderCatalogue();showPlans();showSelected();', 'renderCatalogue();renderStyle();renderCompare();showPlans();showSelected();')
jsfile.write_text(js,encoding='utf-8')
(root/'ROOMFIT-3.2-README.md').write_text('''# RoomFit 3.2 — AR 유지 + 비AR 추천 강화

기존 3.1.1 ARCore Depth, AR 가구 이동/회전, 빈 공간 후보, 결과 촬영/저장은 변경하지 않습니다.

새 기능:
- 취향 선택: 미니멀·우드·모던·포근한 (이름 키워드 기반 임시 분류)
- 생활패턴 + 취향 + 예산을 함께 고려한 가구 조합 추천
- 추천 상품별 설명 (생활패턴, 이름 키워드 일치, 가격 데이터 구분)
- 같은 종류 가구 최대 3개 가격·치수·스타일 비교 및 선택

데이터 주의: 총 60개 중 54개 모델의 가격은 시연용으로 임의 설정된 값입니다. 나머지 6개도 현재 가격이 아닌 과거 참고가입니다. 실제 쇼핑 최저가 비교를 의미하지 않습니다. 스타일 분류도 제조사 검증이 아닌 이름 규칙에 의한 추정입니다.

앱 실행 순서: 생활패턴 → 예산·취향 및 가구 추천/가격 비교 → AR → 결과 촬영.

테스트: `node tools/roomfit32.test.cjs` 및 Android Studio Gradle 빌드. ARCore 기능은 실제 지원 기기에서 추가 검증해야 합니다.
''',encoding='utf-8')
print('Patched RoomFit 3.2 at', root)