'use strict';
const $ = id => document.getElementById(id);
let state = {key:'', posts:[], publications:[], mode:'articles', selected:null, cover:'', dirty:false};
function notice(message, error=false) { const ok=$('success-banner'),bad=$('error-banner'); ok.hidden=true;bad.hidden=true;const box=error?bad:ok;box.textContent=message;box.hidden=false; box.scrollIntoView({block:'nearest',behavior:'smooth'}); }
function clearNotices(){ $('success-banner').hidden=true; $('error-banner').hidden=true; }
async function post(path, value, binary=false) {
  const options={method:'POST',headers:{'X-Editor-Key':state.key}};
  if(binary){options.body=value.data;}else{options.body=JSON.stringify(value);options.headers['Content-Type']='application/json';}
  const r=await fetch(path,options);
  const json=await r.json().catch(()=>({error:'Błąd odpowiedzi serwera.'}));
  if(!r.ok || json.error) throw new Error(json.error||`Błąd ${r.status}`);
  return json;
}
function safeSlug(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l').replace(/Ł/g,'L').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,75);}
const today=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
function getArticle(){return {id:state.selected?.id||'',title:$('title').value,category:$('category').value,publishedAt:$('publishedAt').value,slug:$('slug').value,lead:$('lead').value,body:$('body').value,cover:state.cover};}
function getPublication(){return {id:state.selected?.id||'',title:$('pub-title').value,system:$('pub-system').value,format:$('pub-format').value,description:$('pub-description').value,url:$('pub-url').value,cover:state.cover};}
function coverPreview(id,path){const box=$(id);box.replaceChildren();if(path){let img=document.createElement('img');img.src='/view/'+path;img.alt='Podgląd okładki';box.append(img);}else{box.textContent='✦';}}
function setDirty(value){state.dirty=value;document.title=(value?'● ':'')+'Pracownia publikacji · RPG';}
function askUnsaved(){return !state.dirty||window.confirm('Masz niezapisane zmiany. Odrzucić je?');}
function newEntry(force=false){if(!force&&!askUnsaved())return;state.selected=null;state.cover='';clearNotices();if(state.mode==='articles'){
  $('article-form').reset();$('publishedAt').value=today();$('slug').readOnly=false;delete $('slug').dataset.userEdited;$('editor-heading').textContent='Nowy artykuł';$('status-pill').textContent='Nowy szkic';$('publish').textContent='Opublikuj artykuł ↗';$('save-draft').textContent='Zapisz szkic';$('unpublish').hidden=true;$('delete-draft').hidden=true;$('open-article').hidden=true;coverPreview('cover-box','');$('preview-area').innerHTML='<p class="preview-placeholder">Wpisz treść i kliknij „Odśwież podgląd”.</p>';wordCount();
} else {$('publication-form').reset();coverPreview('pub-cover-box','');$('editor-heading').textContent='Nowa publikacja';$('status-pill').textContent='Nowy produkt';$('delete-publication').hidden=true;}
  setDirty(false);renderList();}
function selectEntry(entry){if(!askUnsaved())return;state.selected={...entry};state.cover=entry.cover||'';clearNotices();if(state.mode==='articles'){
  for(const key of ['title','category','publishedAt','slug','lead','body']) $(key).value=entry[key]||'';
  $('slug').readOnly=entry.status==='published';$('editor-heading').textContent=entry.title;
  $('status-pill').textContent=entry.status==='published'?'Opublikowany':'Szkic';
  $('publish').textContent=entry.status==='published'?'Zaktualizuj artykuł ↗':'Opublikuj artykuł ↗';$('save-draft').textContent=entry.status==='published'?'Zapisz zmiany':'Zapisz szkic';
  $('open-article').hidden=entry.status!=='published';$('unpublish').hidden=entry.status!=='published';$('delete-draft').hidden=entry.status!=='draft';
  coverPreview('cover-box',state.cover);updatePreview();wordCount();
} else {
  for(const key of ['title','system','format','description','url']) $('pub-'+key).value=entry[key]||'';
  coverPreview('pub-cover-box',state.cover);$('editor-heading').textContent=entry.title;
  $('status-pill').textContent='W katalogu';$('delete-publication').hidden=false;
}
  setDirty(false);renderList();}
function renderList(){let items=state.mode==='articles'?state.posts:state.publications;const filter=$('list-search').value.toLocaleLowerCase('pl').trim();items=items.filter(p=>[p.title,p.category,p.system,p.format].filter(Boolean).join(' ').toLocaleLowerCase('pl').includes(filter));
  $('items-count').textContent=String(items.length);
  let target=$('post-list');target.replaceChildren();if(!items.length){const p=document.createElement('p');p.className='empty-list';p.textContent='Na razie brak wpisów. Kliknij przycisk powyżej, aby utworzyć pierwszy.';target.append(p);return;}
  for(const item of items){let btn=document.createElement('button');btn.className='post-row'+(item.id===state.selected?.id?' selected':'');btn.type='button';let name=document.createElement('span');name.className='post-title';name.textContent=item.title;let meta=document.createElement('span');meta.className='post-meta';let badge=document.createElement('span');badge.className='status-tag '+(item.status||'published');badge.textContent=state.mode==='articles'?(item.status==='draft'?'Szkic':'Opublikowany'):'Publikacja';meta.append(badge);let date=document.createElement('span');date.textContent=item.publishedAt||item.system||'';meta.append(date);btn.append(name,meta);btn.addEventListener('click',()=>selectEntry(item));target.append(btn);}
}
function switchTab(next){if(next===state.mode)return;if(!askUnsaved())return;state.mode=next;state.selected=null;state.cover='';$('article-form').hidden=next!=='articles';$('publication-form').hidden=next!=='publications';for(const b of document.querySelectorAll('[data-tab]')){const active=b.dataset.tab===next;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));}
  $('editor-subtitle').textContent=next==='articles'?'ZAPISKI MISTRZA GRY':'WYDAWNICTWO RPG';$('list-heading').textContent=next==='articles'?'Twoje wpisy':'Twoje publikacje';$('new-btn').textContent=next==='articles'?'＋ Nowy artykuł':'＋ Nowa publikacja';$('list-search').value='';newEntry(true);}
