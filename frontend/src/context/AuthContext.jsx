import { createContext, useEffect, useState } from "react";
import { getMe, refreshToken } from "../api/auth";

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  const refresh = async () => {
    const storedRefreshToken = localStorage.getItem("refresh_token");
    if (!storedRefreshToken) {
      throw new Error("No refresh token available");
    }
    const res = await refreshToken(storedRefreshToken);
    localStorage.setItem("access_token", res.data.access_token);
    return res.data.access_token;
  };

  useEffect(() => {
    const init = async () => {
      try {
        const token = localStorage.getItem("access_token");
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