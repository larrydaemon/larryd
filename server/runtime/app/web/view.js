/* THE HOST OF AN AGENT'S OWN VIEW (the developer's shelf; the platform's host does the same): a card's hire button
   (data-hire, aria-pressed) inside the view's shadow root becomes this page's own hire post (#mk-hire, its token).
   Nothing of the view is read as code: only the button's two attributes, as text. */
(function () {
  var form = document.getElementById('mk-hire');
  if (!form) return;
  document.querySelectorAll('.mk-view').forEach(function (host) {
    var root = host.shadowRoot;
    if (!root) return;
    root.addEventListener('click', function (e) {
      var button = e.target && e.target.closest ? e.target.closest('button[data-hire]') : null;
      if (!button) return;
      e.preventDefault();
      form.elements.key.value = button.getAttribute('data-hire') || '';
      form.elements.value.value = button.getAttribute('aria-pressed') === 'true' ? 'off' : 'on';
      form.submit();
    });
  });
})();
