'use strict';
let FPS=30,TOTAL=1218,KEY='wechat-0a5c43-manual-review-v1';
const api=new URL('/api/manual-review',location.origin).href;
let groups=[],meta,undoStack=[],dirty=false;
const CLASSIFICATION_REVISION='composition-modes-v2';
const modeLabels={'visual-only':'仅画面动效','subtitle-only':'仅字幕动效','combined':'画面＋字幕动态组合'};
function modeFor(g){return g.compositionMode||(g.visual&&g.subtitle?'combined':g.visual?'visual-only':'subtitle-only')}
const $=s=>document.querySelector(s),esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const frameTime=n=>meta?.frameTimes?.[Math.max(0,Math.min(TOTAL,n))]??n/FPS;
const stamp=n=>frameTime(n).toFixed(3)+' 秒 · 第 '+n+' 帧';
function nearestFrame(time){if(!meta?.frameTimes)return Math.max(0,Math.min(TOTAL-1,Math.round(time*FPS)));let lo=0,hi=TOTAL-1;while(lo<hi){const mid=Math.floor((lo+hi+1)/2);if(frameTime(mid)<=time+0.00001)lo=mid;else hi=mid-1;}return lo;}
const parseTC=s=>{let a=s.split(':').map(Number);return a.reduce((v,x)=>v*60+x,0)};
function payload(){return {schema:1,fps:FPS,endFrameConvention:'exclusive',groups,updatedAt:new Date().toISOString()}}
function cache(){dirty=true;const p=payload();localStorage.setItem(KEY,JSON.stringify(p));$('#status').textContent='已缓存到本浏览器；请点“保存全部调整到项目”';}
function pauseAll(){document.querySelectorAll('video').forEach(v=>v.pause())}
function render(){
 pauseAll();$('#cards').innerHTML='';
 groups=groups.filter(g=>!(meta.feedbackReceipt?.excluded||[]).some(x=>x.id===g.id));
 groups.forEach(g=>{const a=meta.feedbackAnalysis?.[g.id],revision=meta.classificationRevision||CLASSIFICATION_REVISION;if(a&&g.classificationRevision!==revision){g.originalName=g.originalName||g.name;g.name=a.name;g.visual=a.visual??null;g.subtitle=a.subtitle??null;g.compositionMode=a.compositionMode||(a.visual&&a.subtitle?'combined':a.visual?'visual-only':'subtitle-only');g.visualComponents=a.visualComponents||[];g.subtitleComponents=a.subtitleComponents||[];g.layerOrder=a.layerOrder||[];g.classificationRevision=revision;}});
 groups.forEach((g,index)=>{
  const card=document.createElement('article');card.className='card';card.dataset.id=g.id;
  const analysis=meta.feedbackAnalysis?.[g.id];
  card.dataset.mode=modeFor(g);
  card.innerHTML=`<div class="card-head"><div class="summary">${esc(g.id)} · 来源条目：${g.members.map(esc).join('、')}${g.sourceAnnotationId?' · 拆自 '+esc(g.sourceAnnotationId):''}</div><h2 class="current-title">${esc(g.name)}</h2><span class="mode-badge">${esc(modeLabels[modeFor(g)])}</span><label>当前动效名称</label><input class="name" aria-label="动效名称" value="${esc(g.name)}"><label>完整组构成方式 <select class="composition-mode">${Object.entries(modeLabels).map(([k,v])=>`<option value="${k}" ${modeFor(g)===k?'selected':''}>${v}</option>`).join('')}</select></label><div class="composition-evidence"></div><details class="history"><summary>查看历史名称和原始备注</summary><p>旧名称：${esc(g.originalName||g.name)}</p><p>原始备注：${esc(g.note||'无')}</p>${analysis?.userNote?'<p>用户原备注：'+esc(analysis.userNote)+'</p>':''}</details></div>
  <div class="layout"><div><video controls playsinline preload="metadata" src="reference-browser.mp4" aria-label="${esc(g.name)}参考视频"></video><div class="buttons"><button class="play" data-act="play">▶ 播放本组</button><button data-act="pause">暂停</button></div><label class="toggle"><input type="checkbox" class="loop" checked>循环本组</label></div>
  <div><div class="clock">准备载入原片…</div><div class="buttons"><button data-act="prev">◀ 前一帧</button><button data-act="next">后一帧 ▶</button></div>
  <label>起点帧（包含） <input class="start" type="number" min="0" max="${TOTAL-1}" value="${g.startFrame}"></label><div class="summary start-time"></div>
  <div class="buttons"><button data-act="mark-start">当前位置设为起点</button><button data-act="goto-start">看首帧</button></div>
  <label>终点帧（不包含） <input class="end" type="number" min="1" max="${TOTAL}" value="${g.endFrame}"></label><div class="summary end-time"></div>
  <div class="buttons"><button data-act="mark-end">当前帧之后设为终点</button><button data-act="goto-end">看末帧</button></div>
  <label>校正说明</label><textarea class="note" placeholder="例如：这里多带了下一组；这两段应为连续一组">${esc(g.note||'')}</textarea>
  <div class="buttons"><button data-act="merge" ${index===groups.length-1?'disabled':''}>与下一组合并</button><button data-act="save">保存本次调整</button></div></div></div>
  <div class="strip"><label>原片全长定位（可超出当前组，寻找准确边界）</label><input class="seek" aria-label="原片逐帧定位" type="range" min="0" max="${TOTAL-1}" step="1" value="${g.startFrame}"><div class="stripe"><div class="selected"></div></div><div class="summary duration"></div></div>`;
  $('#cards').appendChild(card);
  const describe=()=>{const mode=modeFor(g),visual=(g.visualComponents?.length?g.visualComponents:[g.visual]).map(id=>(meta.visualFamilies||[]).find(f=>f.id===id)?.name||'待填写画面机制').join(' ＋ '),subtitle=(g.subtitleComponents?.length?g.subtitleComponents:[g.subtitle]).map(id=>(meta.subtitleFamilies||[]).find(f=>f.id===id)?.name||'待填写字幕机制').join(' ＋ ');card.dataset.mode=mode;card.querySelector('.mode-badge').textContent=modeLabels[mode];card.querySelector('.composition-evidence').innerHTML=`<p><b>画面动效：</b>${mode==='subtitle-only'?'无；背景仅作底片，具体见下方层级记录':esc(visual)}</p><p><b>字幕动效：</b>${mode==='visual-only'?'无；本组由画面动作独立表达':esc(subtitle)}</p><p><b>表达与接力：</b>${esc(g.purpose||analysis?.purpose||'待补充表达目的')}</p><div class="component-flow">${mode==='subtitle-only'?'底片保留 → 字幕揭晓／强调 → 字幕收束（仅字幕动作）':mode==='visual-only'?'画面入场 → 推进／揭晓 → 停留／退场（无字幕组件）':'画面动作铺垫 ⇄ 字幕接管／强调 → 共同收束（可重叠或连续接力）'}</div><p class="muted">${esc(g.relation||analysis?.relation||'按用户边界保留')}；具体组件时钟待逐帧测量。</p>`;};describe();installComponentEditors(card,g,describe);if(g.visualVariant){const n=document.createElement('p');n.className='muted';n.textContent='本次实例变体：'+g.visualVariant;card.querySelector('.composition-evidence').appendChild(n);}if(g.layerOrder?.length){const layers=document.createElement('p');layers.className='muted';layers.textContent='层级（后→前）：'+g.layerOrder.join(' → ');card.querySelector('.composition-evidence').appendChild(layers);}if(analysis?.userNote){const n=document.createElement('p');n.className='muted';n.textContent='用户原备注：'+analysis.userNote;card.querySelector('.card-head').appendChild(n);}const decision=(meta.feedbackReceipt?.decisions||[]).find(d=>d.id===g.id||d.id===g.sourceAnnotationId);if(decision){const n=document.createElement('p');n.textContent='本次修订：'+decision.reason;card.querySelector('.card-head').appendChild(n);}if(analysis?.boundaryEvidence){const detail=document.createElement('details');detail.innerHTML='<summary>查看首尾与过程帧证据（原片帧号 / PTS）</summary><img style="width:100%;height:auto" src="'+esc(analysis.boundaryEvidence.startsWith('observations/')?'/'+analysis.boundaryEvidence:analysis.boundaryEvidence)+'" alt="'+esc(g.id)+'动作前后与过程帧证据"><p>'+esc(analysis.confidence)+'</p>';card.querySelector('.card-head').appendChild(detail);}
  const v=card.querySelector('video'),seek=card.querySelector('.seek');let groupPlaying=false;
  const frame=()=>Math.min(TOTAL-1,Math.max(0,nearestFrame(v.currentTime)));
  const go=n=>{groupPlaying=false;v.pause();v.currentTime=frameTime(Math.max(0,Math.min(TOTAL-1,n)))+0.000001;};
  const update=()=>{card.querySelector('.clock').textContent=stamp(frame());seek.value=frame();};
  const labels=()=>{card.querySelector('.start-time').textContent=stamp(g.startFrame);card.querySelector('.end-time').textContent=stamp(g.endFrame);card.querySelector('.duration').textContent=`当前保留 ${(g.endFrame-g.startFrame)} 帧 / ${(frameTime(g.endFrame)-frameTime(g.startFrame)).toFixed(3)} 秒；首帧 ${g.startFrame}，末帧 ${g.endFrame-1}`;const bar=card.querySelector('.selected');bar.style.left=g.startFrame/TOTAL*100+'%';bar.style.width=(g.endFrame-g.startFrame)/TOTAL*100+'%';};labels();
  const setRange=(a,b)=>{if(!Number.isInteger(a)||!Number.isInteger(b)||a<0||b>TOTAL||a>=b){$('#status').textContent=`范围无效：须为整数帧，且 0 ≤ 起点 < 终点 ≤ ${TOTAL}`;card.querySelector('.start').value=g.startFrame;card.querySelector('.end').value=g.endFrame;return false}g.startFrame=a;g.endFrame=b;card.querySelector('.start').value=a;card.querySelector('.end').value=b;labels();cache();return true;};
  function bound(t){if(groupPlaying && t>=frameTime(g.endFrame)-0.0005){if(card.querySelector('.loop').checked){v.currentTime=frameTime(g.startFrame)+0.000001;}else{groupPlaying=false;v.pause();v.currentTime=frameTime(g.endFrame-1)+0.000001;}}}
  v.addEventListener('loadedmetadata',()=>{v.currentTime=frameTime(g.startFrame)+0.000001;update()});v.addEventListener('timeupdate',()=>{bound(v.currentTime);update()});v.addEventListener('seeked',update);
  if('requestVideoFrameCallback' in v){const tick=(now,data)=>{bound(data.mediaTime);v.requestVideoFrameCallback(tick)};v.requestVideoFrameCallback(tick)}
  v.addEventListener('play',()=>{document.querySelectorAll('video').forEach(other=>{if(other!==v)other.pause()})});
  seek.addEventListener('input',()=>go(Number(seek.value)));
  card.querySelector('.start').addEventListener('input',e=>{const n=Number(e.target.value);if(Number.isInteger(n)&&n>=0&&n<g.endFrame){g.startFrame=n;labels();cache()}});card.querySelector('.end').addEventListener('input',e=>{const n=Number(e.target.value);if(Number.isInteger(n)&&n>g.startFrame&&n<=TOTAL){g.endFrame=n;labels();cache()}});card.querySelector('.start').addEventListener('change',e=>{if(setRange(Number(e.target.value),g.endFrame))go(g.startFrame)});
  card.querySelector('.end').addEventListener('change',e=>{if(setRange(g.startFrame,Number(e.target.value)))go(g.endFrame-1)});
  card.querySelector('.name').addEventListener('input',e=>{g.name=e.target.value;card.querySelector('.current-title').textContent=g.name;cache()});card.querySelector('.note').addEventListener('input',e=>{g.note=e.target.value;cache()});
  card.querySelector('.composition-mode').addEventListener('change',e=>{g.compositionMode=e.target.value;if(g.compositionMode==='visual-only'){g.subtitle=null;g.subtitleComponents=[]}if(g.compositionMode==='subtitle-only'){g.visual=null;g.visualComponents=[]}describe();updateModes();cache();render()});
  card.addEventListener('click',async e=>{const action=e.target.closest('[data-act]')?.dataset.act;if(!action)return;
   if(action==='play'){pauseAll();v.currentTime=frameTime(g.startFrame)+0.000001;groupPlaying=true;try{await v.play()}catch(err){$('#status').textContent='播放失败：'+err.message}}
   if(action==='pause'){groupPlaying=false;v.pause()}
   if(action==='prev')go(frame()-1);if(action==='next')go(frame()+1);
   if(action==='mark-start'){const n=frame();if(setRange(n,g.endFrame))go(n)}
   if(action==='mark-end'){const n=frame();setRange(g.startFrame,n+1)}
   if(action==='goto-start')go(g.startFrame);if(action==='goto-end')go(g.endFrame-1);
   if(action==='save')save();
   if(action==='merge'&&groups[index+1]){undoStack.push(JSON.stringify(groups));const next=groups[index+1];g.endFrame=Math.max(g.endFrame,next.endFrame);g.startFrame=Math.min(g.startFrame,next.startFrame);g.members=[...g.members,...next.members];g.visualComponents=[...new Set([...(g.visualComponents||[]),...(next.visualComponents||[])])];g.subtitleComponents=[...new Set([...(g.subtitleComponents||[]),...(next.subtitleComponents||[])])];g.visual=g.visualComponents[0]||null;g.subtitle=g.subtitleComponents[0]||null;g.compositionMode=g.visual&&g.subtitle?'combined':g.visual?'visual-only':'subtitle-only';g.purpose=[g.purpose,next.purpose].filter(Boolean).join('；');g.relation=[g.relation,next.relation].filter(Boolean).join(' → ');g.name+=' ＋ '+next.name;g.note=(g.note||'')+'\n手动合并：'+next.id;groups.splice(index+1,1);cache();render()}
  });
 });
 $('#undo').disabled=!undoStack.length;
 updateModes();
}
function updateModes(){const selected=$('#mode-filter')?.value||'all';document.querySelectorAll('.card').forEach(c=>{c.hidden=selected!=='all'&&c.dataset.mode!==selected});if($('#mode-summary'))$('#mode-summary').textContent=Object.entries(modeLabels).map(([k,v])=>`${v}：${groups.filter(g=>modeFor(g)===k).length}`).join('　｜　');}
async function save(){try{document.querySelectorAll('.card').forEach(card=>{const g=groups.find(x=>x.id===card.dataset.id);const a=Number(card.querySelector('.start').value),b=Number(card.querySelector('.end').value);if(!Number.isInteger(a)||!Number.isInteger(b)||a<0||a>=b||b>TOTAL)throw Error('起终帧范围无效');g.startFrame=a;g.endFrame=b;});for(const g of groups){if((modeFor(g)!=='subtitle-only'&&!g.visual)||(modeFor(g)!=='visual-only'&&!g.subtitle))throw Error(g.id+'：请先在活动组件中选择对应机制，或校正构成类型。')} const r=await fetch(api,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload())});const d=await r.json();if(!r.ok)throw Error(d.error);dirty=false;$('#status').textContent='已保存到项目：'+d.path;}catch(e){$('#status').textContent='项目保存失败，浏览器缓存仍在。可下载 JSON 备份。'+e.message}}
$('#save').onclick=save;
$('#download').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(payload(),null,2)],{type:'application/json'}));a.download='动效边界与合并标注.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
$('#undo').onclick=()=>{if(undoStack.length){groups=JSON.parse(undoStack.pop());cache();render()}};
$('#mode-filter')?.addEventListener('change',updateModes);
async function init(){try{meta=await (await fetch('metadata.json?manual-review=1')).json();FPS=meta.fps||30;TOTAL=meta.totalFrames||1218;KEY=(meta.projectKey||'motion-review')+'-manual-review-v1';let server=null;try{server=await (await fetch(api)).json()}catch(e){}let local=null;try{local=JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){}const latest=server?.groups?server:null;const preferLocal=local?.groups&&(!latest||Date.parse(local.updatedAt)>Date.parse(latest.updatedAt||latest.savedAt));
 groups=structuredClone(preferLocal?local.groups:latest?.groups||(meta.reviewedOccurrences||meta.completeGroups).map(g=>{const [a,b]=g.timecode.split('-').map(parseTC);return {...g,name:g.name||'待校正动效',members:g.members||[g.id],startFrame:g.startFrame??Math.round(a*FPS),endFrame:g.endFrame??Math.min(TOTAL,Math.round(b*FPS)),note:g.note||''}}));groups=reconcileAppliedFeedback(groups,preferLocal?local:latest);render();$('#status').textContent=`已载入 ${groups.length} 条${preferLocal?'浏览器缓存':latest?(meta.feedbackReceipt?'反馈修订稿（保留原标注）':'用户项目标注'):'待校正草稿'}；可逐帧调整并保存`;
 const families=$('#families');families.innerHTML='<details><summary>查看画面与字幕分类草稿（尚未验收）</summary><pre>'+esc((meta.visualFamilies||[]).map(f=>f.id+' '+f.name).join('\n')+'\n\n'+(meta.subtitleFamilies||[]).map(f=>f.id+' '+f.name).join('\n'))+'</pre></details>';
 const feedback=$('#feedback');if(feedback&&meta.firstPassOverview&&!meta.feedbackReceipt){feedback.innerHTML='<h2>新视频独立首轮拆解</h2><p>'+esc(meta.firstPassOverview.message)+'</p><p>候选 '+meta.firstPassOverview.counts.groups+' 组；仅画面 '+meta.firstPassOverview.counts.visualOnly+'；仅字幕 '+meta.firstPassOverview.counts.subtitleOnly+'；组合 '+meta.firstPassOverview.counts.combined+'。</p><p>每卡可逐帧、改边界、改名、改构成、合并、备注并保存。未完成：'+meta.firstPassOverview.limits.map(esc).join('、')+'</p>';};if(feedback&&meta.feedbackReceipt){feedback.innerHTML='<h2>技能测试与用户反馈修订</h2><p>已保留 '+meta.feedbackReceipt.annotationCount+' 条原始标注，按你的备注归并 '+meta.feedbackReceipt.completeGroupCount+' 个完整组。标注应用不等于机制验收，当前不进入复刻。拆分、合并、排除后的当前数量以此处为准。</p>'+meta.feedbackReceipt.lessons.map(l=>'<details open><summary>'+esc(l.source.join('、'))+'</summary><p>'+esc(l.lesson)+'</p></details>').join('')+'<h2>画面动效与字幕动效如何搭配表达</h2>'+(meta.pairings||[]).map(p=>'<details><summary>'+esc(p.visual)+'</summary><p>可与本片已观察的字幕机制搭配：'+(p.withSubtitles.length?p.withSubtitles.map(esc).join('、'):'无独立字幕组件；普通主字幕不计入')+'</p><p>'+esc(p.purpose)+'</p><p class="muted">依据：'+p.evidence.map(esc).join('、')+'；跨内容复用尚未验证。</p></details>').join('');}
 }catch(e){$('#status').textContent='载入失败：'+e.message}}
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue=''}});init();

