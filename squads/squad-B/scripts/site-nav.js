(() => {
  const menu = document.querySelector('.menu');
  if (!menu) return;

  const links = [
    ['home.html', 'Home'],
    ['sobre.html', 'Sobre'],
    ['servicos.html', 'Serviços'],
    ['projetos.html', 'Projetos'],
    ['habilidades.html', 'Skills'],
    ['depoimentos.html', 'Depoimentos'],
    ['case-de-sucesso.html', 'Case de sucesso'],
    ['contato.html', 'Contato'],
  ];
  const currentPage = window.location.pathname.split('/').pop() || 'home.html';
  menu.innerHTML = `<ul>${links.map(([href, label]) => {
    const active = href === currentPage || (currentPage === '' && href === 'home.html');
    return `<li><a href="${href}" class="${active ? 'pag-ativa' : ''}" ${active ? 'aria-current="page"' : ''}>${label}</a></li>`;
  }).join('')}</ul>`;
})();
