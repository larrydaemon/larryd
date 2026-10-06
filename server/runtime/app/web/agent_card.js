/* THE ONE AGENT CARD TEMPLATE'S SCRIPT. Each card carries its agent's look as names (data-look, already cleaned by the
   server); this checks every name against the menu AGAIN and only then sets it with style.setProperty (CSP-safe: no
   inline style, no unsafe-inline), pointing at the LIVE variables. Anything not on the menu is dropped. */
(function () {
  var MENU = JSON.parse(document.currentScript.dataset.menu || '{}');
  function on(list, v) { return typeof v === 'string' && Array.isArray(list) && list.indexOf(v) >= 0; }
  function dress(card) {
    var look;
    try { look = JSON.parse(card.dataset.look || '{}'); } catch (e) { look = {}; }
    if (!look || typeof look !== 'object') look = {};
    if (on(MENU.accent, look.accent)) card.style.setProperty('--accent', 'var(--' + look.accent + ')');
    if (on(MENU.radius, look.radius)) card.style.setProperty('--radius', 'var(--' + look.radius + ')');
    if (on(MENU.space, look.space)) card.style.setProperty('--space', 'var(--' + look.space + ')');
    if (on(MENU.effect, look.effect)) { card.style.setProperty('--effect', look.effect); card.dataset.effect = look.effect; }
    var text = look.text && typeof look.text === 'object' ? look.text : {};
    Object.keys(text).forEach(function (part) {
      if (!on(MENU.parts, part) || !on(MENU.roles, text[part])) return;
      card.querySelectorAll('[data-part="' + part + '"]').forEach(function (el) {
        MENU.roles.forEach(function (r) { el.classList.remove(r); });
        el.classList.add(text[part]);
      });
    });
  }
  function all(root) {
    root.querySelectorAll('.agent-card[data-look]').forEach(dress);
    root.querySelectorAll('[data-agent-card]').forEach(function (host) { if (host.shadowRoot) all(host.shadowRoot); });
  }
  all(document);
})();
