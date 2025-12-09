// Simpelt JS: små AJAX-kald for at undgå reload (som i x(1)-stilen)

// Hjælpere
async function fetchJson(url, options = {}) {
  const res = await fetch(url, options);
  let data = {};
  try {
    data = await res.json();
  } catch (_) {
    throw new Error("Server error");
  }
  if (!res.ok || data.status === "error") {
    throw new Error(data.message || "Error");
  }
  return data;
}

// Formularer med .js-ajax
function bindAjaxForms() {
  document.querySelectorAll("form.js-ajax").forEach((form) => {
    if (form.dataset.bound) return;
    form.dataset.bound = "1";
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const data = await fetchJson(form.action, { method: form.method || "POST", body: fd });
        if (data.redirect) {
          window.location = data.redirect;
          return;
        }
        if (form.dataset.target && data.html) {
          const target = document.querySelector(form.dataset.target);
          if (target) {
            if (form.dataset.mode === "prepend") {
              target.insertAdjacentHTML("afterbegin", data.html);
            } else {
              target.insertAdjacentHTML("beforeend", data.html);
            }
            bindAjaxForms(); // nye forms i HTML
          }
        }
        form.reset();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

// Like
function bindLikeButtons() {
  document.body.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-like");
    if (!btn) return;
    e.preventDefault();
    const postId = btn.dataset.post;
    try {
      const data = await fetchJson(`/api/posts/${postId}/like`, { method: "POST" });
      const count = btn.querySelector(".like-count");
      if (count) count.textContent = data.likes;
      const icon = btn.querySelector("i");
      if (icon) icon.className = data.liked ? "fa-solid fa-heart" : "fa-regular fa-heart";
    } catch (err) {
      alert(err.message);
    }
  });
}

// Delete (post/comment)
function bindDeleteButtons() {
  document.body.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-delete");
    if (!btn) return;
    e.preventDefault();
    if (!confirm("Delete?")) return;
    const url = btn.dataset.url;
    try {
      await fetchJson(url, { method: "DELETE" });
      const card = btn.closest("[data-post], [data-comment]");
      if (card) card.remove();
    } catch (err) {
      alert(err.message);
    }
  });
}

// Follow
function bindFollowButtons() {
  document.body.addEventListener("click", async (e) => {
    const btn = e.target.closest(".js-follow");
    if (!btn) return;
    e.preventDefault();
    const userId = btn.dataset.user;
    try {
      const data = await fetchJson(`/api/follow/${userId}`, { method: "POST" });
      btn.textContent = data.following ? btn.dataset.unfollow : btn.dataset.follow;
    } catch (err) {
      alert(err.message);
    }
  });
}

// Kommentar-formularer (append ny comment)
function bindCommentForms() {
  document.querySelectorAll("form.comment-form").forEach((form) => {
    if (form.dataset.bound) return;
    form.dataset.bound = "1";
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const data = await fetchJson(form.action, { method: "POST", body: fd });
        const target = document.querySelector(form.dataset.target);
        if (target && data.html) {
          target.insertAdjacentHTML("beforeend", data.html);
          bindAjaxForms();
        }
        form.reset();
      } catch (err) {
        alert(err.message);
      }
    });
  });
}

// Search (submit only)
function bindSearch() {
  const form = document.querySelector(".js-search");
  if (!form || form.dataset.bound) return;
  form.dataset.bound = "1";
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    try {
      const data = await fetchJson(form.action, { method: "POST", body: fd });
      const results = document.querySelector("#search_results");
      if (!results) return;
      const users = data.users
        .map((u) => `<div class="search-row"><strong>${u.user_first_name}</strong> @${u.user_username}</div>`)
        .join("");
      const posts = data.posts
        .map((p) => `<div class="search-row">${p.post_message} <span class="muted">@${p.user_username}</span></div>`)
        .join("");
      results.innerHTML = users + posts;
    } catch (err) {
      alert(err.message);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindAjaxForms();
  bindCommentForms();
  bindLikeButtons();
  bindDeleteButtons();
  bindFollowButtons();
  bindSearch();
});
