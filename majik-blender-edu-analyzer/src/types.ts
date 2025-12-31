export type ISODateString = string;

export interface MajikBlenderEduJSON {
  id: string;
  data: RawActionLogEntry[];
  total_working_time: number;
  period: LogPeriod;
  timestamp: ISODateString;
  secret_key?: string;
  student_id?: string;
}

export interface RawActionLogJSON {
  data: RawActionLogEntry[];
  status: string;
  total_working_time: number;
  period: LogPeriod;
}

export interface LogPeriod {
  start: ISODateString;
  end: ISODateString;
}

export interface RawActionLogEntry {
  t: number;
  a: string;
  o: string;
  ot: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  d: Record<string, any>;
  dt: number;
  s: {
    v: number;
    f: number;
    o: number;
  };
  ph: string;
}

export interface ActionLogEntry {
  timestamp: ISODateString;
  actionType: string;
  name: string;
  type: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details?: Record<string, any>;
  duration: number;
  sceneStats: SceneStats;
  hash: string;
}

export interface SceneStats {
  vertex: number;
  face: number;
  object: number;
}

export type HealthSeverity = "healthy" | "warning" | "critical";

export interface ActionLogHealth {
  status: HealthSeverity;
  reasons: string[];
}

export interface MajikBlenderEduSummary {
  totalLogs: number;
  totalWorkingTime: number;
  effectiveTime: number;
  idleRatio: number;
  avgIdleTime: number;
  totalVertices: number;
  totalObjects: number;
  mostActiveObject: string | null;
  actionCounts: Record<string, number>;
  score: number;
  flags: string[];
  verdict: string;
  entropyScore: number;
}
