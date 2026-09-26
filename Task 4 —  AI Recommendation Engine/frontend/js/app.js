/**
 * CineMatch AI - Frontend Controller & Application Logic
 */

const state = {
  activeUserId: "user-1",
  activeUser: null,
  users: [],
  activeModel: "hybrid",
  alpha: 0.6,
  activeTab: "browse",
  currentItem: null,
  curatedData: null,
  searchQuery: ""
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await checkApiHealth();
  await loadUsers();
  await loadContent();
});

// Setup DOM Event Listeners
function setupEventListeners() {
  // Tab Navigation
  document.querySelectorAll(".nav-tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      switchTab(tab);
    });
  });

  // User Persona Switcher
  const userSelect = document.getElementById("user-select-dropdown");
  if (userSelect) {
    userSelect.addEventListener("change", (e) => {
      switchUser(e.target.value);
    });
  }

  // Model Toggle Buttons
  document.querySelectorAll(".model-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const model = btn.dataset.model;
      setModel(model);
    });
  });

  // Alpha Weight Slider
  const slider = document.getElementById("alpha-slider");
  if (slider) {
    slider.addEventListener("input", (e) => {
      const val = parseFloat(e.target.value);
      state.alpha = val;
      const badge = document.getElementById("slider-val-badge");
      if (badge) {
        badge.textContent = `${Math.round(val * 100)}% Content / ${Math.round((1 - val) * 100)}% CF`;
      }
    });
    slider.addEventListener("change", () => {
      loadContent();
    });
  }

  // Modal Close
  const closeBtn = document.getElementById("modal-close-btn");
  const overlay = document.getElementById("item-modal-overlay");
  if (closeBtn && overlay) {
    closeBtn.addEventListener("click", closeModal);
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) closeModal();
    });
  }

  // Search Input
  const searchInput = document.getElementById("search-input");
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener("input", (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        state.searchQuery = e.target.value.trim();
        handleSearch();
      }, 300);
    });
  }
}

// Check Backend API Connection & Security Status
async function checkApiHealth() {
  const statusPill = document.getElementById("api-status-indicator");
  try {
    const health = await window.api.checkHealth();
    if (statusPill) {
      statusPill.innerHTML = `<span class="status-dot"></span> API Online (ML Engine Ready)`;
      statusPill.style.color = "var(--accent-green)";
    }
  } catch (err) {
    if (statusPill) {
      statusPill.innerHTML = `<span class="status-dot" style="background:#ef4444;box-shadow:0 0 8px #ef4444;"></span> Backend Offline`;
      statusPill.style.color = "#ef4444";
    }
    console.warn("API health check failed. Ensure backend server is running on http://127.0.0.1:5000");
  }
}

// Load User Personas
async function loadUsers() {
  try {
    const res = await window.api.getUsers();
    state.users = res.users;
    
    const select = document.getElementById("user-select-dropdown");
    if (select) {
      select.innerHTML = state.users.map(u => `
        <option value="${u.id}" ${u.id === state.activeUserId ? "selected" : ""}>
          ${u.name} (${u.ratings_count} ratings)
        </option>
      `).join("");
    }

    updateActiveUserHeader();
  } catch (err) {
    console.error("Failed to load users:", err);
  }
}

function updateActiveUserHeader() {
  const user = state.users.find(u => u.id === state.activeUserId);
  if (user) {
    state.activeUser = user;
    const avatar = document.getElementById("header-user-avatar");
    const nameEl = document.getElementById("header-user-name");
    const roleEl = document.getElementById("header-user-role");

    if (avatar) avatar.src = user.avatar;
    if (nameEl) nameEl.textContent = user.name;
    if (roleEl) roleEl.textContent = user.preferred_genres.length ? user.preferred_genres.slice(0, 2).join(", ") : "New Member";
  }
}

// Switch Active User
async function switchUser(userId) {
  state.activeUserId = userId;
  updateActiveUserHeader();
  await loadContent();
  if (state.activeTab === "profile") {
    loadProfileView();
  } else if (state.activeTab === "history") {
    loadHistoryView();
  } else if (state.activeTab === "control") {
    loadControlView();
  }
}

