/* RoomFit 3.2 - deterministic recommendation helpers.
 * Heuristic tags are inferred from furniture display names, NOT vendor-verified style metadata.
 * Works offline and is pure enough to unit test in Node.
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.Roomfit32 = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const STYLES = Object.freeze({
    minimal: { label: '미니멀', description: '깔끔하고 단순한 형태를 선호해요.' },
    wood: { label: '우드', description: '나무 질감이 느껴지는 가구를 선호해요.' },
    modern: { label: '모던', description: '단정하고 현대적인 디자인을 선호해요.' },
    cozy: { label: '포근한', description: '편안한 분위기와 쿠션·패브릭을 선호해요.' }
  });
  const KEYWORDS = Object.freeze({
    minimal: /화이트|슬림|미니|낮은|저상|기본|사각|스툴|심플|정리|선반/i,
    wood: /원목|참나무|나무|우드|오크|목재/i,
    modern: /모던|컴퓨터|작업|와이드|회전|스퀘어|홈오피스|서재|블랙|오픈/i,
    cozy: /쿠션|패브릭|소파|라운지|헤드보드|수면|침대|플로어/i
  });
  function tags(product) {
    const name = String(product && product.name || '');
    return Object.keys(STYLES).filter(key => KEYWORDS[key].test(name));
  }
  function styleMatch(product, style) {
    return tags(product).includes(style) ? 1 : 0;
  }
  function uniqueById(items) {
    const seen = new Set();
    return items.filter(x => { if (seen.has(x.id)) return false; seen.add(x.id); return true; });
  }
  function choose(items, style, mode) {
    const pool = items.filter(m => Number.isFinite(m.price) && m.price > 0).slice();
    pool.sort((a, b) => a.price - b.price || String(a.name).localeCompare(String(b.name), 'ko'));
    if (!pool.length) return null;
    if (mode === 'economy') return pool[0];
    const matching = pool.filter(m => styleMatch(m, style));
    if (mode === 'focus') return matching[0] || pool[0];
    return matching[Math.floor(matching.length / 2)] || pool[Math.floor((pool.length - 1) / 2)];
  }
  function compare(items, group, style) {
    const pool = items.filter(m => m.group === group && Number.isFinite(m.price) && m.price > 0)
      .slice().sort((a, b) => a.price - b.price || String(a.name).localeCompare(String(b.name), 'ko'));
    if (!pool.length) return [];
    const preferred = pool.filter(m => styleMatch(m, style));
    const middle = pool[Math.floor((pool.length - 1) / 2)];
    // Price low, style fit, and an alternative at a different price tier.
    const last = pool[pool.length - 1];
    return uniqueById([pool[0], preferred[0] || middle, last]).slice(0, 3);
  }
  function reasons(product, context) {
    const style = context && context.style in STYLES ? context.style : 'minimal';
    const hours = context && context.hours || {};
    const group = String(product.group || '');
    const out = [];
    if (styleMatch(product, style)) out.push(STYLES[style].label + ' 취향 키워드와 일치');
    const study = Number(hours.study || 0), sleep = Number(hours.sleep || 0), hobby = Number(hours.hobby || 0);
    if ((group === 'desk' || group === 'chair') && study >= 3) out.push('공부·작업 시간이 많아 우선 추천');
    else if (group === 'bed' && sleep >= 6) out.push('수면 시간이 많아 우선 추천');
    else if ((group === 'sofa' || group === 'table') && hobby >= 3) out.push('취미·휴식 공간에 적합한 종류');
    if (product.priceType === 'demo') out.push('가격은 시연용 가정값');
    else if (product.priceType === 'historical') out.push('가격은 과거 참고가');
    return out.length ? out : ['선택한 종류와 예산 기준의 후보'];
  }
  return Object.freeze({ STYLES, tags, styleMatch, choose, compare, reasons });
});