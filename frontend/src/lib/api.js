import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const api = axios.create({ baseURL: API });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("swarna_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  const companyId = localStorage.getItem("swarna_company_id");
  if (companyId) {
    config.params = { ...(config.params || {}), company_id: companyId };
  }
  return config;
});

export function apiError(e, fallback = "Terjadi kesalahan. Coba lagi.") {
  const detail = e?.response?.data?.detail;
  if (!detail) return e?.message || fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d?.msg || JSON.stringify(d)).join(" ");
  return String(detail);
}

export { API };
export default api;