// Switch Algorithm Model
function setModel(modelType) {
  state.activeModel = modelType;
  document.querySelectorAll(".model-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.model === modelType);
  });

  const sliderGroup = document.getElementById("alpha-slider-group");
  if (sliderGroup) {
    sliderGroup.style.display = modelType === "hybrid" ? "flex" : "none";
  }

  loadContent();
}

// Tab Switching
function switchTab(tabName) {
  state.activeTab = tabName;
  document.querySelectorAll(".nav-tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });

  document.querySelectorAll(".tab-view").forEach(view => {
    view.style.display = view.id === `tab-${tabName}` ? "block" : "none";
  });

  if (tabName === "browse") {
    loadContent();
  } else if (tabName === "profile") {
    loadProfileView();
  } else if (tabName === "control") {
    loadControlView();
  } else if (tabName === "history") {
    loadHistoryView();
  }
}

// Main Content Loader (Hero + Rails)
async function loadContent() {
  const loadingIndicator = document.getElementById("global-loading");
  if (loadingIndicator) loadingIndicator.style.display = "block";

  try {
    // 1. Fetch recommendations based on active model and alpha
    const recsRes = await window.api.getRecommendations(
      state.activeUserId,
      state.activeModel,
      state.alpha,
      12
    );

    // 2. Fetch curated rails (Top Picks, Because You Loved, Trending)
    const railsRes = await window.api.getCuratedRails(state.activeUserId);
    state.curatedData = railsRes.rails;

    // Check Cold Start banner
    const coldBanner = document.getElementById("cold-start-banner");
    if (coldBanner) {
      if (recsRes.is_cold_start) {
        coldBanner.style.display = "flex";
        coldBanner.innerHTML = `
          <span>⚠️ <strong>Cold-Start Active:</strong> This profile has fewer than 3 ratings. The hybrid model has automatically adapted by prioritizing high-affinity content metadata and popular consensus.</span>
          <button class="btn btn-secondary" style="padding:0.3rem 0.8rem; font-size:0.75rem;" onclick="openItemModal('item-1')">Rate a Title Now</button>
        `;
      } else {
        coldBanner.style.display = "none";
      }
    }

    // Render Hero Spotlight (Use 1st Top Pick or Trending Item)
    const heroItem = recsRes.recommendations.length > 0 ? recsRes.recommendations[0].item : state.curatedData.trending.items[0].item;
    renderHero(heroItem, recsRes.recommendations[0]?.match_percentage || 98);

    // Render Recommendation Rails
    renderRails(recsRes.recommendations, state.curatedData);

  } catch (err) {
    console.error("Failed to load recommendations:", err);
  } finally {
    if (loadingIndicator) loadingIndicator.style.display = "none";
  }
}

// Render Hero Spotlight
function renderHero(item, matchPct) {
  const hero = document.getElementById("hero-spotlight");
  if (!hero || !item) return;

  hero.style.background = item.gradient || "linear-gradient(135deg, #0d1b2a, #1b263b, #415a77)";
  
  const titleEl = document.getElementById("hero-title");
  const synEl = document.getElementById("hero-synopsis");
  const matchEl = document.getElementById("hero-match");
  const metaEl = document.getElementById("hero-meta");
  const actionBtn = document.getElementById("hero-play-btn");
  const infoBtn = document.getElementById("hero-info-btn");

  if (titleEl) titleEl.textContent = item.title;
  if (synEl) synEl.textContent = item.overview;
  if (matchEl) matchEl.textContent = `${matchPct}% Match For You`;
  if (metaEl) {
    metaEl.innerHTML = `
      <span>⭐ ${item.rating}/10</span>
      <span>•</span>
      <span>${item.year}</span>
      <span>•</span>
      <span>${item.duration}</span>
      <span>•</span>
      <span>${item.genres.join(", ")}</span>
    `;
  }

  if (actionBtn) {
    actionBtn.onclick = () => {
      window.api.logInteraction(state.activeUserId, item.id, "watched");
      alert(`🎬 Now Streaming: "${item.title}". Logged interaction to your recommendation history!`);
      loadContent();
    };
  }

  if (infoBtn) {
    infoBtn.onclick = () => openItemModal(item.id);
  }
}

// Render Recommendation Rails
function renderRails(topRecs, curated) {
  // Rail 1: Top Picks (or Active Model suggestions)
  const topPicksGrid = document.getElementById("rail-top-picks-grid");
  const topPicksTitle = document.getElementById("top-picks-title");
  const topPicksBadge = document.getElementById("top-picks-badge");

  if (topPicksTitle) {
    const modelLabels = {
      hybrid: "Top Picks For You (Hybrid Model)",
      content: "Personalized Suggestions (Content-Based)",
      collaborative: "Viewer Taste Matches (Collaborative SVD)"
    };
    topPicksTitle.textContent = modelLabels[state.activeModel] || "Top Picks";
  }

  if (topPicksBadge) {
    topPicksBadge.textContent = state.activeModel.toUpperCase();
  }

  if (topPicksGrid) {
    topPicksGrid.innerHTML = topRecs.map(r => createCardHTML(r.item, r.match_percentage, r.reasons[0])).join("");
  }

  // Rail 2: Because You Loved (Similar Items)
  const becauseLovedGrid = document.getElementById("rail-similar-grid");
  const becauseLovedHeader = document.getElementById("rail-similar-header");
  if (curated && curated.because_you_watched) {
    const byw = curated.because_you_watched;
    if (becauseLovedHeader) {
      becauseLovedHeader.textContent = byw.title;
    }
    if (becauseLovedGrid) {
      if (byw.items.length > 0) {
        becauseLovedGrid.innerHTML = byw.items.map(s => createCardHTML(s.item, s.match_percentage, s.reasons[0])).join("");
      } else {
        becauseLovedGrid.innerHTML = `<p style="color:var(--text-muted); grid-column:1/-1;">Rate more movies to unlock tailored 'Because You Loved' recommendations!</p>`;
      }
    }
  }

  // Rail 3: Trending & Critically Acclaimed
  const trendingGrid = document.getElementById("rail-trending-grid");
  if (curated && curated.trending && trendingGrid) {
    trendingGrid.innerHTML = curated.trending.items.map(t => createCardHTML(t.item, t.match_percentage, t.reasons[0])).join("");
  }

  // Attach card click handlers
  document.querySelectorAll(".movie-card").forEach(card => {
    card.addEventListener("click", () => {
      const itemId = card.dataset.itemId;
      openItemModal(itemId);
    });
  });
}

// Generate Movie Card HTML
function createCardHTML(item, matchPercentage, reasonText) {
  const genresChips = (item.genres || []).slice(0, 2).map(g => `<span class="genre-chip">${g}</span>`).join("");
  const safeReason = reasonText || "High recommendation confidence";

  return `
    <div class="movie-card" data-item-id="${item.id}" id="card-${item.id}">
      <div class="card-poster" style="background: ${item.gradient || '#1e293b'};">
        <span class="card-type-tag">${item.type}</span>
        <span class="card-match-pill">${matchPercentage}% Match</span>
      </div>
      <div class="card-content">
        <div>
          <h3 class="card-title">${item.title}</h3>
          <div class="card-meta">
            <span>⭐ ${item.rating}</span>
            <span>•</span>
            <span>${item.year}</span>
            <span>•</span>
            <span>${item.duration}</span>
          </div>
          <div class="card-genres">
            ${genresChips}
          </div>
        </div>
        <div class="card-reason">
          💡 ${safeReason}
        </div>
      </div>
    </div>
  `;
}

// Search Filter Handler
async function handleSearch() {
  if (!state.searchQuery) {
    loadContent();
    return;
  }

  try {
    const res = await window.api.getItems({ search: state.searchQuery });
    const topPicksGrid = document.getElementById("rail-top-picks-grid");
    const topPicksTitle = document.getElementById("top-picks-title");

    if (topPicksTitle) topPicksTitle.textContent = `Search Results for "${state.searchQuery}" (${res.total})`;
    if (topPicksGrid) {
      if (res.items.length > 0) {
        topPicksGrid.innerHTML = res.items.map(i => createCardHTML(i, Math.round(i.popularity), `Director: ${i.director}`)).join("");
        document.querySelectorAll(".movie-card").forEach(card => {
          card.addEventListener("click", () => openItemModal(card.dataset.itemId));
        });
      } else {
        topPicksGrid.innerHTML = `<p style="color:var(--text-muted); grid-column:1/-1; padding:2rem 0;">No matching movies or series found for "${state.searchQuery}".</p>`;
      }
    }
  } catch (err) {
    console.error("Search failed:", err);
  }
}

// Open Item Details & Similar Items Modal
async function openItemModal(itemId) {
  try {
    const res = await window.api.getItem(itemId);
    const item = res.item;
    state.currentItem = item;

    const overlay = document.getElementById("item-modal-overlay");
    const hero = document.getElementById("modal-hero-bg");
    const title = document.getElementById("modal-item-title");
    const meta = document.getElementById("modal-item-meta");
    const syn = document.getElementById("modal-item-synopsis");
    const director = document.getElementById("modal-item-director");
    const cast = document.getElementById("modal-item-cast");
    const tags = document.getElementById("modal-item-tags");

    if (hero) hero.style.background = item.gradient || "#1e293b";
    if (title) title.textContent = item.title;
    if (meta) {
      meta.innerHTML = `
        <span class="card-match-pill" style="position:static;">${item.rating} ★ IMDb</span>
        <span>${item.year}</span>
        <span>${item.duration}</span>
        <span>${item.type}</span>
      `;
    }
    if (syn) syn.textContent = item.overview;
    if (director) director.textContent = item.director;
    if (cast) cast.textContent = item.cast.join(", ");
    if (tags) {
      tags.innerHTML = item.tags.map(t => `<span class="genre-chip" style="background:rgba(0,242,254,0.1); color:var(--accent-cyan); border-color:rgba(0,242,254,0.2);">#${t}</span>`).join(" ");
    }

    // Set up interactive Star Rating Widget
    setupRatingWidget(itemId);

    // Set up Watchlist Toggle
    setupWatchlistButton(itemId);

    // Fetch and render Similar Items ("More Like This")
    loadSimilarItems(itemId);

    if (overlay) overlay.classList.add("open");

    // Log modal view interaction
    window.api.logInteraction(state.activeUserId, itemId, "viewed_details");

  } catch (err) {
    console.error("Failed to open item modal:", err);
  }
}

function closeModal() {
  const overlay = document.getElementById("item-modal-overlay");
  if (overlay) overlay.classList.remove("open");
}

// Interactive Star Rating Widget
function setupRatingWidget(itemId) {
  const starsContainer = document.getElementById("modal-rating-stars");
  const scoreBadge = document.getElementById("modal-rating-score");
  if (!starsContainer) return;

  const currentRating = (state.activeUser?.ratings && state.activeUser.ratings[itemId]) || 0;
  if (scoreBadge) {
    scoreBadge.textContent = currentRating > 0 ? `Your Rating: ${currentRating} ★` : "Tap to rate";
  }

  starsContainer.innerHTML = [1, 2, 3, 4, 5].map(starNum => `
    <button class="star-btn ${starNum <= currentRating ? 'active' : ''}" data-star="${starNum}">★</button>
  `).join("");

  starsContainer.querySelectorAll(".star-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const selectedRating = parseFloat(btn.dataset.star);
      try {
        await window.api.rateItem(state.activeUserId, itemId, selectedRating);
        
        // Update local user state
        if (!state.activeUser.ratings) state.activeUser.ratings = {};
        state.activeUser.ratings[itemId] = selectedRating;
        
        // Visual feedback
        if (scoreBadge) scoreBadge.textContent = `Saved: ${selectedRating} ★! Recalculating models...`;
        starsContainer.querySelectorAll(".star-btn").forEach(s => {
          s.classList.toggle("active", parseFloat(s.dataset.star) <= selectedRating);
        });

        // Re-load recommendations in background to reflect updated taste
        await loadUsers();
        await loadContent();
      } catch (err) {
        alert("Failed to submit rating: " + err.message);
      }
    });
  });
}

