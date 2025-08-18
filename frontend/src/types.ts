export interface Process {
  id: string;
  name: string;
  script_path: string;
  status: 'running' | 'stopped' | 'error' | 'starting';
  pid?: number;
  start_time?: string;
  auto_restart: boolean;
  restart_count: number;
  logs?: string[];
}

export interface Script {
  name: string;
  path: string;
  size: number;
}

export interface ProcessFormData {
  name: string;
  script_path: string;
  auto_restart: boolean;
} 