import axios from 'axios';
import type {
  Store,
  Product,
  Scan,
  ScanList,
  TimelineDataPoint,
  TimelineRequest,
  AnalysisStats,
  StoreCreate,
  ProductCreate
} from '../types';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const storesApi = {
  getAll: () => api.get<Store[]>('/api/stores/'),
  getById: (id: number) => api.get<Store>(`/api/stores/${id}`),
  create: (store: StoreCreate) => api.post<Store>('/api/stores/', store),
  update: (id: number, store: Partial<StoreCreate>) => api.put<Store>(`/api/stores/${id}`, store),
  delete: (id: number) => api.delete(`/api/stores/${id}`),
};

export const productsApi = {
  getAll: () => api.get<Product[]>('/api/products/'),
  getById: (id: number) => api.get<Product>(`/api/products/${id}`),
  create: (product: ProductCreate) => api.post<Product>('/api/products/', product),
  update: (id: number, product: Partial<ProductCreate>) => api.put<Product>(`/api/products/${id}`, product),
  delete: (id: number) => api.delete(`/api/products/${id}`),
};

export const scansApi = {
  getAll: (params?: {
    store_id?: number;
    product_id?: number;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
  }) => api.get<ScanList[]>('/api/scans/', { params }),
  getById: (id: number) => api.get<Scan>(`/api/scans/${id}`),
  create: (formData: FormData) => api.post<Scan>('/api/scans/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  delete: (id: number) => api.delete(`/api/scans/${id}`),
  getAnnotated: (id: number, params?: {
    style?: string;
    show_confidence?: boolean;
    show_labels?: boolean;
  }) => api.get<{ annotated_image_path: string }>(`/api/scans/${id}/annotated`, { params }),
  getAnnotatedSummary: (id: number) => api.get(`/api/scans/${id}/annotated-summary`),
};

export const timelineApi = {
  getData: (request: TimelineRequest) => api.post<TimelineDataPoint[]>('/api/timeline/data', request),
  getStats: (params?: {
    store_id?: number;
    product_id?: number;
  }) => api.get<AnalysisStats>('/api/timeline/stats', { params }),
  getSummary: (params?: {
    days?: number;
    store_id?: number;
    product_id?: number;
  }) => api.get('/api/timeline/summary', { params }),
};

export default api;