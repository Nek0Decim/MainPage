(() => {
  'use strict';
  const publications = window.TWORCZOSC_CONTENT?.publications;
  if (!Array.isArray(publications)) return;
  const publication = publications.find(item => typeof item?.title === 'string' && item.title.trim());
  if (!publication) return;
  const section = document.getElementById('studio-publication');
  const title = document.getElementById('studio-publication-title');
  const description = document.getElementById('studio-publication-desc');
  const link = document.getElementById('studio-publication-link');
  if (!section || !title || !description || !link) return;
  title.textContent = publication.title.trim();
  description.textContent = typeof publication.description === 'string' ? publication.description.trim() : '';
  description.hidden = !description.textContent;
  if (typeof publication.url === 'string' && /^https:\/\/[^\s]+$/i.test(publication.url.trim())) {
    link.href = publication.url.trim();
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
  }
  section.hidden = false;
})();
