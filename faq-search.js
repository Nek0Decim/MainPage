// Wyszukiwarka FAQ działa bez bibliotek i bez przesyłania danych na serwer.
(() => {
  const input = document.getElementById('faq-search');
  const clear = document.getElementById('faq-clear');
  const status = document.getElementById('faq-status');
  const empty = document.getElementById('faq-empty');
  if (!input || !clear || !status || !empty) return;
  const groups = Array.from(document.querySelectorAll('[data-faq-group]'));
  const norm = (s) => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pl').trim();
  const update = () => {
    const search = norm(input.value);
    let matches = 0;
    for (const group of groups) {
      let visibleInGroup = 0;
      for (const item of group.querySelectorAll('[data-faq-item]')) {
        const found = !search || norm(item.textContent).includes(search);
        item.hidden = !found;
        if (found) { matches++; visibleInGroup++; }
      }
      group.hidden = visibleInGroup === 0;
    }
    clear.hidden = !input.value;
    empty.hidden = matches > 0;
    status.textContent = search ? (matches === 1 ? 'Znaleziono 1 pytanie.' : `Znaleziono ${matches} pytań.`) : '';
  };
  input.addEventListener('input', update);
  clear.addEventListener('click', () => { input.value = ''; update(); input.focus(); });
  update();
})();
