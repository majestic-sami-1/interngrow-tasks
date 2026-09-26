/**
 * CineMatch AI - REST API Client
 * Clean decoupled client layer communicating with the Flask Recommendation API.
 */
class CineMatchAPI {
  constructor() {
    this.baseUrl = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
      ? "http://127.0.0.1:5000"
      : "";
    // Default configured security key
    this.apiKey = "cine-rec-secret-key-2026-secure";
  }

  async _request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      "X-API-Key": this.apiKey,
      ...(options.headers || {})
    };

    try {
      const response = await fetch(url, { ...options, headers });
      
      if (response.status === 401) {
        throw new Error("Authentication Failed: Invalid or missing API key.");
      }
      if (response.status === 429) {
        const retry = response.headers.get("Retry-After") || "a few";
        throw new Error(`Rate limit exceeded! Please wait ${retry} seconds.`);
      }
      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.message || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  }

  // Health check
  async checkHealth() {
    return this._request("/api/health");
  }

  // Catalog items & search
  async getItems(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this._request(`/api/items${query ? `?${query}` : ""}`);
  }

  async getItem(itemId) {
    return this._request(`/api/items/${itemId}`);
  }

  // Similar Item Detection ("More Like This")
  async getSimilarItems(itemId, limit = 6) {
    return this._request(`/api/items/${itemId}/similar?limit=${limit}`);
  }

  // User Personas & Profile Analysis
  async getUsers() {
    return this._request("/api/users");
  }

  async getUser(userId) {
    return this._request(`/api/users/${userId}`);
  }

  async getUserProfile(userId) {
    return this._request(`/api/users/${userId}/profile`);
  }

  // User Actions: Rate & Watchlist
  async rateItem(userId, itemId, rating) {
    return this._request(`/api/users/${userId}/rate`, {
      method: "POST",
      body: JSON.stringify({ item_id: itemId, rating })
    });
  }

  async toggleWatchlist(userId, itemId) {
    return this._request(`/api/users/${userId}/watchlist`, {
      method: "POST",
      body: JSON.stringify({ item_id: itemId })
    });
  }

  // Recommendations
  async getRecommendations(userId, model = "hybrid", alpha = 0.6, limit = 12) {
    const params = new URLSearchParams({
      user_id: userId,
      model: model,
      alpha: alpha.toString(),
      limit: limit.toString()
    });
    return this._request(`/api/recommendations?${params.toString()}`);
  }

  async getCuratedRails(userId) {
    return this._request(`/api/recommendations/curated?user_id=${userId}`);
  }

  // Recommendation History & Interactions
  async getHistory(userId = null, limit = 30) {
    const query = userId ? `?user_id=${userId}&limit=${limit}` : `?limit=${limit}`;
    return this._request(`/api/history${query}`);
  }

  async logInteraction(userId, itemId, action) {
    return this._request("/api/history/interaction", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, item_id: itemId, action })
    });
  }

  // Model comparison
  async getModelComparison(userId) {
    return this._request(`/api/analytics/model-comparison?user_id=${userId}`);
  }
}

// Export singleton
window.api = new CineMatchAPI();
