export interface Incidence {
  id: number;
  title: string;
  status: 'OPEN' | 'RESOLVED' | 'IGNORED';
  occurrence_count: number;
  users_affected: number;
  last_seen: string;
}

export interface DashboardStats {
  velocity: {
    total_24h: number;
    errors_500: number;
    errors_400: number;
  };
  health: {
    avg_response_time_ms: number;
  };
  top_offenders: Incidence[];
}

export interface Footprint {
  id: number;
  request_id: string;
  request_path: string;
  request_method: string;
  status_code: number;
  response_time: number;
  request_user: string;
  created_at: string;
  // We will add more fields later (headers, body) for the Forensics Lab
}