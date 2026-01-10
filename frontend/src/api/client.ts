import axios from 'axios';
import { DashboardStats, Incidence, Footprint, InsiderSetting } from '../types';

// Detect environment: Dev (localhost:8000) vs Prod (Relative path)
const BASE_URL = import.meta.env.DEV 
  ? 'http://127.0.0.1:8000/insider/api/' 
  : '/insider/api/';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- API FUNCTIONS ---

// 1. Dashboard Stats
export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get('stats/dashboard/');
  return response.data;
};

// 2. Incidence List (Modified to support Filters)
export const fetchIncidences = async (filter?: string): Promise<Incidence[]> => {
  // If filter is present, append it to query params
  const params = filter ? { filter } : {};
  const response = await apiClient.get('incidences/', { params });
  return response.data;
};

// 2b. Bulk Actions (New)
export const bulkResolveIncidences = async (ids: number[]): Promise<void> => {
  await apiClient.post('incidences/bulk_resolve/', { ids });
};

export const bulkIgnoreIncidences = async (ids: number[]): Promise<void> => {
  await apiClient.post('incidences/bulk_ignore/', { ids });
};

// 3. Incidence Detail (Investigation Room - Main Data)
export const fetchIncidenceDetail = async (id: string): Promise<any> => {
  const response = await apiClient.get(`incidences/${id}/`);
  return response.data;
};

// 4. Incidence Footprints (Investigation Room - Sidebar)
export const fetchIncidenceFootprints = async (id: string): Promise<Footprint[]> => {
  const response = await apiClient.get(`incidences/${id}/footprints/`);
  return response.data;
};

// 5. Single Footprint (Forensics Lab - Main Data)
export const fetchFootprint = async (id: string): Promise<Footprint> => {
  const response = await apiClient.get(`footprints/${id}/`);
  return response.data;
};

// 6. User History (Forensics Lab - "What did they do before this?")
export const fetchFootprintBreadcrumbs = async (id: string): Promise<Footprint[]> => {
  const response = await apiClient.get(`footprints/${id}/breadcrumbs/`);
  return response.data;
};

// 7. Get All Settings
export const fetchSettings = async (): Promise<InsiderSetting[]> => {
  const response = await apiClient.get('settings/');
  return response.data;
};

// 8. Update a Setting
export const updateSetting = async (id: number, value: any): Promise<void> => {
  // We patch just the 'value' field
  await apiClient.patch(`settings/${id}/`, { value });
};