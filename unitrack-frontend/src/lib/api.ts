import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
});

// Request interceptor to attach access token from localStorage if present
api.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem("access_token");
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // Don't attempt refresh for the refresh endpoint itself
    const requestUrl: string = (originalRequest && originalRequest.url) || "";
    if (requestUrl.includes("/refresh/")) return Promise.reject(error);

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        const cleanUrl = `${import.meta.env.VITE_API_URL.replace(/\/$/, "")}/api/refresh/`;

        const res = await axios.post(
          cleanUrl,
          { refresh: refreshToken },
          { withCredentials: true }
        );

        // Save new access token if returned in response body
        if (res.data && res.data.access) {
          localStorage.setItem("access_token", res.data.access);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${res.data.access}`;
          }
        }

        return api(originalRequest);
      } catch (refreshError) {
        console.error(
          "Refresh token expired, redirecting to login...",
          refreshError
        );
        // Clear stored tokens from localStorage
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        // Avoid redirecting repeatedly if already on the login page
        if (window.location.pathname !== "/auth/login") {
          // Use replace to avoid creating extra history entries
          window.location.replace("/auth/login");
        }
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
