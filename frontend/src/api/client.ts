import axios from "axios";

export const ACCESS_TOKEN_STORAGE_KEY = "accessToken";

export const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ??
    "http://localhost:8000/api/v1",
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  const token = window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
      window.dispatchEvent(new Event("auth:unauthorized"));
    }

    return Promise.reject(error);
  },
);
