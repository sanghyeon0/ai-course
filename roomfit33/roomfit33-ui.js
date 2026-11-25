/* RoomFit 3.3 · mobile guided flow, persistent bottom tabs, accessible side drawer.
   This enhances, rather than replaces, the tested RoomFit 3.2 recommendation/AR engine. */
(()=>{'use strict';
  const $=id=>document.getElementById(id);
  const root=document.body;
  const steps=[...document.querySelectorAll('.steps [data-step]')];
  if(!steps.length||!$('step1')||!$('step4')) return;
  const labels={1:'생활패턴',2:'가구 선택',3:'AR 배치',4:'결과 보관함'};
  const icons={
    home:'<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
    furniture:'<rect x="4" y="4" width="16" height="11" rx="3"/><path d="M4 12h16M6 15v5M18 15v5M9 8h6"/>',
    camera:'<path d="M4 7h3l2-3h6l2 3h3a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/><circle cx="12" cy="13" r="3.5"/>',
    archive:'<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v11h14V9M10 13h4"/>',
    menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
    close:'<path d="M5 5l14 14M19 5 5 19"/>',
    chevron:'<path d="m9 18 6-6-6-6"/>'
  };
  const svg=k=>`<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${icons[k]}</svg>`;
  const header=document.querySelector('.app-header');
  header.innerHTML=`<div class="rf-header-left"><button class="rf-menu-btn" id="rf-menu-open" type="button" aria-label="메뉴 열기" aria-expanded="false" aria-controls="rf-drawer">${svg('menu')}</button><div class="brand">룸핏<span>.</span><small>ROOMFIT 3.3</small></div></div><div class="rf-header-status"><span class="rf-status-dot"></span>MY ROOM</div>`;
  const oldHero=document.querySelector('.hero');
  oldHero.classList.add('rf-intro');
  oldHero.innerHTML=`<span class="eyebrow">ROOMFIT · MY INTERIOR</span><h1>내 취향에 맞는 방,<br><em>한 단계씩 완성해요.</em></h1><p>생활패턴을 알려주고, 가구를 선택한 뒤 AR로 확인하세요.</p>`;
  // Keep the original four step handlers in place, but present 3 primary steps.
  steps[1].querySelector('span').textContent='가구 선택';
  steps[2].querySelector('span').textContent='AR 배치';
  steps[3].hidden=true;
  const stepsNode=document.querySelector('.steps');
  stepsNode.insertAdjacentHTML('afterend','<div class="rf-meter" id="rf-meter" aria-hidden="true"><span></span><span></span><span></span></div>');
  const nav=document.createElement('nav');
  nav.className='rf-tabs';nav.id='rf-tabs';nav.setAttribute('aria-label','룸핏 주요 메뉴');
  nav.innerHTML=[[1,'home','홈'],[2,'furniture','가구'],[3,'camera','AR'],[4,'archive','보관함']].map(([n,icon,title])=>`<button type="button" data-rf-tab="${n}" aria-label="${title}" aria-current="false">${svg(icon)}<span>${title}</span>${n===2?'<i class="rf-count" id="rf-tab-count" hidden>0</i>':''}</button>`).join('');
  document.body.appendChild(nav);
  const overlay=document.createElement('div');
  overlay.className='rf-drawer-overlay';overlay.id='rf-drawer-overlay';overlay.hidden=true;
  const drawer=document.createElement('aside');
  drawer.className='rf-drawer';drawer.id='rf-drawer';drawer.hidden=true;
  drawer.setAttribute('role','dialog');drawer.setAttribute('aria-modal','true');drawer.setAttribute('aria-label','룸핏 메뉴');drawer.setAttribute('tabindex','-1');
  drawer.innerHTML=`<div class="rf-drawer-head"><div><span class="rf-drawer-mini">MY INTERIOR PLAN</span><strong>룸핏<span>.</span></strong><small>나에게 맞는 공간 만들기</small></div><button type="button" id="rf-menu-close" aria-label="메뉴 닫기">${svg('close')}</button></div><p class="rf-drawer-caption">나만의 인테리어 여정</p><div class="rf-drawer-links">${[[1,'home','홈 · 생활패턴'],[2,'furniture','가구 추천·선택'],[3,'camera','AR 배치'],[4,'archive','결과 보관함']].map(([n,key,title])=>`<button type="button" data-rf-drawer-step="${n}">${svg(key)}<span>${title}</span>${svg('chevron')}</button>`).join('')}</div><div class="rf-drawer-info"><strong>이용 안내</strong><p>① 생활패턴 입력<br>② 취향·예산 맞춤 가구 선택<br>③ 3D 미리보기와 AR 배치<br>④ 촬영 결과는 보관함에서 확인</p><small>일부 가구의 가격은 시연용입니다. AR의 실제 치수와 장애물 판단은 직접 확인하세요.</small></div><p class="rf-drawer-version">RoomFit 3.3 · Android</p>`;
  document.body.append(overlay,drawer);
  const openButton=$('rf-menu-open');
  let lastFocus=null,drawerOpen=false;
  function openDrawer(){
    if(drawerOpen)return;
    lastFocus=document.activeElement;
    drawer.hidden=false;overlay.hidden=false;drawerOpen=true;
    root.classList.add('rf-drawer-open');
    openButton.setAttribute('aria-expanded','true');
    $('rf-menu-close').focus();
  }
  function closeDrawer(){
    if(!drawerOpen)return;
    drawer.hidden=true;overlay.hidden=true;drawerOpen=false;
    root.classList.remove('rf-drawer-open');
    openButton.setAttribute('aria-expanded','false');
    if(lastFocus?.focus)lastFocus.focus();
  }
  openButton.addEventListener('click',openDrawer);
  $('rf-menu-close').addEventListener('click',closeDrawer);
  overlay.addEventListener('click',closeDrawer);
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'&&drawerOpen){e.preventDefault();closeDrawer();return;}
    if(e.key==='Tab'&&drawerOpen){
      const f=[...drawer.querySelectorAll('button:not([disabled])')];
      const i=f.indexOf(document.activeElement);
      if(e.shiftKey&&i===0){e.preventDefault();f[f.length-1].focus();}
      else if(!e.shiftKey&&i===f.length-1){e.preventDefault();f[0].focus();}
    }
  });
  const oldBack=window.roomfitBack;
  window.roomfitBack=()=>{if(drawerOpen){closeDrawer();return true;}return typeof oldBack==='function'?oldBack():false;};
  function go(n){
    closeDrawer();
    const target=steps.find(b=>Number(b.dataset.step)===n);
    if(target)target.click();
  }
  nav.addEventListener('click',e=>{const b=e.target.closest('[data-rf-tab]');if(b)go(Number(b.dataset.rfTab));});
  drawer.addEventListener('click',e=>{const b=e.target.closest('[data-rf-drawer-step]');if(b)go(Number(b.dataset.rfDrawerStep));});
  // A quiet selection summary is always visible on the furniture step.
  const summary=document.createElement('div');
  summary.className='rf-selection-summary';summary.id='rf-selection-summary';
  summary.setAttribute('role','status');summary.innerHTML='<span>선택한 가구</span><strong>0개</strong><small>가구를 골라주세요</small>';
  $('step2').insertBefore(summary,$('step2').firstElementChild.nextElementSibling);
  summary.addEventListener('click',()=>{$('selected').scrollIntoView({behavior:'smooth',block:'center'});});
  function refreshCount(){
    const selected=$('selected');
    const n=selected.querySelectorAll('.chosen').length;
    summary.querySelector('strong').textContent=n+'개';
    summary.querySelector('small').textContent=n?'선택 완료 · 최대 5개':'추천 가구를 선택하세요';
    const badge=$('rf-tab-count');badge.hidden=n===0;badge.textContent=String(n);
  }
  new MutationObserver(refreshCount).observe($('selected'),{childList:true,subtree:true});
  function activeStep(){return [1,2,3,4].find(n=>!$('step'+n).hidden)||1;}
  function renderProgress(){
    const n=activeStep();
    oldHero.hidden=n!==1;
    stepsNode.hidden=n===4;
    $('rf-meter').hidden=n===4;
    [...$('rf-meter').children].forEach((el,i)=>el.classList.toggle('filled',i<n));
    $('progress').textContent=n===4?'결과 보관함':`${n} / 3 단계 · ${labels[n]}`;
    nav.querySelectorAll('[data-rf-tab]').forEach(b=>{
      const isActive=Number(b.dataset.rfTab)===n;
      b.classList.toggle('active',isActive);
      b.setAttribute('aria-current',isActive?'page':'false');
    });
    drawer.querySelectorAll('[data-rf-drawer-step]').forEach(b=>b.classList.toggle('active',Number(b.dataset.rfDrawerStep)===n));
    $('next').textContent={1:'다음 · 가구 선택 →',2:'다음 · AR 배치 →',3:'결과 보관함 →',4:'AR 다시 확인 ↶'}[n];
    $('back').textContent=n===4?'← AR 배치':'← 이전';
  }
  const observer=new MutationObserver(renderProgress);
  [1,2,3,4].forEach(n=>observer.observe($('step'+n),{attributes:true,attributeFilter:['hidden']}));
  refreshCount();renderProgress();
})();