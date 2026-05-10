import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("em_token");
  if (token) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r.data,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem("em_token");
      window.location.href = "/login";
    }
    return Promise.reject(err?.response?.data || err);
  }
);

export const stats = {
  overview:           () => api.get("/stats/overview"),
  byGouvernerat:      () => api.get("/stats/by-gouvernerat"),
  byType:             () => api.get("/stats/by-type"),
  byContrat:          () => api.get("/stats/by-contrat"),
  priceDistribution:  () => api.get("/stats/price-distribution"),
  monthlyTrend:       () => api.get("/stats/monthly-trend"),
  amenities:          () => api.get("/stats/amenities"),
  priceHeatmap:       () => api.get("/stats/price-heatmap"),
  standingDist:       () => api.get("/stats/standing-distribution"),
  insights:           () => api.get("/stats/insights"),
  etrei:              () => api.get("/stats/etrei"),
};

export const listings = {
  list:    (p) => api.get("/listings", { params: p }),
  detail:  (id) => api.get(`/listings/${id}`),
  similar: (id) => api.get(`/listings/${id}/similar`),
  score:   (id) => api.get(`/listings/${id}/score`),
  villes:  (gov) => api.get("/listings/villes", { params: gov ? { gouvernerat: gov } : {} }),
  export:  (p) => `/api/listings/export?${new URLSearchParams(p).toString()}`,
};

export const map = {
  clusters:       (zoom) => api.get("/map/clusters", { params: { zoom } }),
  heatmap:        () => api.get("/map/heatmap"),
  points:         () => api.get("/map/points"),
  choropleth:     () => api.get("/map/choropleth"),
  gouvernerat:    (name) => api.get(`/map/gouvernerat/${encodeURIComponent(name)}`),
  timeMachine:    (year, month) => api.get("/map/time-machine", { params: { year, month } }),
};

export const pipeline = {
  status:  () => api.get("/pipeline/status"),
  trigger: () => api.post("/pipeline/trigger"),
  runs:    () => api.get("/pipeline/runs"),
  tasks:   (id) => api.get(`/pipeline/run/${id}/tasks`),
  quality: () => api.get("/pipeline/quality"),
};

export const auth = {
  logout: () => api.post("/auth/logout").finally(() => {
    localStorage.removeItem("em_token");
    window.location.href = "/login";
  }),
};

export default api;
