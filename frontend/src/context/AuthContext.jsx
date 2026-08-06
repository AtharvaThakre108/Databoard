import { createContext, useEffect, useState } from "react";
import { getMe, refreshToken } from "../api/auth";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const refresh = async () => {
    const res = await refreshToken();
    localStorage.setItem("token", res.data.token);
    return res.data.token;
  };

  useEffect(() => {
    const init = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) return;

        const me = await getMe();
        setUser(me.data);
      } catch (err) {
        try {
          await refresh();
          const me = await getMe();
          setUser(me.data);
        } catch {
          logout();
        }
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, logout, loading, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}
