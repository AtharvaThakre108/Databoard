import api from "../utils/axiosConfig";

export const registerUser = (data) => {
  return api.post("/auth/register", {
    email: String(data.email).trim(),
    password: String(data.password),
  });
};
export const loginUser = (data) => {
  return api.post("/auth/login", {
    email: String(data.email).trim(),
    password: String(data.password),
  });
};
export const getMe = () => api.get("/auth/me");
export const refreshToken = () => api.post("/auth/refresh");
export const logoutUser = () => api.post("/auth/logout");
