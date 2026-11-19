// 轻量客户端搜索：加载索引，按标题/正文匹配，展示前 8 条
(function () {
  var q = document.getElementById('q');
  var box = document.getElementById('results');
  if (!q || !box) return;
  var index = [];
  fetch('assets/search-index.json').then(function (r) { return r.json(); })
    .then(function (data) { index = data; }).catch(function () {});

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
    });
  }

  q.addEventListener('input', function () {
    var term = q.value.trim().toLowerCase();
    if (!term) { box.innerHTML = ''; return; }
    var hits = index.filter(function (it) {
      return it.title.toLowerCase().indexOf(term) >= 0 ||
             it.text.toLowerCase().indexOf(term) >= 0;
    }).slice(0, 8);
    if (!hits.length) { box.innerHTML = '<small>无匹配</small>'; return; }
    box.innerHTML = hits.map(function (it) {
      var pos = it.text.toLowerCase().indexOf(term);
      var snippet = pos >= 0
        ? it.text.slice(Math.max(0, pos - 30), pos + 60)
        : it.title;
      return '<a href="' + it.url + '">' + esc(it.title) +
             '<br><small>' + esc(snippet) + '…</small></a>';
    }).join('');
  });
})();
