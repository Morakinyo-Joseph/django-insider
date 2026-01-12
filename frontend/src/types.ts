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
  velocity_series: {
    time: string;
    errors: number;
    requests: number;
  }[];
  health: {
    avg_response_time_ms: number;
  };
  top_offenders: Incidence[];
  performance_risks: {
    id: number;
    path: string;
    method: string;
    db_query_count: number;
    avg_duration: number;
  }[];
}

export interface StackFrame {
  file: string;
  line: number;
  function: string;
  code: string;
  is_user_code: boolean;
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
  request_headers?: Record<string, string>; 
  request_body?: any;
  response_body?: any;
  system_logs?: string[];
  db_query_count?: number;
  incidence?: number;
  stack_trace?: StackFrame[]; 
}

export interface InsiderSetting {
  id: number;
  key: string;
  value: any;
  field_type: 'BOOLEAN' | 'INTEGER' | 'LIST' | 'STRING';
  description: string;
}