function wordCount(){const words=$('body').value.trim().split(/\s+/).filter(Boolean).length;$('word-count').textContent=`${words} słów · szacunkowo ${Math.max(1,Math.ceil(words/200))} min czytania`;}
let previewTimer;
async function updatePreview(){try{const result=await post('/api/preview',{body:$('body').value});$('preview-area').innerHTML=result.html||'<p class="preview-placeholder">Podgląd będzie widoczny tutaj.</p>'; }catch(err){notice(err.message,true);}}
function formatText(type){const t=$('body'),start=t.selectionStart,end=t.selectionEnd,selected=t.value.slice(start,end);let replacement='';const sample=selected||'Twój tekst';
 switch(type){case 'heading':replacement='## '+sample;break;case 'subheading':replacement='### '+sample;break;case 'bold':replacement='**'+sample+'**';break;case 'italic':replacement='*'+sample+'*';break;case 'quote':replacement='> '+sample;break;case 'list':replacement='- '+sample;break;case 'link':replacement='['+sample+'](https://)';break;case 'rule':replacement='\n---\n';}
 t.setRangeText(replacement,start,end,'end');t.focus();setDirty(true);wordCount();}
async function reload(selectId=null){const response=await fetch('/api/data');const data=await response.json();state.key=data.key;state.posts=data.articles||[];state.publications=data.publications||[];if(data.error)notice(data.error,true);if(selectId){const list=state.mode==='articles'?state.posts:state.publications;const p=list.find(p=>p.id===selectId);if(p){state.selected=null;selectEntry(p);return;}}renderList();}
async function saveArticle(publish){clearNotices();const values=getArticle();if(!values.slug)values.slug=safeSlug(values.title);try{
  const result=await post(publish?'/api/publish':'/api/save-draft',values);setDirty(false);await reload(result.id);notice(publish?'Artykuł został opublikowany. Gotowe pliki czekają na commit do GitHuba.':result.status==='published'?'Opublikowany artykuł zaktualizowany na dysku.':'Szkic zapisany lokalnie (nie trafi do GitHuba).');setDirty(false);
}catch(err){notice(err.message,true);}}
async function imageUpload(file, pub){if(!file)return;if(file.size>3_000_000){notice('Plik jest za duży (maks. 3 MB).',true);return;}
try{const result=await post('/api/upload?name='+encodeURIComponent(file.name),{data:file},true);state.cover=result.cover;coverPreview(pub?'pub-cover-box':'cover-box',state.cover);setDirty(true);notice('Zdjęcie zostało zapisane w folderze images/blog/. Zapisz wpis, aby przypisać okładkę.');}catch(err){notice(err.message,true);}}
async function savePublication(){try{const data=await post('/api/save-publication',getPublication());setDirty(false);await reload(data.id);setDirty(false);notice('Publikacja została zapisana. Lista w „Twórczości” jest zaktualizowana.');}catch(err){notice(err.message,true);}}
async function unpublish(){if(!state.selected||!confirm('Wycofać artykuł ze strony? Zostanie zachowany jako szkic lokalny, a jego strona HTML zniknie z projektu.'))return;try{const id=state.selected.id;await post('/api/unpublish',{id});setDirty(false);await reload(id);notice('Artykuł został wycofany i zapisany jako szkic lokalny.');}catch(err){notice(err.message,true);}}
async function deleteDraft(){if(!state.selected||!confirm('Trwale usunąć ten lokalny szkic?'))return;try{await post('/api/delete-draft',{id:state.selected.id});await reload();newEntry(true);notice('Szkic został usunięty.');}catch(err){notice(err.message,true);}}
async function deletePublication(){if(!state.selected||!confirm('Usunąć publikację z listy na stronie? Nie usunie to jej ze sklepu.'))return;try{await post('/api/delete-publication',{id:state.selected.id});await reload();newEntry(true);notice('Publikacja została usunięta z listy.');}catch(err){notice(err.message,true);}}
async function boot(){await reload();newEntry(true);$('new-btn').addEventListener('click',()=>newEntry());$('list-search').addEventListener('input',renderList);document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));
  $('title').addEventListener('input',()=>{if(!state.selected && (!$('slug').dataset.userEdited||$('slug').value===safeSlug($('title').dataset.previous||''))) $('slug').value=safeSlug($('title').value);$('title').dataset.previous=$('title').value;});
  $('slug').addEventListener('input',()=>{$('slug').dataset.userEdited='yes'});
  $('body').addEventListener('input',()=>{wordCount();clearTimeout(previewTimer);previewTimer=setTimeout(updatePreview,650)});
  for(const name of ['article-form','publication-form']){$(name).addEventListener('input',()=>setDirty(true));}
  document.querySelectorAll('[data-format]').forEach(b=>b.addEventListener('click',()=>formatText(b.dataset.format)));
  $('preview-btn').addEventListener('click',updatePreview);$('save-draft').addEventListener('click',()=>saveArticle(false));$('publish').addEventListener('click',()=>saveArticle(true));
  $('open-article').addEventListener('click',()=>{if(state.selected?.slug)window.open('/view/wpisy/'+state.selected.slug+'.html','_blank','noopener');});
  $('unpublish').addEventListener('click',unpublish);$('delete-draft').addEventListener('click',deleteDraft);
  $('cover-upload').addEventListener('change',e=>imageUpload(e.target.files[0],false));$('remove-cover').addEventListener('click',()=>{state.cover='';coverPreview('cover-box','');setDirty(true)});
  $('pub-cover-upload').addEventListener('change',e=>imageUpload(e.target.files[0],true));$('pub-remove-cover').addEventListener('click',()=>{state.cover='';coverPreview('pub-cover-box','');setDirty(true)});
  $('save-publication').addEventListener('click',savePublication);$('delete-publication').addEventListener('click',deletePublication);
  window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue='';}});
}
boot().catch(err=>notice('Nie udało się uruchomić edytora: '+err.message,true));
