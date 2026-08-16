/**
 * A2UI (Agent-to-User Interface) TypeScript Types
 */

export interface ChartDataset {
  label: string;
  data: number[];
  background_color?: string | string[];
  border_color?: string;
}

export interface ChartData {
  chart_type: 'bar' | 'line' | 'pie' | 'doughnut' | 'radar';
  title: string;
  subtitle?: string;
  labels: string[];
  datasets: ChartDataset[];
}

export interface MapMarker {
  id?: string;
  title: string;
  lat: number;
  lng: number;
  description?: string;
  category?: string;
  icon?: string;
}

export interface MapData {
  title: string;
  center_lat: number;
  center_lng: number;
  zoom: number;
  markers: MapMarker[];
}

export type MetricStatus = 'neutral' | 'positive' | 'negative' | 'warning' | 'info' | 'critical' | 'error';

export interface MetricItem {
  label: string;
  value: string | number;
  delta?: string;
  status?: MetricStatus;
  icon?: string;
}

export interface MetricCardData {
  title: string;
  metrics: MetricItem[];
}

export interface PhotoItem {
  id?: string;
  title: string;
  image_url: string;
  thumbnail_url?: string;
  caption?: string;
  link?: string;
  date?: string;
}

export interface PhotoGalleryData {
  title: string;
  items: PhotoItem[];
}

export interface DataTableData {
  title: string;
  columns: string[];
  rows: (string | number | boolean | null)[][];
  searchable?: boolean;
  sortable?: boolean;
}

export interface A2UIAction {
  label: string;
  action_type: 'prompt' | 'link' | 'filter';
  payload: string;
}

export type A2UIComponentType = 'chart' | 'map' | 'metric_card' | 'photo_gallery' | 'data_table';

export interface A2UIComponent {
  id: string;
  type: A2UIComponentType;
  title?: string;
  data: ChartData | MapData | MetricCardData | PhotoGalleryData | DataTableData | any;
  actions?: A2UIAction[];
}

export interface A2UIPayload {
  version: string;
  layout?: 'vertical' | 'grid' | 'carousel' | 'tabs';
  components: A2UIComponent[];
}

export interface AgentTraceStep {
  id: string;
  stage: 'gateway' | 'expert' | 'tool' | 'a2ui' | 'completed';
  title: string;
  agent?: string;
  tool?: string;
  args?: string;
  detail?: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  timestamp: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model';
  content: string;
  command?: string;
  a2ui?: A2UIPayload | null;
  traces?: AgentTraceStep[];
  statusMessage?: string;
  isStreaming?: boolean;
  timestamp: number;
}
