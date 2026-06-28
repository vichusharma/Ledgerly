/**
 * Axios API client — all requests go through /api/v1.
 * The Next.js rewrite forwards them to the FastAPI backend.
 */
import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,  // include httpOnly session cookie
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      // Redirect to login (handled by middleware or layout)
      if (typeof window !== "undefined") {
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(err);
  }
);
