(function () {
  const TOKEN_KEY = "tips_access_token";
  const TZ_STORAGE_KEY = "tips_tz";

  const $ = (id) => document.getElementById(id);

  function detectBrowserTimeZone() {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
    } catch {
      return "UTC";
    }
  }

  function getSavedTimeZone() {
    const raw = localStorage.getItem(TZ_STORAGE_KEY);
    if (raw && raw.trim()) return raw.trim();
    return detectBrowserTimeZone();
  }

  function persistTimeZone(tz) {
    const t = (tz || "").trim();
    if (t) localStorage.setItem(TZ_STORAGE_KEY, t);
    else localStorage.removeItem(TZ_STORAGE_KEY);
  }

  function initTimeZoneField() {
    const el = $("tz");
    if (!el) return;
    el.value = getSavedTimeZone();
  }

  let historyPage = 1;
  let historyLastTotal = 0;
  let historyLastSize = 10;
  let userLocale = "es";
  let currentIsAdmin = false;

  const flash = $("flash");
  const authLoggedOut = $("auth-logged-out");
  const authLoggedIn = $("auth-logged-in");
  const appSection = $("app-section");

  function showFlash(message, kind) {
    flash.hidden = false;
    flash.textContent = message;
    flash.className = "flash " + (kind === "ok" ? "ok" : "error");
  }

  function clearFlash() {
    flash.hidden = true;
    flash.textContent = "";
    flash.className = "flash";
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(t) {
    if (t) localStorage.setItem(TOKEN_KEY, t);
    else localStorage.removeItem(TOKEN_KEY);
  }

  function authHeaders() {
    const t = getToken();
    const h = { "Content-Type": "application/json" };
    if (t) h.Authorization = "Bearer " + t;
    return h;
  }

  async function api(path, options = {}) {
    const res = await fetch(path, {
      ...options,
      headers: { ...authHeaders(), ...(options.headers || {}) },
    });
    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }
    if (!res.ok) {
      const detail =
        data && data.detail !== undefined
          ? typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
          : res.statusText;
      throw new Error(detail || "Error de red");
    }
    return data;
  }

  function setAuthTab(registerActive) {
    const tabReg = $("tab-register");
    const tabLog = $("tab-login");
    const panelReg = $("panel-register");
    const panelLog = $("panel-login");
    tabReg.classList.toggle("active", registerActive);
    tabLog.classList.toggle("active", !registerActive);
    tabReg.setAttribute("aria-selected", registerActive ? "true" : "false");
    tabLog.setAttribute("aria-selected", registerActive ? "false" : "true");
    panelReg.hidden = !registerActive;
    panelLog.hidden = registerActive;
  }

  function updateAuthUi() {
    const t = getToken();
    if (t) {
      authLoggedOut.hidden = true;
      authLoggedIn.hidden = false;
      appSection.hidden = false;
    } else {
      authLoggedOut.hidden = false;
      authLoggedIn.hidden = true;
      appSection.hidden = true;
      $("user-email").textContent = "";
      currentIsAdmin = false;
      const badge = $("admin-badge");
      if (badge) badge.hidden = true;
      const adSec = $("admin-section");
      if (adSec) adSec.hidden = true;
      const adminList = $("admin-tips-list");
      if (adminList) adminList.innerHTML = "";
    }
  }

  function applyMeToPreferencesUi(me) {
    userLocale = (me && me.locale) || "es";
    const locSel = $("pref-locale");
    if (locSel) {
      const v = userLocale;
      if ([...locSel.options].some((o) => o.value === v)) locSel.value = v;
      else locSel.value = "es";
    }
    const tzEl = $("tz");
    if (!tzEl) return;
    if (me && me.iana_timezone && String(me.iana_timezone).trim()) {
      tzEl.value = String(me.iana_timezone).trim();
      persistTimeZone(tzEl.value);
    } else {
      tzEl.value = getSavedTimeZone();
    }
  }

  async function refreshMe() {
    if (!getToken()) return;
    try {
      const me = await api("/auth/me", { method: "GET" });
      $("user-email").textContent = me.email || "";
      applyMeToPreferencesUi(me);
      currentIsAdmin = Boolean(me.is_admin);
      const badge = $("admin-badge");
      if (badge) badge.hidden = !currentIsAdmin;
      const adSec = $("admin-section");
      if (adSec) adSec.hidden = !currentIsAdmin;
      if (currentIsAdmin) {
        await loadAdminTips();
      }
    } catch (e) {
      setToken(null);
      updateAuthUi();
      showFlash(e.message || "Sesión no válida", "error");
    }
  }

  async function loadAdminTips() {
    if (!getToken() || !currentIsAdmin) return;
    const host = $("admin-tips-list");
    if (!host) return;
    host.innerHTML = '<p class="empty">Cargando…</p>';
    try {
      const st = ($("admin-tip-status").value || "").trim();
      const q = new URLSearchParams({ page: "1", size: "50" });
      if (st) q.set("status", st);
      const data = await api("/admin/tips?" + q.toString(), { method: "GET" });
      host.innerHTML = "";
      if (!data.items || !data.items.length) {
        host.innerHTML =
          '<p class="empty">No hay tips con este filtro.</p>';
        return;
      }
      for (const tip of data.items) {
        const row = document.createElement("div");
        row.className = "admin-tip-row";
        const meta = document.createElement("div");
        meta.className = "admin-meta";
        const idSpan = document.createElement("span");
        idSpan.textContent = "ID " + tip.id;
        const topicSpan = document.createElement("span");
        topicSpan.textContent = "Tema " + tip.topic_id;
        const pill = document.createElement("span");
        const stVal = tip.status || "published";
        pill.className = "status-pill " + stVal;
        pill.textContent = stVal;
        meta.appendChild(idSpan);
        meta.appendChild(topicSpan);
        meta.appendChild(pill);
        row.appendChild(meta);
        const h = document.createElement("h3");
        h.textContent = tip.title;
        row.appendChild(h);
        const prev = document.createElement("p");
        prev.className = "preview";
        const bodyText = (tip.body || "").replace(/\s+/g, " ").trim();
        prev.textContent =
          bodyText.length > 160 ? bodyText.slice(0, 160) + "…" : bodyText;
        row.appendChild(prev);
        const actions = document.createElement("div");
        actions.className = "admin-actions";
        function addBtn(label, statusVal) {
          const b = document.createElement("button");
          b.type = "button";
          b.className = "btn small secondary";
          b.textContent = label;
          b.addEventListener("click", () =>
            setAdminTipStatus(tip.id, statusVal)
          );
          actions.appendChild(b);
        }
        addBtn("Publicar", "published");
        addBtn("Borrador", "draft");
        addBtn("Ocultar", "hidden");
        row.appendChild(actions);
        host.appendChild(row);
      }
    } catch (e) {
      host.innerHTML = "";
      showFlash(e.message, "error");
    }
  }

  async function setAdminTipStatus(tipId, status) {
    try {
      clearFlash();
      await api(
        "/admin/tips/" +
          tipId +
          "/status?status=" +
          encodeURIComponent(status),
        { method: "PATCH" }
      );
      showFlash("Estado actualizado.", "ok");
      await loadAdminTips();
    } catch (e) {
      showFlash(e.message, "error");
    }
  }

  function fillHistoryTopicSelect(topics) {
    const sel = $("history-topic-select");
    const prev = sel.value;
    sel.innerHTML = '<option value="">Todos</option>';
    for (const topic of topics) {
      const o = document.createElement("option");
      o.value = String(topic.id);
      o.textContent = topic.name;
      sel.appendChild(o);
    }
    if (prev && [...sel.options].some((opt) => opt.value === prev)) {
      sel.value = prev;
    }
  }

  function formatDeliveredAt(iso) {
    try {
      const d = new Date(iso);
      const loc = userLocale && userLocale.length ? userLocale : "es";
      return d.toLocaleString(loc, {
        dateStyle: "short",
        timeStyle: "short",
      });
    } catch {
      return iso;
    }
  }

  function updateHistoryPagination() {
    const pag = $("history-pagination");
    const totalPages = Math.max(
      1,
      Math.ceil(historyLastTotal / historyLastSize) || 1
    );
    if (historyLastTotal === 0) {
      pag.hidden = true;
      return;
    }
    pag.hidden = false;
    $("history-page-info").textContent =
      "Página " + historyPage + " de " + totalPages + " · " + historyLastTotal + " envíos";
    $("btn-history-prev").disabled = historyPage <= 1;
    $("btn-history-next").disabled = historyPage >= totalPages;
  }

  async function loadHistory() {
    const host = $("tips-history");
    const size = parseInt($("history-size").value, 10) || 10;
    historyLastSize = size;
    const topicId = ($("history-topic-select").value || "").trim();
    host.innerHTML = '<p class="empty">Cargando historial…</p>';
    $("history-pagination").hidden = true;

    try {
      const q = new URLSearchParams({
        page: String(historyPage),
        size: String(size),
      });
      if (topicId) q.set("topic_id", topicId);
      const data = await api("/me/tips/history?" + q.toString(), { method: "GET" });
      historyLastTotal = data.total || 0;
      host.innerHTML = "";

      if (!data.items || !data.items.length) {
        host.innerHTML =
          '<p class="empty">No hay envíos en el historial (o ninguno con este filtro).</p>';
        updateHistoryPagination();
        return;
      }

      for (const row of data.items) {
        const card = document.createElement("article");
        card.className = "tip-card";
        const meta = document.createElement("div");
        meta.className = "history-meta";
        const isRead = row.status === "read";
        const badge = document.createElement("span");
        badge.className = "badge-status " + (isRead ? "read" : "unread");
        badge.textContent = isRead ? "Leído" : "No leído";
        const topicPill = document.createElement("span");
        topicPill.className = "topic-pill";
        topicPill.textContent = row.topic ? row.topic.name : "Tema";
        const when = document.createElement("span");
        when.textContent = formatDeliveredAt(row.delivered_at);
        meta.appendChild(badge);
        meta.appendChild(topicPill);
        meta.appendChild(when);
        card.appendChild(meta);

        const h = document.createElement("h3");
        h.textContent = row.tip.title;
        const body = document.createElement("p");
        body.textContent = row.tip.body;
        card.appendChild(h);
        card.appendChild(body);
        if (row.tip.source_url) {
          const a = document.createElement("a");
          a.href = row.tip.source_url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = "Fuente";
          card.appendChild(a);
        }
        if (!isRead) {
          const actions = document.createElement("div");
          actions.className = "history-actions";
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "btn small secondary";
          btn.textContent = "Marcar como leído";
          btn.addEventListener("click", () => markDeliveryRead(row.delivery_id, btn));
          actions.appendChild(btn);
          card.appendChild(actions);
        }
        host.appendChild(card);
      }
      updateHistoryPagination();
    } catch (e) {
      host.innerHTML = "";
      showFlash(e.message, "error");
    }
  }

  async function markDeliveryRead(deliveryId, btn) {
    btn.disabled = true;
    try {
      clearFlash();
      await api("/me/tips/" + deliveryId + "/read", { method: "PATCH" });
      showFlash("Marcado como leído.", "ok");
      await loadHistory();
    } catch (e) {
      showFlash(e.message, "error");
      btn.disabled = false;
    }
  }

  async function loadTopicsAndSubs() {
    clearFlash();
    const topics = await api("/topics?only_active=true&limit=100");
    const subs = await api("/subscriptions/me");
    const subIds = new Set(subs.map((s) => s.topic_id));
    fillHistoryTopicSelect(topics);

    const host = $("topics-list");
    host.innerHTML = "";
    if (!topics.length) {
      host.innerHTML =
        '<p class="empty">No hay temas activos. Crea temas vía API o ejecuta el seed de demo.</p>';
      return;
    }

    for (const topic of topics) {
      const row = document.createElement("div");
      row.className = "topic-row";
      const left = document.createElement("div");
      left.innerHTML =
        "<strong>" +
        escapeHtml(topic.name) +
        '</strong><div class="meta">' +
        escapeHtml(topic.slug) +
        "</div>";
      const right = document.createElement("div");
      if (subIds.has(topic.id)) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn small danger";
        btn.textContent = "Quitar";
        btn.addEventListener("click", () => unsubscribe(topic.id));
        right.appendChild(btn);
      } else {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn small secondary";
        btn.textContent = "Suscribirme";
        btn.addEventListener("click", () => subscribe(topic.id));
        right.appendChild(btn);
      }
      row.appendChild(left);
      row.appendChild(right);
      host.appendChild(row);
    }
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  async function subscribe(topicId) {
    try {
      clearFlash();
      await api("/subscriptions", {
        method: "POST",
        body: JSON.stringify({ topic_id: topicId }),
      });
      await loadTopicsAndSubs();
      historyPage = 1;
      await loadHistory();
      showFlash("Suscripción creada.", "ok");
    } catch (e) {
      showFlash(e.message, "error");
    }
  }

  async function unsubscribe(topicId) {
    try {
      clearFlash();
      await api("/subscriptions", {
        method: "DELETE",
        body: JSON.stringify({ topic_id: topicId }),
      });
      await loadTopicsAndSubs();
      historyPage = 1;
      await loadHistory();
      showFlash("Suscripción eliminada.", "ok");
    } catch (e) {
      showFlash(e.message, "error");
    }
  }

  async function loadTodayTips() {
    const rawTz = ($("tz").value || "").trim();
    const tz = rawTz || getSavedTimeZone();
    if (($("tz").value || "").trim() !== tz) $("tz").value = tz;
    persistTimeZone(tz);
    const host = $("tips-today");
    host.innerHTML = '<p class="empty">Cargando…</p>';
    try {
      clearFlash();
      const q = new URLSearchParams({ per_topic: "1" });
      if (rawTz) q.set("tz", rawTz);
      const data = await api("/me/tips/today?" + q.toString(), { method: "GET" });
      host.innerHTML = "";
      const head = document.createElement("p");
      head.className = "hint";
      head.textContent =
        "Fecha: " + String(data.date).slice(0, 10) + " · " + data.count + " tips";
      host.appendChild(head);
      if (!data.items || !data.items.length) {
        const p = document.createElement("p");
        p.className = "empty";
        p.textContent =
          "No hay tips para hoy. Asegúrate de estar suscrito y de que haya tips en la base (seed o ingest).";
        host.appendChild(p);
        await loadHistory();
        return;
      }
      for (const tip of data.items) {
        const card = document.createElement("article");
        card.className = "tip-card";
        const h = document.createElement("h3");
        h.textContent = tip.title;
        const body = document.createElement("p");
        body.textContent = tip.body;
        card.appendChild(h);
        card.appendChild(body);
        if (tip.source_url) {
          const a = document.createElement("a");
          a.href = tip.source_url;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          a.textContent = "Fuente";
          card.appendChild(a);
        }
        host.appendChild(card);
      }
      await loadHistory();
    } catch (e) {
      host.innerHTML = "";
      showFlash(e.message, "error");
    }
  }

  $("tab-register").addEventListener("click", () => {
    clearFlash();
    setAuthTab(true);
  });

  $("tab-login").addEventListener("click", () => {
    clearFlash();
    setAuthTab(false);
  });

  $("form-register").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const email = $("reg-email").value.trim();
    const password = $("reg-password").value;
    const confirm = $("reg-password-confirm").value;

    if (!email) {
      showFlash("Indica un email válido.", "error");
      return;
    }
    if (password.length < 6) {
      showFlash("La contraseña debe tener al menos 6 caracteres.", "error");
      return;
    }
    if (password !== confirm) {
      showFlash("Las contraseñas no coinciden.", "error");
      return;
    }

    const submitBtn = $("btn-register-submit");
    submitBtn.disabled = true;
    try {
      clearFlash();
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const tok = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(tok.access_token);
      updateAuthUi();
      await refreshMe();
      await loadTopicsAndSubs();
      historyPage = 1;
      await loadTodayTips();
      $("form-register").reset();
      showFlash("Cuenta creada. Ya estás dentro.", "ok");
    } catch (e) {
      showFlash(e.message, "error");
    } finally {
      submitBtn.disabled = false;
    }
  });

  $("form-login").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const email = $("login-email").value.trim();
    const password = $("login-password").value;
    if (!email || !password) {
      showFlash("Email y contraseña obligatorios.", "error");
      return;
    }
    const submitBtn = $("btn-login-submit");
    submitBtn.disabled = true;
    try {
      clearFlash();
      const tok = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(tok.access_token);
      updateAuthUi();
      await refreshMe();
      await loadTopicsAndSubs();
      historyPage = 1;
      await loadTodayTips();
      showFlash("Sesión iniciada.", "ok");
    } catch (e) {
      showFlash(e.message, "error");
    } finally {
      submitBtn.disabled = false;
    }
  });

  $("btn-logout").addEventListener("click", () => {
    setToken(null);
    updateAuthUi();
    setAuthTab(true);
    clearFlash();
    $("tips-today").innerHTML = "";
    $("tips-history").innerHTML = "";
    $("history-pagination").hidden = true;
    historyPage = 1;
    historyLastTotal = 0;
  });

  $("btn-admin-reload").addEventListener("click", () => loadAdminTips());
  $("admin-tip-status").addEventListener("change", () => loadAdminTips());

  $("btn-today").addEventListener("click", () => loadTodayTips());

  $("btn-save-prefs").addEventListener("click", async () => {
    if (!getToken()) return;
    const locale = ($("pref-locale").value || "es").trim();
    const tzRaw = ($("tz").value || "").trim();
    const submit = $("btn-save-prefs");
    submit.disabled = true;
    try {
      clearFlash();
      const body = { locale };
      body.iana_timezone = tzRaw || null;
      const updated = await api("/me/preferences", {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      userLocale = updated.locale || "es";
      if (updated.iana_timezone) {
        $("tz").value = updated.iana_timezone;
        persistTimeZone(updated.iana_timezone);
      } else {
        persistTimeZone($("tz").value);
      }
      showFlash("Preferencias guardadas.", "ok");
    } catch (e) {
      showFlash(e.message, "error");
    } finally {
      submit.disabled = false;
    }
  });

  $("tz").addEventListener("change", () => {
    persistTimeZone($("tz").value);
  });
  $("tz").addEventListener("blur", () => {
    const v = ($("tz").value || "").trim();
    if (!v) {
      $("tz").value = detectBrowserTimeZone();
    }
    persistTimeZone($("tz").value);
  });

  $("btn-history-refresh").addEventListener("click", () => {
    historyPage = 1;
    loadHistory();
  });

  $("history-size").addEventListener("change", () => {
    historyPage = 1;
    loadHistory();
  });

  $("history-topic-select").addEventListener("change", () => {
    historyPage = 1;
    loadHistory();
  });

  $("btn-history-prev").addEventListener("click", () => {
    if (historyPage > 1) {
      historyPage -= 1;
      loadHistory();
    }
  });

  $("btn-history-next").addEventListener("click", () => {
    const totalPages = Math.ceil(historyLastTotal / historyLastSize) || 1;
    if (historyPage < totalPages) {
      historyPage += 1;
      loadHistory();
    }
  });

  initTimeZoneField();
  setAuthTab(true);
  updateAuthUi();
  if (getToken()) {
    refreshMe().then(() => {
      historyPage = 1;
      return loadTopicsAndSubs()
        .then(() => loadTodayTips())
        .catch((e) => showFlash(e.message, "error"));
    });
  }
})();
