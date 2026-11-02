(() => {
  'use strict';
  const search = document.getElementById('rep-search');
  const system = document.getElementById('rep-system');
  const kind = document.getElementById('rep-kind');
  const reset = document.getElementById('rep-reset');
  const groups = Array.from(document.querySelectorAll('.rep-group'));
  const cards = Array.from(document.querySelectorAll('.rep-card'));
  const result = document.getElementById('rep-results');
  const empty = document.getElementById('rep-empty');
  const fold = value => (value || '').toLocaleLowerCase('pl-PL').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
  const update = () => {
    const q=fold(search.value);
    let count=0;
    for(const card of cards){
      const show=(!q || fold(card.dataset.title).includes(q)) &&
        (system.value === 'all' || card.dataset.system === system.value) &&
        (kind.value === 'all' || card.dataset.kind === kind.value);
      card.hidden=!show;
      if(show) count++;
    }
    for(const group of groups){
      group.hidden=!Array.from(group.querySelectorAll('.rep-card')).some(c=>!c.hidden);
    }
    result.textContent=`Wyświetlono ${count} z ${cards.length} przygód`;
    empty.hidden = count !== 0;
  };
  for(const el of [search,system,kind]){
    el.addEventListener('input',update);
    el.addEventListener('change',update);
  }
  reset.addEventListener('click',() => { document.getElementById('rep-filters').reset(); update(); });
  update();
})();