function installComponentEditors(card,g,describe){
 const box=document.createElement('details');box.className='component-edit';box.innerHTML='<summary>手动校正活动组件、表达目的和接力</summary>';
 for(const [kind,label,list] of [['visual','画面活动组件',meta.visualFamilies],['subtitle','字幕活动组件',meta.subtitleFamilies]]){
  if((kind==='visual'&&modeFor(g)==='subtitle-only')||(kind==='subtitle'&&modeFor(g)==='visual-only'))continue;
  const lab=document.createElement('label');lab.textContent=label+'（可多选）';const select=document.createElement('select');select.multiple=true;select.setAttribute('aria-label',label);
  for(const f of list||[]){const o=document.createElement('option');o.value=f.id;o.textContent=f.id+' '+f.name;o.selected=(g[kind+'Components']||[g[kind]]).includes(f.id);select.appendChild(o)}
  select.onchange=()=>{g[kind+'Components']=Array.from(select.selectedOptions).map(o=>o.value);g[kind]=g[kind+'Components'][0]||null;describe();cache()};lab.appendChild(select);box.appendChild(lab);
 }
 for(const [key,label] of [['purpose','表达目的'],['relation','阶段与接力']]){const lab=document.createElement('label');lab.textContent=label;const input=document.createElement('input');input.value=g[key]||meta.feedbackAnalysis?.[g.id]?.[key]||'';input.setAttribute('aria-label',label);input.oninput=()=>{g[key]=input.value;describe();cache()};lab.appendChild(input);box.appendChild(lab)}
 card.querySelector('.card-head').appendChild(box);
}

