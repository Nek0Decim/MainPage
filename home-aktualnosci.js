/* Aktualności strony głównej są pobierane z danych edytora. */
(() => {
  'use strict';
  const data=window.TWORCZOSC_CONTENT||{};
  const articles=Array.isArray(data.articles)?data.articles:[];
  const publications=Array.isArray(data.publications)?data.publications:[];
  const urlOK=url=>typeof url==='string' && (/^https?:\/\//i.test(url)||/^(?:[a-z0-9_-]+\/)*[a-z0-9_-]+\.html$/i.test(url));
  const latest=articles.filter(a=>a?.title&&urlOK(a.url)).sort((a,b)=>(b.publishedAt||'').localeCompare(a.publishedAt||''))[0];
  if(latest){
    const banner=document.querySelector('.blog-promo');
    const foot=banner?.querySelector('.blog-promo__footnote');
    const label=banner?.querySelector('.blog-promo__top .mini-label');
    const link=banner?.querySelector('.text-link');
    if(label)label.textContent='Najnowszy artykuł';
    if(foot){foot.replaceChildren();const strong=document.createElement('strong');strong.textContent=latest.title;foot.append(strong);if(latest.lead){const sub=document.createElement('span');sub.textContent=' — '+latest.lead;foot.append(sub);}}
    if(link){link.href=latest.url;link.firstChild.textContent='Czytaj najnowszy wpis ';if(/^https?:\/\//i.test(latest.url)){link.target='_blank';link.rel='noopener noreferrer';}}
  }
  const first=publications.find(p=>p?.title?.trim());
  if(first){
    const panel=document.querySelector('.creation-feature');
    const title=panel?.querySelector('h3');
    const hint=panel?.querySelector('.creation-feature__hint');
    if(title)title.textContent=first.title;
    if(hint)hint.textContent=first.description||'Zobacz szczegóły wydanej przygody w zakładce „Twórczość”.';
    const mock=panel?.querySelector('.book-mock');
    if(mock){const mockTitle=mock.querySelector('.book-mock__title'); if(mockTitle)mockTitle.textContent=first.title;}
    const goto=panel?.querySelector('.text-link');
    if(goto && urlOK(first.url)){goto.href=first.url;goto.firstChild.textContent='Zobacz wydaną przygodę ';if(/^https?:\/\//i.test(first.url)){goto.target='_blank';goto.rel='noopener noreferrer';}}
    if(typeof first.cover==='string' && /^images\/blog\/[\w.-]+\.(png|jpe?g|webp)$/i.test(first.cover) && mock){
      const img=document.createElement('img');img.src=first.cover;img.alt='Okładka '+first.title;img.loading='lazy';img.className='creation-home-cover';img.addEventListener('load',()=>mock.replaceWith(img),{once:true});
    }
  }
})();
