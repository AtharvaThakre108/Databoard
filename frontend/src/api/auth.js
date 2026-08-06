import axios from "axios";
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

// Deliberately NOT using the shared `api` instance here -- going through
// it would attach the (expired) access token via the request
// interceptor, but /auth/refresh requires the REFRESH token as the
// Bearer credential. A plain axios call with an explicit header avoids
// that mix-up entirely.
export const refreshToken = (refresh_token) =>
  axios.post(
    `${api.defaults.baseURL}/auth/refresh`,
    {},
    { headers: { Authorization: `Bearer ${refresh_token}` } }
  );

// No /auth/logout route exists on the backend (JWTs aren't server-side
// revocable in this design -- "logging out" just means the frontend
// discards its tokens). Kept as a no-op export so callers don't need to
// change, but it does nothing server-side.
export const logoutUser = () => Promise.resolve();