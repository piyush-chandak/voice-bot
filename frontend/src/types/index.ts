export interface User {
  id: number;
  username: str;
  email: str;
  role: "Technician" | "Supervisor" | "Admin";
  isActive: bool;
}

export interface TokenData {
  access_token: string;
  token_type: string;
}

export interface Asset {
  id: number;
  name: string;
  description?: string;
  sku: string;
  latitude: number;
  longitude: number;
  status: "operational" | "maintenance_required" | "down" | string;
  distance?: number;
}

export interface Ticket {
  id: number;
  title: string;
  description: string;
  status: "open" | "in_progress" | "resolved" | "closed" | string;
  priority: "low" | "medium" | "high" | "critical" | string;
  technician_id: number;
  asset_id: number;
  asset?: Asset;
  created_at?: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  timestamp: string;
  audioUrl?: string;
  intent?: string;
  data?: any;
}
export type str = string;
export type bool = boolean;
