import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=checking, false=guest
  const [companies, setCompanies] = useState([]);
  const [companyId, setCompanyId] = useState(localStorage.getItem("swarna_company_id") || "");
  const [companiesLoaded, setCompaniesLoaded] = useState(false);

  const loadCompanies = useCallback(async () => {
    try {
      const { data } = await api.get("/companies");
      setCompanies(data);
      if (data.length) {
        const current = localStorage.getItem("swarna_company_id");
        const valid = data.find((c) => c.id === current);
        const chosen = valid ? current : data[0].id;
        localStorage.setItem("swarna_company_id", chosen);
        setCompanyId(chosen);
      } else {
        localStorage.removeItem("swarna_company_id");
        setCompanyId("");
      }
    } catch {
      /* ignore */
    } finally {
      setCompaniesLoaded(true);
    }
  }, []);

  const bootstrap = useCallback(async () => {
    const token = localStorage.getItem("swarna_token");
    if (!token) { setUser(false); return; }
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      await loadCompanies();
    } catch {
      localStorage.removeItem("swarna_token");
      setUser(false);
    }
  }, [loadCompanies]);

  useEffect(() => { bootstrap(); }, [bootstrap]);

  const login = async (token, u) => {
    localStorage.setItem("swarna_token", token);
    setUser(u);
    await loadCompanies();
  };

  const logout = () => {
    localStorage.removeItem("swarna_token");
    localStorage.removeItem("swarna_company_id");
    setUser(false);
    setCompanies([]);
    setCompanyId("");
    setCompaniesLoaded(false);
  };

  const switchCompany = (id) => {
    localStorage.setItem("swarna_company_id", id);
    setCompanyId(id);
    window.location.reload();
  };

  return (
    <AuthContext.Provider value={{ user, setUser, companies, companyId, companiesLoaded, login, logout, switchCompany, loadCompanies }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
