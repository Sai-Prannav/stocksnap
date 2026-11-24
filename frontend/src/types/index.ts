export interface Store {
  id: number;
  name: string;
  location?: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface Product {
  id: number;
  name: string;
  sku?: string;
  description?: string;
  category?: string;
  created_at: string;
  updated_at?: string;
}

export interface Detection {
  id: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  label: string;
  confidence: number;
  area?: number;
  properties?: Record<string, any>;
}

export interface SegmentationMask {
  id: number;
  mask_type: string;
  mask_data: Record<string, any>;
  label: string;
  confidence?: number;
  file_path?: string;
  properties?: Record<string, any>;
}

export interface Scan {
  id: number;
  store_id: number;
  product_id: number;
  image_path: string;
  count: number;
  confidence: number;
  scanned_at: string;
  notes?: string;
  store?: Store;
  product?: Product;
  detections?: Detection[];
  segmentation_masks?: SegmentationMask[];
}

export interface ScanList {
  id: number;
  image_path: string;
  count: number;
  confidence: number;
  scanned_at: string;
  store_name: string;
  product_name: string;
}

export interface TimelineDataPoint {
  date: string;
  count: number;
  avg_confidence: number;
  scan_count: number;
}

export interface TimelineRequest {
  store_id?: number;
  product_id?: number;
  start_date?: string;
  end_date?: string;
  group_by?: 'day' | 'week' | 'month';
}

export interface AnalysisStats {
  total_scans: number;
  avg_count: number;
  avg_confidence: number;
  min_count: number;
  max_count: number;
}

export interface StoreCreate {
  name: string;
  location?: string;
  description?: string;
}

export interface ProductCreate {
  name: string;
  sku?: string;
  description?: string;
  category?: string;
}
