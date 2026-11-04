(() => {
  "use strict";
  const content = window.TWORCZOSC_CONTENT || {};
  const publications = Array.isArray(content.publications) ? content.publications : [];
  const articles = Array.isArray(content.articles) ? content.articles : [];
  const validUrl = (value) => {
    if (typeof value !== 'string' || !value.trim()) return null;
    const url = value.trim();
    if (/^https?:\/\//i.test(url)) return url;
    if (/^(?:[a-z0-9_-]+\/)*[a-z0-9_-]+\.html(?:#[a-z0-9_-]+)?$/i.test(url)) return url;
    return null;
  };
  const addTextTag = (container, text) => {
    if (!text) return;
    const tag = document.createElement('span');
    tag.textContent = text;
    container.append(tag);
  };
  const first = publications[0];
  if (first && first.title && first.title.trim()) {
    const title = document.querySelector('#featured-title');
    const description = document.querySelector('#featured-description');
    const tags = document.querySelector('#featured-tags');
    const link = document.querySelector('#featured-link');
    const notice = document.querySelector('#featured-notice');
    title.textContent = first.title;
    if (first.description?.trim()) description.textContent = first.description.trim();
    tags.replaceChildren();
    addTextTag(tags, first.system);
    addTextTag(tags, first.format);
    if (!first.system && !first.format) addTextTag(tags, 'Scenariusz RPG');
    const url = validUrl(first.url);
    if (url) {
      link.href = url;
      link.firstChild.textContent = 'Zobacz publikację ';
      if (/^https?:\/\//i.test(url)) {
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
      }
      notice.hidden = true;
    } else {
      notice.textContent = 'Odnośnik do publikacji zostanie dodany wkrótce.';
    }
    if (typeof first.cover === 'string' && /^(?:images\/)[\w\-./]+\.(?:png|jpe?g|webp)$/i.test(first.cover)) {
      const art = document.querySelector('#featured-art');
      const cover = document.createElement('img');
      cover.className = 'creation-featured__cover';
      cover.alt = 'Okładka publikacji „' + first.title + '”';
      cover.loading = 'lazy';
      cover.src = first.cover;
      cover.addEventListener('load', () => { document.querySelector('#featured-book-placeholder').hidden = true; }, { once:true });
      cover.addEventListener('error', () => cover.remove(), { once:true });
      art.append(cover);
    }
  }
  if (publications.length > 1) {
    const grid = document.querySelector('#other-publications');
    publications.slice(1).filter(item => item?.title?.trim()).forEach(item => {
      const card = document.createElement('article');
      card.className = 'creation-more-card';
      const imgPattern = /^(?:images\/)[\w\-./]+\.(?:png|jpe?g|webp)$/i;
      if (item.cover && imgPattern.test(item.cover)) {
        const img = document.createElement('img'); img.src = item.cover; img.alt = 'Okładka publikacji „'+item.title+'”'; img.loading = 'lazy'; img.className = 'creation-more-card__image'; card.append(img);
      } else {
        const placeholder = document.createElement('div'); placeholder.className = 'creation-more-card__placeholder'; placeholder.textContent = '✦'; placeholder.setAttribute('aria-hidden','true'); card.append(placeholder);
      }
      const body = document.createElement('div'); body.className = 'creation-more-card__body';
      const label = document.createElement('p'); label.className = 'mini-label'; label.textContent = [item.system,item.format].filter(Boolean).join(' · ') || 'Scenariusz RPG'; body.append(label);
      const heading = document.createElement('h4'); heading.textContent = item.title; body.append(heading);
      if (item.description) { const desc = document.createElement('p'); desc.textContent = item.description; body.append(desc); }
      const linkUrl = validUrl(item.url);
      if (linkUrl) {
        const link = document.createElement('a'); link.href = linkUrl; link.className = 'text-link'; link.textContent = 'Zobacz publikację ↗';
        if (/^https?:\/\//i.test(linkUrl)) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
        body.append(link);
      }
      card.append(body);grid.append(card);
    });
    grid.hidden = !grid.children.length;
  }

  const isArticle = article => article?.title?.trim() && article?.lead?.trim() && validUrl(article.url);
  const available = articles.filter(isArticle).sort((a,b) => (b.publishedAt||'').localeCompare(a.publishedAt||''));
  if (!available.length) return;
  const filters = document.querySelector('#article-filters');
  const results = document.querySelector('#articles-list');
  const empty = document.querySelector('#articles-empty');
  const noMatch = document.querySelector('#articles-no-match');
  const count = document.querySelector('#articles-count');
  const search = document.querySelector('#article-search');
  const buttons = [...document.querySelectorAll('[data-article-category]')];
  filters.hidden = false; results.hidden = false; empty.hidden = true;
  let category = 'Wszystkie';
  const render = () => {
    const q = search.value.toLocaleLowerCase('pl').trim();
    const items = available.filter(article =>
      (category === 'Wszystkie' || article.category === category) &&
      [article.title,article.lead,article.category].join(' ').toLocaleLowerCase('pl').includes(q)
    );
    results.replaceChildren();
    items.forEach(article => {
      const card = document.createElement('article'); card.className = 'creation-article-card';
      const label = document.createElement('p'); label.className = 'creation-article-card__category'; label.textContent = article.category || 'Zapiski Mistrza Gry'; card.append(label);
      const h = document.createElement('h4'); h.textContent = article.title; card.append(h);
      const desc = document.createElement('p'); desc.textContent = article.lead; card.append(desc);
      const meta = document.createElement('div'); meta.className = 'creation-article-card__meta';
      if (/^\d{4}-\d{2}-\d{2}$/.test(article.publishedAt||'')) {
        const time = document.createElement('time'); time.dateTime = article.publishedAt;
        time.textContent = new Date(article.publishedAt+'T12:00:00').toLocaleDateString('pl-PL', {year:'numeric',month:'long',day:'numeric'}); meta.append(time);
      }
      if (article.readTime) { const t = document.createElement('span'); t.textContent = '· '+article.readTime;meta.append(t); }
      card.append(meta);
      const link = document.createElement('a'); link.className = 'text-link'; link.href = validUrl(article.url); link.textContent = 'Czytaj artykuł ↗';
      if (/^https?:\/\//i.test(link.href)) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
      card.append(link); results.append(card);
    });
    results.hidden = !items.length; noMatch.hidden = !!items.length;
    count.textContent = `Wyświetlono ${items.length} z ${available.length} wpisów`;
  };
  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.articleCategory;
    buttons.forEach(b => { const selected = b===button; b.classList.toggle('is-selected',selected); b.setAttribute('aria-pressed',String(selected)); });
    render();
  }));
  search.addEventListener('input',render);
  render();
})();
