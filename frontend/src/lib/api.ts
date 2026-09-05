import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios"
import { isValidJwtFormat } from "./validation"

const BASE_URL = "https://lubricate-flatness-foster.ngrok-free.dev"

let currentAccessToken: string | null = null

export function setAccessToken(token: string | null): void {
  currentAccessToken = token
}

export function getAccessToken(): string | null {
  return currentAccessToken
}

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (currentAccessToken) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`
  }
  return config
})

let isRefreshing = false
let failedQueue: Array<{
  resolve: (value: unknown) => void
  reject: (reason?: unknown) => void
}> = []

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`
            }
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const res = await api.post("/auth/refresh")
        const newToken = res.data?.data?.access_token
        if (newToken && isValidJwtFormat(newToken)) {
          setAccessToken(newToken)
          originalRequest.headers.Authorization = `Bearer ${newToken}`
          processQueue(null, newToken)
          return api(originalRequest)
        }
        processQueue(new Error("Refresh failed"), null)
        return Promise.reject(error)
      } catch (refreshError) {
        setAccessToken(null)
        processQueue(refreshError as Error, null)
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