// Watchlist Button
function setupWatchlistButton(itemId) {
  const btn = document.getElementById("modal-watchlist-btn");
  if (!btn) return;

  const inWatchlist = (state.activeUser?.watchlist || []).includes(itemId);
  btn.innerHTML = inWatchlist ? "✓ In Your Watchlist" : "+ Add to Watchlist";
  btn.className = inWatchlist ? "btn btn-cyan" : "btn btn-secondary";

  btn.onclick = async () => {
    try {
      const res = await window.api.toggleWatchlist(state.activeUserId, itemId);
      const isNowIn = res.in_watchlist;
      btn.innerHTML = isNowIn ? "✓ In Your Watchlist" : "+ Add to Watchlist";
      btn.className = isNowIn ? "btn btn-cyan" : "btn btn-secondary";
      await loadUsers();
    } catch (err) {
      alert("Failed to update watchlist: " + err.message);
    }
  };
}

// Load Similar Items ("More Like This")
async function loadSimilarItems(itemId) {
  const container = document.getElementById("modal-similar-grid");
  if (!container) return;

  container.innerHTML = `<p style="color:var(--text-muted);">Detecting similar items with Content Cosine Vectorizer...</p>`;

  try {
    const res = await window.api.getSimilarItems(itemId, 4);
    if (res.similar_items.length > 0) {
      container.innerHTML = res.similar_items.map(s => `
        <div class="movie-card" onclick="openItemModal('${s.item.id}')" style="cursor:pointer;">
          <div class="card-poster" style="aspect-ratio:16/9; background:${s.item.gradient || '#1e293b'};">
            <span class="card-match-pill">${s.match_percentage}% Similar</span>
          </div>
          <div style="padding:0.75rem;">
            <h4 style="font-size:0.9rem; font-weight:700;">${s.item.title}</h4>
            <div style="font-size:0.7rem; color:var(--accent-cyan); margin-top:0.25rem;">
              ${s.reasons[0] || 'Content feature match'}
            </div>
          </div>
        </div>
      `).join("");
    } else {
      container.innerHTML = `<p style="color:var(--text-muted);">No similar items found.</p>`;
    }
  } catch (err) {
    container.innerHTML = `<p style="color:var(--text-muted);">Could not load similar items.</p>`;
  }
}