function reconcileAppliedFeedback(current,source){
 const receipt=meta.feedbackReceipt;if(!receipt)return current;
 const revision=meta.classificationRevision;
 const allCurrent=current.length&&current.every(g=>g.classificationRevision===revision);
 const appliedAt=Date.parse(receipt.sourceUpdatedAt||receipt.sourceSavedAt||0);
 const sourceAt=Date.parse(source?.updatedAt||source?.savedAt||0);
 if(!allCurrent && (!source || !Number.isFinite(sourceAt) || sourceAt<=appliedAt))return structuredClone(meta.reviewedOccurrences||meta.completeGroups);
 const excluded=new Set((receipt.excluded||[]).map(x=>x.id));
 const splitParents=new Map((receipt.splits||[]).map(x=>[x.id,x]));
 const canonical=new Map((meta.reviewedOccurrences||meta.completeGroups).map(g=>[g.id,g]));
 const retired=new Set((meta.reviewedOccurrences||meta.completeGroups).flatMap(g=>g.members||[]).filter(id=>!canonical.has(id)&&!splitParents.has(id)));
 const result=[];
 for(const saved of current){
  if(excluded.has(saved.id)||retired.has(saved.id))continue;
  if(splitParents.has(saved.id)){for(const child of splitParents.get(saved.id).children){if(!current.some(g=>g.id===child.id)&&canonical.has(child.id))result.push(structuredClone(canonical.get(child.id)))}continue}
  result.push(saved);
 }
 return result;
}
