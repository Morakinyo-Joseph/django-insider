import axios from 'axios';
import type { DashboardStats, Incidence, Footprint, InsiderSetting } from '../types';

// Manually find the CSRF token in the browser cookies
const getCookie = (name: string) => {
  if (typeof document === "undefined") {
    return null;
  }
  return document.cookie
    .split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith(`${name}=`))
    ?.split("=")[1] ?? null;
};

// Detect environment
const BASE_URL = import.meta.env.DEV 
  ? 'http://127.0.0.1:8000/insider/api/' 
  : '/insider/api/';

// Create the Axios Instance
export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Crucial: Ensures the cookie is sent back
});

// Before every request, manually grab the token and shove it in the header.
apiClient.interceptors.request.use((config) => {
  const token = getCookie("csrftoken");
  if (token) {
    config.headers.set("X-CSRFToken", token);
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});


// --- API FUNCTIONS (Unchanged) ---

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get('stats/dashboard/');
  return response.data;
};

export const fetchIncidences = async (filter?: string): Promise<Incidence[]> => {
  const params = filter ? { filter } : {};
  const response = await apiClient.get('incidences/', { params });
  return response.data;
};

export const bulkResolveIncidences = async (ids: number[]): Promise<void> => {
  await apiClient.post('incidences/bulk_resolve/', { ids });
};

export const bulkIgnoreIncidences = async (ids: number[]): Promise<void> => {
  await apiClient.post('incidences/bulk_ignore/', { ids });
};

export const fetchIncidenceDetail = async (id: string): Promise<any> => {
  const response = await apiClient.get(`incidences/${id}/`);
  return response.data;
};

export const fetchIncidenceFootprints = async (id: string): Promise<Footprint[]> => {
  const response = await apiClient.get(`incidences/${id}/footprints/`);
  return response.data;
};

export const fetchFootprint = async (id: string): Promise<Footprint> => {
  const response = await apiClient.get(`footprints/${id}/`);
  return response.data;
};

export const fetchFootprintBreadcrumbs = async (id: string): Promise<Footprint[]> => {
  const response = await apiClient.get(`footprints/${id}/breadcrumbs/`);
  return response.data;
};

export const fetchSettings = async (): Promise<InsiderSetting[]> => {
  const response = await apiClient.get('settings/');
  return response.data;
};

export const updateSetting = async (id: number, value: any): Promise<void> => {
  await apiClient.patch(`settings/${id}/`, { value });
};