// Render User Profile Analysis View
async function loadProfileView() {
  const container = document.getElementById("tab-profile-content");
  if (!container) return;

  container.innerHTML = `<p style="color:var(--text-muted);">Analyzing user profile taste distribution...</p>`;

  try {
    const res = await window.api.getUserProfile(state.activeUserId);
    const p = res.profile_analysis;

    const affinityBarsHTML = p.genre_affinity.map(g => `
      <div class="affinity-bar-item">
        <div class="affinity-bar-label">
          <span><strong>${g.genre}</strong> (${g.count} titles rated)</span>
          <span style="color:var(--accent-cyan); font-weight:700;">${g.affinity_percentage}%</span>
        </div>
        <div class="affinity-bar-track">
          <div class="affinity-bar-fill" style="width: ${g.affinity_percentage}%;"></div>
        </div>
      </div>
    `).join("");

    const recentActivityHTML = p.recent_activity.length > 0
      ? p.recent_activity.map(act => `
          <div style="display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid rgba(255,255,255,0.05); font-size:0.85rem;">
            <span>${act.item_title || act.item_id}</span>
            <span style="color:var(--accent-gold);">${act.action === 'rated' ? `${act.score} ★` : act.action}</span>
          </div>
        `).join("")
      : `<p style="color:var(--text-muted); font-size:0.85rem;">No recent activity recorded yet.</p>`;

    container.innerHTML = `
      <div class="profile-dashboard">
        <!-- Left Column: User Summary & Core Metrics -->
        <div class="profile-card">
          <img src="${p.avatar}" alt="${p.name}" class="profile-avatar-lg">
          <h2 style="font-size:1.5rem; margin-bottom:0.25rem;">${p.name}</h2>
          <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:1.25rem;">${p.bio}</p>

          <div class="stat-metric-row">
            <div class="metric-box">
              <div class="metric-num">${p.total_ratings}</div>
              <div class="metric-title">Total Rated</div>
            </div>
            <div class="metric-box">
              <div class="metric-num">${p.average_rating} ★</div>
              <div class="metric-title">Average Rating</div>
            </div>
            <div class="metric-box">
              <div class="metric-num">${p.diversity_score}%</div>
              <div class="metric-title">Taste Diversity (${p.diversity_label})</div>
            </div>
            <div class="metric-box">
              <div class="metric-num">${p.novelty_score}%</div>
              <div class="metric-title">Novelty Index</div>
            </div>
          </div>

          <div style="margin-top:1.5rem; text-align:left;">
            <div style="font-size:0.75rem; text-transform:uppercase; color:var(--text-muted); font-weight:700; margin-bottom:0.5rem;">Favorite Themes</div>
            <div style="display:flex; flex-wrap:wrap; gap:0.4rem;">
              ${p.favorite_tags.map(t => `<span class="genre-chip" style="background:rgba(157,78,221,0.15); color:var(--accent-purple);">#${t}</span>`).join("")}
            </div>
          </div>
        </div>

        <!-- Right Column: Deep Genre Affinity & Activity -->
        <div class="profile-card" style="text-align:left;">
          <h3 style="font-size:1.25rem; margin-bottom:1.25rem;">📊 Genre Affinity Radar (Calculated Weights)</h3>
          <div style="margin-bottom:2rem;">
            ${affinityBarsHTML || '<p style="color:var(--text-muted);">No ratings yet to calculate genre affinity.</p>'}
          </div>

          <h3 style="font-size:1.25rem; margin-bottom:1rem;">🕒 Recent Interactions</h3>
          <div>
            ${recentActivityHTML}
          </div>
        </div>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<p style="color:#ef4444;">Failed to load user profile: ${err.message}</p>`;
  }
}

// Render Engine Control Room (Weights & Algorithm Comparison Lab)
async function loadControlView() {
  const container = document.getElementById("tab-control-content");
  if (!container) return;

  container.innerHTML = `<p style="color:var(--text-muted);">Running ML algorithm comparison for ${state.activeUser?.name}...</p>`;

  try {
    const res = await window.api.getModelComparison(state.activeUserId);
    const m = res.metrics;

    const renderColumnItems = (items) => items.map(i => `
      <div style="background:rgba(255,255,255,0.03); padding:0.75rem; border-radius:var(--radius-sm); margin-bottom:0.75rem; border:1px solid var(--border-glass);">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong style="font-size:0.9rem;">${i.item.title}</strong>
          <span class="card-match-pill" style="position:static;">${i.match_percentage}%</span>
        </div>
        <div style="font-size:0.725rem; color:var(--text-muted); margin-top:0.25rem;">
          ${i.reasons[0] || 'High affinity'}
        </div>
      </div>
    `).join("");

    container.innerHTML = `
      <div style="margin-bottom:2rem;">
        <h2 style="font-size:1.8rem; margin-bottom:0.5rem;">🔬 Machine Learning Model Laboratory</h2>
        <p style="color:var(--text-muted); max-width:800px;">
          Compare how Pure Content-Based Filtering, Pure Collaborative Filtering (Matrix Factorization SVD), and the Hybrid Model prioritize items differently for <strong>${state.activeUser?.name}</strong>.
        </p>

        <div style="display:flex; gap:1rem; margin-top:1.25rem; flex-wrap:wrap;">
          <div class="metric-box" style="padding:0.75rem 1.25rem;">
            <div class="metric-num" style="font-size:1.3rem;">${m.content_vs_cf_overlap} / 5</div>
            <div class="metric-title">Model Overlap Count</div>
          </div>
          <div class="metric-box" style="padding:0.75rem 1.25rem;">
            <div class="metric-num" style="font-size:1.3rem;">${Math.round(m.jaccard_similarity * 100)}%</div>
            <div class="metric-title">Jaccard Taste Agreement</div>
          </div>
          <div class="metric-box" style="padding:0.75rem 1.25rem;">
            <div class="metric-num" style="font-size:1.3rem; color:${m.cold_start_active ? 'var(--accent-gold)' : 'var(--accent-green)'}">
              ${m.cold_start_active ? 'Cold Start Active' : 'Warm Matrix Fit'}
            </div>
            <div class="metric-title">Cold Start State</div>
          </div>
        </div>
      </div>

      <div class="comparison-grid">
        <!-- Content-Based Column -->
        <div class="comparison-column">
          <div class="comparison-col-header">
            <span class="brand-badge" style="background:rgba(0,242,254,0.15); color:var(--accent-cyan);">Content-Based</span>
            <h3 style="font-size:1.2rem; margin-top:0.4rem;">TF-IDF + Cosine</h3>
            <p style="font-size:0.75rem; color:var(--text-muted);">Recommends items with matching genres, directors, and plot keywords.</p>
          </div>
          ${renderColumnItems(res.content_based.items)}
        </div>

        <!-- Collaborative Filtering Column -->
        <div class="comparison-column">
          <div class="comparison-col-header">
            <span class="brand-badge" style="background:rgba(157,78,221,0.15); color:var(--accent-purple);">Collaborative SVD</span>
            <h3 style="font-size:1.2rem; margin-top:0.4rem;">Latent Factor Matrix</h3>
            <p style="font-size:0.75rem; color:var(--text-muted);">Discovers latent viewer taste clusters across the user-item rating matrix.</p>
          </div>
          ${renderColumnItems(res.collaborative.items)}
        </div>

        <!-- Hybrid Model Column -->
        <div class="comparison-column" style="border-color:rgba(229,9,20,0.4); box-shadow:0 0 20px rgba(229,9,20,0.1);">
          <div class="comparison-col-header">
            <span class="brand-badge" style="background:rgba(229,9,20,0.2); color:var(--accent-red);">Hybrid Model</span>
            <h3 style="font-size:1.2rem; margin-top:0.4rem;">α-Weighted Ensemble</h3>
            <p style="font-size:0.75rem; color:var(--text-muted);">Optimal balance preventing cold start while uncovering serendipitous hits.</p>
          </div>
          ${renderColumnItems(res.hybrid.items)}
        </div>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<p style="color:#ef4444;">Failed to load model comparison: ${err.message}</p>`;
  }
}

// Render Recommendation History & Audit View
async function loadHistoryView() {
  const container = document.getElementById("tab-history-content");
  if (!container) return;

  container.innerHTML = `<p style="color:var(--text-muted);">Loading recommendation audit trail...</p>`;

  try {
    const res = await window.api.getHistory(state.activeUserId, 40);
    const history = res.history;

    if (history.length === 0) {
      container.innerHTML = `<p style="color:var(--text-muted);">No recommendation events logged for this user yet.</p>`;
      return;
    }

    const rowsHTML = history.map(h => {
      const timeStr = new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const statusBadge = h.status === 'served' 
        ? `<span class="genre-chip" style="color:var(--text-muted);">Served</span>`
        : `<span class="card-match-pill" style="position:static; font-size:0.65rem;">${h.status}</span>`;

      return `
        <tr>
          <td><strong style="color:#fff;">${h.item_title}</strong></td>
          <td><span class="genre-chip" style="background:rgba(255,255,255,0.06);">${h.model_type}</span></td>
          <td>${statusBadge}</td>
          <td style="font-size:0.75rem; color:var(--accent-cyan);">${h.reasons[0] || 'N/A'}</td>
          <td style="font-size:0.75rem; color:var(--text-muted);">${timeStr}</td>
        </tr>
      `;
    }).join("");

    container.innerHTML = `
      <div style="margin-bottom:1.5rem;">
        <h2 style="font-size:1.8rem; margin-bottom:0.5rem;">📜 Recommendation Audit History</h2>
        <p style="color:var(--text-muted);">
          Every recommendation generated by the engine is tracked along with timestamp, model used, score, and recorded user feedback.
        </p>
      </div>

      <div style="background:var(--bg-card); border-radius:var(--radius-lg); border:1px solid var(--border-glass); overflow:hidden;">
        <table class="history-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Recommendation Model</th>
              <th>Interaction Status</th>
              <th>Reason Attribution</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHTML}
          </tbody>
        </table>
      </div>
    `;

  } catch (err) {
    container.innerHTML = `<p style="color:#ef4444;">Failed to load history: ${err.message}</p>`;
  }
}
