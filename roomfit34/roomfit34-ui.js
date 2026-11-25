/* RoomFit 3.4: five-stage mobile wizard, persistent nav, native independent 3D preview. */
(()=>{'use strict';
 const $=id=>document.getElementById(id);
 const stages=['생활패턴','취향·예산','가구 선택','3D 미리보기','AR 배치'];
 const icons={menu:'M4 6h16M4 12h16M4 18h16',close:'M5 5l14 14M19 5L5 19',home:'M3 10l9-7 9 7v11H3zM9 21v-8h6v8',heart:'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.8l-1.1-1.2a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z',chair:'M5 5h14v10H5zM5 12h14M7 15v5M17 15v5',cube:'M12 2l9 5-9 5-9-5zM3 7v10l9 5 9-5V7M12 12v10',camera:'M4 7h3l2-3h6l2 3h3a2 2 0 0 1 2 2v10H2V9a2 2 0 0 1 2-2zM12 10a4 4 0 1 0 0 8 4 4 0 0 0 0-8',archive:'M3 4h18v5H3zM5 9v11h14V9M10 13h4',arrow:'M5 12h14m-6-6 6 6-6 6'};
 const svg=k=>`<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" stroke-linecap="round"><path d="${icons[k]||icons.cube}"/></svg>`;
 if(!$('step1')||!$('step4')||!$('selected'))return;
 let current=1,drawerOpen=false,backTarget=null,models=null;
 // The original app owns data validation, recommendations, and native AR handoff.
 const nativeShow=n=>{const b=document.querySelector(`.steps [data-step="${n}"]`);if(!b)return false;b.click();return !$('step'+n).hidden;};
 const originalHeader=document.querySelector('.app-header');
 originalHeader.innerHTML=`<div class="rf34-head-left"><button id="rf34-open-menu" class="rf34-icon-button" aria-label="메뉴 열기">${svg('menu')}</button><div class="rf34-brand">룸핏<span>.</span><small>ROOMFIT 3.4</small></div></div><span class="rf34-head-meta">MY ROOM</span>`;
 const intro=document.querySelector('.hero');
 intro.innerHTML='<span class="eyebrow">YOUR ROOM, YOUR STYLE</span><h1>내 방을 만드는<br><em>5가지 쉬운 단계</em></h1><p>생활패턴을 입력하고, 취향에 맞는 가구를 고른 뒤 3D로 확인하세요.</p>';
 const oldSteps=document.querySelector('.steps');oldSteps.classList.add('rf34-old-steps');
 const five=document.createElement('nav');five.className='rf34-progress';five.id='rf34-progress';five.setAttribute('aria-label','5단계 진행');
 five.innerHTML=stages.map((s,i)=>`<button type="button" data-rf34-step="${i+1}" aria-label="${i+1}단계 ${s}"><span>${i+1}</span><small>${s}</small></button>`).join('');
 oldSteps.insertAdjacentElement('afterend',five);
 const step3d=document.createElement('section');step3d.id='step3d';step3d.className='step rf34-3d-step';step3d.hidden=true;
 step3d.innerHTML=`<div class="section-title"><small>04 / 3D VIEW</small><h2>가구를 3D로 살펴봐요.</h2><p>카메라나 AR 인식 없이 선택한 가구를 회전·확대할 수 있습니다.</p></div><div class="panel"><p class="rf34-message">선택한 가구를 눌러 3D 모델을 확인해 보세요. 시연용 모형은 실제 상품 외형과 다를 수 있습니다.</p><div id="rf34-3d-items" class="rf34-preview-list"></div></div><button type="button" id="rf34-preview-next" class="primary full">5단계 · AR 배치로 이동 →</button>`;
 $('step3').before(step3d);
 const libraryButton=document.createElement('button');libraryButton.type='button';libraryButton.className='rf34-open-library soft';libraryButton.id='rf34-open-library';libraryButton.textContent='📂 촬영 결과 보관함 열기';$('step3').appendChild(libraryButton);
 const retry=document.createElement('div');retry.className='rf34-ar-guide';retry.innerHTML=`<strong>AR 가구가 안 보일 때</strong><p>① 밝고 넓은 바닥을 비추고 천천히 움직이세요. ② 화면을 터치하세요. ③ 카메라가 멈추면 AR 화면의 「추적 다시 시작」을 사용하세요.</p><p>ARCore가 위치 추적을 시작하지 못하면 가구가 실제 공간에 고정되지 않습니다. 이 경우 4단계의 3D 미리보기로 확인할 수 있습니다.</p><button type="button" id="rf34-back-preview" class="soft">AR 대신 3D로 보기</button></div>`;
 $('step3').appendChild(retry);
 const tabs=document.createElement('nav');tabs.className='rf34-tabs';tabs.setAttribute('aria-label','주요 메뉴');tabs.innerHTML=[['home','홈',1],['heart','취향',2],['chair','가구',3],['cube','3D',4],['camera','AR',5]].map(([icon,text,n])=>`<button type="button" data-rf34-tab="${n}">${svg(icon)}<span>${text}</span></button>`).join('');document.body.appendChild(tabs);
 const backdrop=document.createElement('div');backdrop.id='rf34-backdrop';backdrop.hidden=true;backdrop.className='rf34-backdrop';document.body.appendChild(backdrop);
 const drawer=document.createElement('aside');drawer.id='rf34-drawer';drawer.className='rf34-drawer';drawer.setAttribute('role','dialog');drawer.setAttribute('aria-modal','true');drawer.setAttribute('aria-label','룸핏 메뉴');drawer.hidden=true;
 drawer.innerHTML=`<div class="rf34-drawer-title"><div><small>MY INTERIOR PLAN</small><strong>룸핏<span>.</span></strong><p>나만의 인테리어 만들기</p></div><button class="rf34-icon-button" id="rf34-close-menu" aria-label="메뉴 닫기">${svg('close')}</button></div><nav>${stages.map((s,i)=>`<button type="button" data-rf34-drawer="${i+1}">${svg(['home','heart','chair','cube','camera'][i])}<span>${i+1}단계 · ${s}</span></button>`).join('')}<button type="button" data-rf34-drawer="6">${svg('archive')}<span>결과 보관함</span></button></nav><p class="rf34-drawer-note">※ 일부 가구 가격은 시연용입니다. AR 공간 인식과 치수·장애물 검사는 정확도를 보장하지 않습니다.</p>`;
 document.body.appendChild(drawer);
 function closeDrawer(){if(!drawerOpen)return;drawerOpen=false;drawer.hidden=true;backdrop.hidden=true;document.body.classList.remove('rf34-drawer-open');backTarget?.focus?.();}
 function openDrawer(){if(drawerOpen)return;backTarget=document.activeElement;drawerOpen=true;drawer.hidden=false;backdrop.hidden=false;document.body.classList.add('rf34-drawer-open');$('rf34-close-menu').focus();}
 $('rf34-open-menu').addEventListener('click',openDrawer);$('rf34-close-menu').addEventListener('click',closeDrawer);backdrop.addEventListener('click',closeDrawer);
 document.addEventListener('keydown',e=>{if(!drawerOpen)return;if(e.key==='Escape'){closeDrawer();return;}if(e.key==='Tab'){const f=[...drawer.querySelectorAll('button:not(:disabled)')];let i=f.indexOf(document.activeElement);if((e.shiftKey&&i===0)||(!e.shiftKey&&i===f.length-1)){e.preventDefault();f[e.shiftKey?f.length-1:0].focus();}}});
 const panels=[...$('step2').querySelectorAll(':scope > .panel')];
 const originalTitle=$('step2').querySelector(':scope > .section-title');
 function choiceCount(){return $('selected').querySelectorAll('.chosen').length;}
 async function loadModels(){if(models)return models;try{const r=await fetch('/product-models.json');if(!r.ok)throw Error('data');models=await r.json();return models;}catch{return null;}}
 const safeText=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 async function render3D(){const list=$('rf34-3d-items');list.textContent='선택한 가구를 불러오는 중…';let ids=[];try{ids=JSON.parse(localStorage.getItem('roomfit3-settings')||'{}').selected||[];}catch{}
 const all=await loadModels();if(current!==4)return;if(!all){list.textContent='모델 정보를 확인할 수 없습니다. 가구 선택 단계에서 다시 시도해주세요.';return;}
 list.innerHTML=ids.map(id=>{const m=all[id];if(!m)return '';const dims=(m.dimensionsCm||[50,50,50]).map(Number);
 return `<div class="rf34-3d-card"><img loading="lazy" src="/model-thumbnails/${encodeURIComponent(m.asset||id)}.webp" alt="${safeText(m.name)} 사진"><div><strong>${safeText(m.name)}</strong><small>크기 ${dims.map(x=>Math.round(x)).join(' × ')} cm</small><button type="button" data-rf34-view="${safeText(id)}" class="primary">3D로 회전·확대해서 보기</button></div></div>`;}).join('')||'<p>아직 선택한 가구가 없습니다. 3단계에서 먼저 가구를 선택해주세요.</p>';
 }
 $('rf34-3d-items').addEventListener('click',async e=>{const b=e.target.closest('[data-rf34-view]');if(!b)return;const all=await loadModels();const id=b.dataset.rf34View;const m=all?.[id];if(!m)return;const dims=m.dimensionsCm||[50,50,50];if(window.RoomfitNative?.openFurniturePreview){try{window.RoomfitNative.openFurniturePreview(JSON.stringify({id,name:m.name,kind:m.kind||'table',width:Number(dims[0]),depth:Number(dims[1]),height:Number(dims[2])}));}catch{alert('3D 화면을 열지 못했습니다.');}}else alert('3D 모델 회전·확대는 Android APK에서 지원합니다.');});
 function displayStage(n){
  const original=n===1?1:n<=4?2:n===5?3:4;
  if(!nativeShow(original))return false;
  current=n;
  for(let i=1;i<=4;i++)$('step'+i).hidden=true;
  if(n===1)$('step1').hidden=false;
  if(n===2||n===3)$('step2').hidden=false;
  if(n===4)step3d.hidden=false;
  if(n===5)$('step3').hidden=false;
  if(n===6)$('step4').hidden=false;
  const isBudget=n===2,isFurniture=n===3;
  panels.forEach((p,i)=>p.hidden=isBudget?i>2:isFurniture?i<3:true);
  if(originalTitle){originalTitle.querySelector('small').textContent=isBudget?'02 / STYLE & BUDGET':'03 / FURNITURE';originalTitle.querySelector('h2').textContent=isBudget?'취향과 예산을 정해요.':'마음에 드는 가구를 골라요.';originalTitle.querySelector('p').textContent=isBudget?'인테리어 스타일과 예산을 설정하고 추천 이유를 확인하세요.':'가구 60개를 살펴보고 가격을 비교한 다음 최대 5개를 선택하세요.';}
  intro.hidden=n!==1;
  five.hidden=n===6;
  five.querySelectorAll('button').forEach(b=>{const on=Number(b.dataset.rf34Step)===n;b.classList.toggle('active',on);b.classList.toggle('finished',Number(b.dataset.rf34Step)<n);b.setAttribute('aria-current',on?'step':'false');});
  $('progress').textContent=n===6?'결과 보관함':`${n} / 5 단계 · ${stages[n-1]}`;
  $('back').disabled=n===1;$('back').textContent=n===6?'← AR 배치':'← 이전';
  $('next').textContent=n===6?'AR 배치로 돌아가기':n===5?'결과 보관함 열기 →':`다음 · ${stages[n]} →`;
  tabs.querySelectorAll('button').forEach(b=>{const active=Number(b.dataset.rf34Tab)===n;b.classList.toggle('active',active);b.setAttribute('aria-current',active?'page':'false');});
  drawer.querySelectorAll('button[data-rf34-drawer]').forEach(b=>b.classList.toggle('active',Number(b.dataset.rf34Drawer)===n));
  if(n===4)render3D();
  window.scrollTo({top:0,behavior:'instant'});return true;
 }
 function go(n){closeDrawer();if(n<1||n>6)return;if(n>=4&&n<=5&&choiceCount()===0){alert('3단계에서 먼저 가구를 하나 이상 선택해 주세요.');displayStage(3);return;}displayStage(n);}
 // Intercept legacy bubble handlers to guarantee one wizard and correct five-stage navigation.
 $('back').addEventListener('click',e=>{e.stopImmediatePropagation();go(current===6?5:current-1);},true);
 $('next').addEventListener('click',e=>{e.stopImmediatePropagation();go(current===6?5:current+1);},true);
 tabs.addEventListener('click',e=>{const b=e.target.closest('[data-rf34-tab]');if(b)go(Number(b.dataset.rf34Tab));});
 drawer.addEventListener('click',e=>{const b=e.target.closest('[data-rf34-drawer]');if(b)go(Number(b.dataset.rf34Drawer));});
 five.addEventListener('click',e=>{const b=e.target.closest('[data-rf34-step]');if(b)go(Number(b.dataset.rf34Step));});
 $('rf34-preview-next').addEventListener('click',()=>go(5));
 $('rf34-open-library').addEventListener('click',()=>go(6));
 $('rf34-back-preview').addEventListener('click',()=>go(4));
 // Native AR result handler invokes the original 4th internal step; show library instead.
 const receive=window.receiveLockedARResult;
 window.receiveLockedARResult=(result)=>{if(receive)receive(result);if(result&&typeof result.image==='string'&&result.image.startsWith('data:image/jpeg;base64,'))displayStage(6);};
 window.roomfitBack=()=>{if(drawerOpen){closeDrawer();return true;}if(current>1){go(current===6?5:current-1);return true;}return false;};
 // Base project might asynchronously render selected items; rerender only count-dependent UI.
 displayStage(1);
})();