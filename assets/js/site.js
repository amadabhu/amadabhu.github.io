// Build a sticky TOC from the article's h2 headings, and highlight the active
// section as the user scrolls. Runs only on pages whose layout includes #toc-nav.
(function () {
  var nav = document.getElementById('toc-nav');
  if (!nav) return;

  var article = document.querySelector('article.prose');
  if (!article) return;

  var headings = Array.prototype.slice.call(article.querySelectorAll('h2'));
  if (headings.length === 0) {
    nav.style.display = 'none';
    return;
  }

  var slugify = function (text) {
    return text.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .trim()
      .replace(/\s+/g, '-');
  };

  var links = headings.map(function (h) {
    if (!h.id) h.id = slugify(h.textContent);
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    a.dataset.target = h.id;
    nav.appendChild(a);
    return a;
  });

  var setActive = function (id) {
    links.forEach(function (a) {
      a.classList.toggle('active', a.dataset.target === id);
    });
  };

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) setActive(entry.target.id);
      });
    }, { rootMargin: '-30% 0px -60% 0px', threshold: 0 });
    headings.forEach(function (h) { observer.observe(h); });
  } else {
    setActive(headings[0].id);
  }
})();
