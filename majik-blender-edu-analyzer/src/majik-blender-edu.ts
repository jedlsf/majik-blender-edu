import { customAlphabet } from "nanoid";
import {
  ActionLogEntry,
  ISODateString,
  RawActionLogEntry,
  RawActionLogJSON,
  LogPeriod,
  MajikBlenderEduJSON,
  HealthSeverity,
  ActionLogHealth,
  MajikBlenderEduSummary,
  SceneStats,
  RawSceneStats,
} from "./types";
import {
  calculateDuration,
  computeEntryHash,
  DEFAULT_COLORS,
  generateGenesisKey,
  isSessionStartLog,
  validateLogIntegrity,
} from "./utils";
import {
  BarChartTrace,
  createBarTrace,
  createLineTrace,
  createPieTrace,
  PieChartTrace,
  TimeSeriesTrace,
} from "./plotly";

export class MajikBlenderEdu {
  private id: string;
  public logs: ActionLogEntry[];
  _raw_logs: RawActionLogEntry[];
  public timestamp: string;
  private period: LogPeriod;
  private total_working_time: number;
  private secret_key?: string;
  private student_id?: string;
  private sceneStats: SceneStats;

  constructor(
    id: string = autogenerateID("mjkbedu"),
    logs: ActionLogEntry[] = [],
    raw_logs: RawActionLogEntry[] = [],
    period: LogPeriod,
    sceneStats: RawSceneStats,
    time: number = 0,
    timestamp: string = new Date().toISOString(),
    secret_key?: string,
    student_id?: string
  ) {
    this.id = id;
    this.logs = logs;
    this._raw_logs = raw_logs;
    this.period = period;
    this.sceneStats = {
      vertex: sceneStats.v,
      face: sceneStats.f,
      object: sceneStats.o,
    };
    this.total_working_time = time;
    this.timestamp = timestamp;
    this.secret_key = secret_key;
    this.student_id = student_id;

    this.normalizeDuration();
    this.updateTotalWorkingTime();
  }

  private static readonly HEALTH_THRESHOLDS = {
    idleCritical: 0.9,
    idleWarning: 0.7,
    entropyWarning: 1.2,
    entropyHealthy: 1.5,
    minVertices: 50,
    minActions: 20,
    repetitiveThreshold: 5,
    vertexJumpThreshold: 500, // Default threshold for suspicious imports
    maxWorkGap: 1800, // 30 minutes: durations longer than this are considered "breaks", not "idling"
  };

  /** Transpose a single raw log entry into structured ActionLogEntry */
  private static transposeLog(raw: RawActionLogEntry): ActionLogEntry {
    return {
      timestamp: new Date(raw.t * 1000).toISOString(), // convert Unix timestamp to ISO
      actionType: raw.a,
      name: raw.o,
      type: raw.ot,
      details: raw.d ?? {},
      duration: raw.dt ?? 0,
      sceneStats: {
        vertex: raw.s?.v ?? 0,
        face: raw.s?.f ?? 0,
        object: raw.s?.o ?? 0,
      },
      hash: raw.ph,
    };
  }

  /** Convert a structured ActionLogEntry back into a RawActionLogEntry */
  private static reverseTransposeLog(
    parsed: ActionLogEntry
  ): RawActionLogEntry {
    return {
      t: Math.floor(new Date(parsed.timestamp).getTime() / 1000), // ISO → Unix timestamp
      a: parsed.actionType,
      o: parsed.name,
      ot: parsed.type,
      d: parsed.details ?? {},
      dt: parsed.duration ?? 0,
      s: {
        v: parsed.sceneStats.vertex ?? 0,
        f: parsed.sceneStats.face ?? 0,
        o: parsed.sceneStats.object ?? 0,
      },
      ph: parsed.hash,
    };
  }

  public getID(): string {
    return this.id;
  }

  public getTotalWorkingTime(): number {
    return this.total_working_time;
  }

  public getPeriod(): LogPeriod {
    return this.period;
  }

  private getStudentLogs(): ActionLogEntry[] {
    return this.logs.slice(1);
  }

  /** Static initializer to create an instance from raw logs */
  public static initialize(
    rawJSON: RawActionLogJSON,
    secretKey?: string,
    studentID?: string,
    id?: string,
    timestamp?: string
  ): MajikBlenderEdu {
    const logs = rawJSON.data.map(MajikBlenderEdu.transposeLog);

    const newInstance = new MajikBlenderEdu(
      id,
      logs,
      rawJSON.data,
      rawJSON.period,
      rawJSON.stats,
      rawJSON.total_working_time,
      timestamp,
      secretKey,
      studentID
    );

    if (!newInstance.validateGenesis()) {
      throw new Error("Invalid Credentials");
    }
    return newInstance;
  }

  // ---------------------------
  // Raw / Parsed Log Additions
  // ---------------------------

  /** Add a raw log entry and update the parsed logs automatically */
  public addRawLog(rawLog: RawActionLogEntry) {
    const exists = this._raw_logs.some((r) => r.ph === rawLog.ph);
    if (exists) return;

    this._raw_logs.push(rawLog);
    this.logs.push(MajikBlenderEdu.transposeLog(rawLog));
    this.updateTotalWorkingTime();
  }

  /** Add a pre-parsed log entry and update the raw logs automatically */
  public addParsedLog(parsedLog: ActionLogEntry) {
    const exists = this.logs.some((l) => l.hash === parsedLog.hash);
    if (exists) return;

    this.logs.push(parsedLog);

    const raw = MajikBlenderEdu.reverseTransposeLog(parsedLog);
    this._raw_logs.push(raw);

    this.updateTotalWorkingTime();
  }

  /** Wrapper that auto-detects the type of log and calls the appropriate method */
  public addLog(log: RawActionLogEntry | ActionLogEntry) {
    if ("t" in log) {
      this.addRawLog(log);
    } else {
      this.addParsedLog(log);
    }
  }

  /** Overwrite the entire logs array */
  public setLogs(logs: (RawActionLogEntry | ActionLogEntry)[]) {
    this.logs = logs.map((log) =>
      "t" in log ? MajikBlenderEdu.transposeLog(log) : log
    );
    this._raw_logs = this.logs.map(MajikBlenderEdu.reverseTransposeLog);
    this.updateTotalWorkingTime();
  }

  /** Clear all logs */
  public clearLogs() {
    this.logs = [];
    this._raw_logs = [];
    this.total_working_time = 0;
  }

  /** Optional: get total number of logs */
  public getLogCount(): number {
    return this.logs.length;
  }

  public getLogsByActionType(actionType: string): ActionLogEntry[] {
    return this.logs.filter((log) => log.actionType === actionType);
  }

  public getLogsInTimeRange(
    start: ISODateString,
    end: ISODateString
  ): ActionLogEntry[] {
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();

    return this.logs.filter((log) => {
      const logTime = new Date(log.timestamp).getTime();
      return logTime >= startTime && logTime <= endTime;
    });
  }

  /**
   * REVISED: Calculate total time spent actually working.
   * Excludes massive gaps (breaks) so they don't bloat the idle ratio.
   */
  private updateTotalWorkingTime() {
    const studentLogs = this.getStudentLogs();
    // Sum only durations that aren't considered "Back from break" gaps
    this.total_working_time = studentLogs.reduce((sum, log) => {
      const d = log.duration ?? 0;
      return d > MajikBlenderEdu.HEALTH_THRESHOLDS.maxWorkGap ? sum : sum + d;
    }, 0);
  }

  /** Set teacher/student credentials for integrity checks */
  public setCredentials(secretKey: string, studentID: string) {
    this.secret_key = secretKey;
    this.student_id = studentID;
  }

  /** Get the expected genesis hash for this instance */
  public getGenesisHash(): string | undefined {
    if (!this.secret_key || !this.student_id) return undefined;
    const genesisKey = generateGenesisKey(this.secret_key, this.student_id);

    return genesisKey;
  }

  /** Validate if the first log entry matches the genesis key */
  public validateGenesis(): boolean {
    if (!this.logs.length || !this.secret_key || !this.student_id) return false;
    const genesisHash = this.getGenesisHash();
    return this.logs[0].hash === genesisHash;
  }

  /** Validate the entire log chain for integrity */
  public validateLogChain(): boolean {
    if (!this.logs.length || !this.secret_key || !this.student_id) return false;

    return validateLogIntegrity(
      this._raw_logs,
      this.secret_key,
      this.student_id
    );
  }

  /** Validate a single entry against the previous hash */
  public validateEntry(
    entry: RawActionLogEntry,
    prevEntry?: RawActionLogEntry
  ): boolean {
    const expectedPrev = prevEntry
      ? computeEntryHash(prevEntry)
      : this.getGenesisHash();
    return entry.ph === expectedPrev;
  }

  /**
   * Normalizes duration for parsed logs by calculating
   * elapsed time between consecutive entries.
   *
   * - Applies ONLY to `this.logs`
   * - Skips genesis entry
   * - Does NOT mutate raw logs
   */
  private normalizeDuration(): void {
    if (this.logs.length < 2) return;

    for (let i = 1; i < this.logs.length; i++) {
      const prev = this.logs[i - 1];
      const curr = this.logs[i];

      curr.duration = calculateDuration(prev, curr);
    }

    // Genesis log always has 0 duration
    this.logs[0].duration = 0;
  }

  // ---------------------------
  // Basic Log Queries
  // ---------------------------

  /**
   * Get all logs for a specific object name.
   * @param name - Object name to filter logs by
   * @returns Array of ActionLogEntry
   */
  public getLogsByObjectName(name: string): ActionLogEntry[] {
    return this.logs.filter((log) => log.name === name);
  }

  /**
   * Get all logs that involve a specific object type
   * @param type - Object type (e.g., 'MESH', 'CURVE')
   * @returns Array of ActionLogEntry
   */
  public getLogsByObjectType(type: string): ActionLogEntry[] {
    return this.logs.filter((log) => log.type === type);
  }

  /**
   * Get all unique object names in the logs
   * @returns Array of unique object names
   */
  public getUniqueObjects(): string[] {
    return [...new Set(this.logs.map((log) => log.name))];
  }

  // ---------------------------
  // Time & Activity Analysis
  // ---------------------------

  /**
   * Get the working period (start/end) in ISO format
   * @returns Object with start and end ISO strings
   */
  public getWorkingPeriod(): { start: ISODateString; end: ISODateString } {
    if (this.logs.length < 2) {
      const now = new Date().toISOString();
      return { start: now, end: now };
    }

    const start = this.logs[1].timestamp; // skip genesis
    const end = this.logs[this.logs.length - 1].timestamp;
    return { start, end };
  }

  /**
   * Get idle periods between logs in seconds
   * @returns Array of idle periods in seconds
   */
  public getIdlePeriods(): number[] {
    const filteredLogs = this.getStudentLogs().filter(
      (log) => !isSessionStartLog(log)
    );
    return filteredLogs.slice(1).map((log) => log.duration ?? 0);
  }

  /**
   * REVISED: Idle ratio now compares focused work vs. minor distractions
   * within active sessions, ignoring long breaks.
   */
  public getIdleRatio(): number {
    const totalActive = this.total_working_time;
    if (totalActive <= 0) return 0;

    const effective = this.getEffectiveWorkingTime();
    // Ratio of (Short Gaps) / (Total Active Time)
    const ratio = (totalActive - effective) / totalActive;
    return Number(Math.max(0, ratio).toFixed(2));
  }

  /**
   * Get the average idle time in seconds
   * @returns Average idle time
   */
  public getAverageIdleTime(): number {
    const idle = this.getIdlePeriods();
    if (!idle.length) return 0;
    return Math.round(idle.reduce((a, b) => a + b, 0) / idle.length);
  }

  public getEffectiveWorkingTime(maxIdleGapSec = 300): number {
    let total = 0;
    const filteredLogs = this.getStudentLogs().filter(
      (l) => !isSessionStartLog(l)
    );

    for (const log of filteredLogs) {
      const d = log.duration ?? 0;
      // If the gap is small (e.g. < 5 mins), it counts as "Effective/Present"
      if (d <= maxIdleGapSec) {
        total += d;
      }
    }
    return Math.round(total);
  }

  // ---------------------------
  // Scene Statistics
  // ---------------------------

  /**
   * Get total vertex count added across all logs
   * @returns Total vertex count
   */
  public getTotalVertices(): number {
    return this.sceneStats.vertex;
  }

  /**
   * Get total object count changes across logs
   * @returns Total object count
   */
  public getTotalObjects(): number {
    return this.sceneStats.object;
  }

  /**
   * Get average object count per log
   * @returns Average object count
   */
  public getAverageObjects(): number {
    if (!this.logs.length) return 0;
    return Math.round(this.getTotalObjects() / this.logs.length);
  }

  // ---------------------------
  // Vertex & Authenticity Analysis (Requested Methods)
  // ---------------------------

  /** 1. Get average vertices across all logs */

  /**
   * Get average vertices per log
   * @returns Average vertex count
   */
  public getAverageVertices(): number {
    if (!this.logs.length) return 0;
    return Math.round(this.getTotalVertices() / this.logs.length);
  }

  /** 2. Get average vertices prior to a specific log entry */
  public getAverageVerticesPrior(entry: ActionLogEntry): number {
    const entryIdx = this.logs.findIndex((l) => l.hash === entry.hash);
    if (entryIdx <= 0) return 0; // No logs before this or entry not found

    const priorLogs = this.logs.slice(0, entryIdx);
    const totalPriorVertices = priorLogs.reduce(
      (sum, log) => sum + (log.sceneStats.vertex ?? 0),
      0
    );
    return Math.round(totalPriorVertices / priorLogs.length);
  }

  /** 3. Check if the average vertices prior to a log is greater than a threshold */
  public hasHighComplexityContext(
    entry: ActionLogEntry,
    threshold = 500
  ): boolean {
    return this.getAverageVerticesPrior(entry) > threshold;
  }

  /** 4. Check if action is a Mesh Addition */
  public isMeshAddition(entry: ActionLogEntry): boolean {
    return entry.actionType === "Added Mesh" && entry.type === "MESH";
  }

  /** 5. Flag big jumps (Potential Imports)
   * Detects if a mesh addition results in a vertex count significantly
   * higher than the average complexity established so far.
   */
  public hasSuspiciousVertexJump(
    entry: ActionLogEntry,
    threshold = MajikBlenderEdu.HEALTH_THRESHOLDS.vertexJumpThreshold
  ): boolean {
    if (!this.isMeshAddition(entry)) return false;

    const avgPrior = this.getAverageVerticesPrior(entry);
    const currentVerts = entry.sceneStats.vertex ?? 0;

    // Flag if the new mesh is significantly denser than the average previous scene state
    return currentVerts > avgPrior + threshold;
  }

  /** Checks all logs for any suspicious import jumps */
  public detectAllImportJumps(): ActionLogEntry[] {
    return this.logs.filter((log) => this.hasSuspiciousVertexJump(log));
  }

  // ---------------------------
  // Action & Frequency Analysis
  // ---------------------------

  public hasLogTamperingIndicators(): boolean {
    return !this.validateGenesis() || !this.validateLogChain();
  }

  public getActionEntropy(): number {
    const counts = this.getActionCounts();
    const total = this.getStudentLogs().length;
    let entropy = 0;

    for (const key in counts) {
      const p = counts[key] / total;
      entropy -= p * Math.log2(p);
    }

    return Number(entropy.toFixed(2));
  }

  public getRepetitiveActionBursts(threshold = 5): string[] {
    const bursts: string[] = [];
    let streak = 1;

    const studentLogs = this.getStudentLogs();

    for (let i = 2; i < studentLogs.length; i++) {
      if (studentLogs[i].actionType === studentLogs[i - 1].actionType) {
        streak++;
        if (streak === threshold) {
          bursts.push(studentLogs[i].actionType);
        }
      } else {
        streak = 1;
      }
    }

    return [...new Set(bursts)];
  }

  public getSceneGrowthOverTime(): {
    time: ISODateString;
    vertices: number;
  }[] {
    return this.logs.slice(1).map((log) => ({
      time: log.timestamp,
      vertices: log.sceneStats.vertex,
    }));
  }

  public hasMeaningfulProgress(
    minVertices = MajikBlenderEdu.HEALTH_THRESHOLDS.minVertices,
    minActions = MajikBlenderEdu.HEALTH_THRESHOLDS.minActions
  ): boolean {
    return (
      this.getTotalVertices() >= minVertices && this.logs.length >= minActions
    );
  }

  /**
   * Count the number of times each action type occurs
   * @returns Object mapping actionType → count
   */
  public getActionCounts(): Record<string, number> {
    return this.getStudentLogs().reduce((acc: Record<string, number>, log) => {
      acc[log.actionType] = (acc[log.actionType] ?? 0) + 1;
      return acc;
    }, {});
  }

  /**
   * Count how many times a specific object was modified
   * @param objectName - Name of object
   * @returns Number of modifications
   */
  public getObjectActionCount(objectName: string): number {
    return this.logs.filter((log) => log.name === objectName).length;
  }

  /**
   * Get most frequently acted upon object
   * @returns Object name
   */
  public getMostActiveObject(): string | null {
    const counts: Record<string, number> = {};
    this.logs.forEach((log) => {
      counts[log.name] = (counts[log.name] ?? 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted.length ? sorted[0][0] : null;
  }

  // ---------------------------
  // Advanced Metrics
  // ---------------------------

  /**
   * Get cumulative time spent on each action type
   * @returns Object mapping actionType → total duration (seconds)
   */
  public getActionDurations(): Record<string, number> {
    return this.getStudentLogs().reduce((acc: Record<string, number>, log) => {
      acc[log.actionType] = (acc[log.actionType] ?? 0) + (log.duration ?? 0);
      return acc;
    }, {});
  }

  /**
   * Get actions sorted by duration (descending)
   * @returns Array of ActionLogEntry
   */
  public getActionsByLongestDuration(): ActionLogEntry[] {
    return [...this.logs].sort((a, b) => (b.duration ?? 0) - (a.duration ?? 0));
  }

  /**
   * Get log summary statistics for teacher dashboards
   * @returns Summary object
   */
  public getSummary(): MajikBlenderEduSummary {
    return {
      totalLogs: this.logs.length,
      totalWorkingTime: this.getTotalWorkingTime(),
      effectiveTime: this.getEffectiveWorkingTime(),
      idleRatio: this.getIdleRatio(),
      avgIdleTime: this.getAverageIdleTime(),
      totalVertices: this.getTotalVertices(),
      totalObjects: this.getTotalObjects(),
      mostActiveObject: this.getMostActiveObject(),
      actionCounts: this.getActionCounts(),
      score: this.getAuthenticityScore(),
      flags: this.detectSuspiciousPatterns(),
      verdict: this.getAssessmentVerdict(),
      entropyScore: this.getActionEntropy(),
    };
  }

  public getEduHealth(): ActionLogHealth {
    const reasons: string[] = [];
    let maxSeverity: HealthSeverity = "healthy";

    const severityRank: Record<HealthSeverity, number> = {
      healthy: 0,
      warning: 1,
      critical: 2,
    };

    const escalate = (severity: HealthSeverity, reason: string) => {
      reasons.push(reason);
      if (severityRank[severity] > severityRank[maxSeverity]) {
        maxSeverity = severity;
      }
    };

    const idleRatio = this.getIdleRatio();
    const actionEntropy = this.getActionEntropy();
    const totalVertices = this.getTotalVertices();
    const totalActions = this.getStudentLogs().length;
    const repetitiveBursts = this.getRepetitiveActionBursts();
    const tampering = this.hasLogTamperingIndicators();

    /* ----------------------------- Critical checks ---------------------------- */
    if (tampering) escalate("critical", "Log integrity issues detected");
    const jumps = this.detectAllImportJumps();
    if (jumps.length > 0) {
      // We escalate based on the SEVERITY of the jump
      const maxJump = Math.max(...jumps.map((j) => j.sceneStats.vertex));
      if (maxJump > 2000) {
        escalate(
          "critical",
          `Extremely high-poly import detected (${maxJump} vertices)`
        );
      } else {
        escalate("warning", "Potential mesh imports detected");
      }
    }

    if (totalActions === 0)
      escalate("critical", "No student activity recorded");
    if (idleRatio > MajikBlenderEdu.HEALTH_THRESHOLDS.idleCritical)
      escalate("critical", "Excessive idle time");
    /* ------------------------------ Warning checks ----------------------------- */
    if (idleRatio > MajikBlenderEdu.HEALTH_THRESHOLDS.idleWarning)
      escalate("warning", "High idle time");
    if (actionEntropy < MajikBlenderEdu.HEALTH_THRESHOLDS.entropyWarning)
      escalate("warning", "Low action diversity");
    if (
      totalVertices < MajikBlenderEdu.HEALTH_THRESHOLDS.minVertices &&
      totalActions >= MajikBlenderEdu.HEALTH_THRESHOLDS.minActions
    )
      escalate("warning", "Low scene progress despite activity");
    if (
      repetitiveBursts.length >=
      MajikBlenderEdu.HEALTH_THRESHOLDS.repetitiveThreshold
    )
      escalate("warning", "Repetitive action bursts detected");

    /* ------------------------------ Healthy signals ---------------------------- */
    if (idleRatio < 0.3 && actionEntropy >= 1.5 && totalVertices >= 50)
      escalate("healthy", "Student shows consistent and diverse activity");

    if (reasons.length === 0) {
      reasons.push("All metrics are within acceptable thresholds");
    }

    return {
      status: maxSeverity,
      reasons,
    };
  }

  public detectSuspiciousPatterns(): string[] {
    const flags: string[] = [];
    const jumpLogs = this.detectAllImportJumps();

    if (
      this.getActionEntropy() < MajikBlenderEdu.HEALTH_THRESHOLDS.entropyWarning
    )
      flags.push("Low action diversity");

    if (this.getIdleRatio() > MajikBlenderEdu.HEALTH_THRESHOLDS.idleCritical)
      flags.push("Excessive idle time");

    if (jumpLogs.length > 0)
      flags.push(`Suspicious vertex jumps detected (${jumpLogs.length})`);

    if (this.getRepetitiveActionBursts().length)
      flags.push("Repetitive action bursts detected");

    if (!this.hasMeaningfulProgress()) flags.push("Low scene progress");

    if (this.hasLogTamperingIndicators()) flags.push("Log integrity issues");

    return flags;
  }

  public getAssessmentVerdict(): string {
    const flags = this.detectSuspiciousPatterns();

    if (!flags.length) return "Authentic work with consistent effort.";
    if (flags.length <= 2) return "Mostly authentic with minor concerns.";

    return "Potential integrity or effort issues detected.";
  }

  public getAuthenticityScore(): number {
    let score = 100;

    if (!this.validateLogChain()) score -= 40;
    if (this.getIdleRatio() > MajikBlenderEdu.HEALTH_THRESHOLDS.idleWarning)
      score -= 20;
    if (this.detectAllImportJumps().length > 0) score -= 40;
    if (
      this.getActionEntropy() < MajikBlenderEdu.HEALTH_THRESHOLDS.entropyWarning
    )
      score -= 20;
    if (!this.hasMeaningfulProgress()) score -= 20;

    return Math.max(0, score);
  }

  /**
   * Detects “all work done in 5 minutes before deadline”.
   * @returns
   */
  public getActionDensityPerMinute(): Record<string, number> {
    const buckets: Record<string, number> = {};

    for (const log of this.logs.slice(1)) {
      const minute = log.timestamp.slice(0, 16); // YYYY-MM-DDTHH:MM
      buckets[minute] = (buckets[minute] ?? 0) + 1;
    }

    return buckets;
  }

  // ---------------------------
  // Plotly Trace Generators
  // ---------------------------

  /**
   * Line chart showing scene vertex growth over time.
   * This reflects actual modeling effort and scene complexity.
   */
  public getPlotlySceneGrowthOverTime(): TimeSeriesTrace[] {
    const data = this.getSceneGrowthOverTime();

    return [
      createLineTrace({
        x: data.map((d) => d.time),
        y: data.map((d) => d.vertices),
        name: "Vertices",
        hovertemplate: "%{x}<br>Vertices: %{y}<extra></extra>",
      }),
    ];
  }

  /**
   * Line chart showing action density per minute (burst activity)
   */
  public getPlotlyActionDensity(): TimeSeriesTrace[] {
    const density = this.getActionDensityPerMinute();

    return [
      createLineTrace({
        x: Object.keys(density),
        y: Object.values(density),
        name: "Actions per Minute",
        hovertemplate: "%{x}<br>Actions: %{y}<extra></extra>",
      }),
    ];
  }

  /**
   * Bar chart showing count of each action type.
   */
  public getPlotlyActionCountBar(
    color: string = DEFAULT_COLORS.blue
  ): BarChartTrace[] {
    const counts = this.getActionCounts();
    return [
      createBarTrace({
        name: "Action Counts",
        x: Object.keys(counts),
        y: Object.values(counts),
        color: color,
        hovertemplate: "%{x}: %{y}<extra></extra>",
      }),
    ];
  }

  /**
   * Bar chart showing most active objects by number of logs.
   */
  public getPlotlyMostActiveObjectsBar(
    topN = 10,
    color: string = DEFAULT_COLORS.green
  ): BarChartTrace[] {
    const counts: Record<string, number> = {};
    this.logs.forEach((log) => {
      counts[log.name] = (counts[log.name] ?? 0) + 1;
    });

    const sorted = Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN);

    return [
      createBarTrace({
        name: "Most Active Objects",
        x: sorted.map(([name]) => name),
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        y: sorted.map(([_, count]) => count),
        color: color,
        hovertemplate: "%{x}: %{y}<extra></extra>",
      }),
    ];
  }

  /**
   * Pie chart showing distribution of actions by actionType
   * (excluding SYSTEM-origin logs).
   */
  public getPlotlyActionTypePie(): PieChartTrace[] {
    const counts = this.getStudentLogs()
      .filter((log) => log.type !== "SYSTEM")
      .reduce((acc: Record<string, number>, log) => {
        acc[log.actionType] = (acc[log.actionType] ?? 0) + 1;
        return acc;
      }, {});

    const filteredCounts = Object.fromEntries(
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      Object.entries(counts).filter(([_, v]) => v > 0)
    );

    if (!Object.keys(filteredCounts).length) return [];

    return [
      createPieTrace({
        name: "Action Types",
        labels: Object.keys(counts),
        values: Object.values(counts),
        hovertemplate: "%{label}: %{value} (%{percent})<extra></extra>",
      }),
    ];
  }

  /**
   * Pie chart summarizing student health (healthy/warning/critical)
   */
  public getPlotlyHealthStatusPie(): PieChartTrace[] {
    const health = this.getEduHealth();
    const statusCount: Record<string, number> = {
      healthy: 0,
      warning: 0,
      critical: 0,
    };

    if (health.status) statusCount[health.status] = 1;

    return [
      createPieTrace({
        labels: Object.keys(statusCount),
        values: Object.values(statusCount),
        name: "Health Status",
        hovertemplate: "%{label}: %{value}<extra></extra>",
      }),
    ];
  }

  /**
   * Line chart showing idle periods over time (in seconds)
   */
  public getPlotlyIdleTimeTraces(): TimeSeriesTrace[] {
    const idlePeriods = this.getIdlePeriods();
    const timestamps = this.logs.slice(2).map((log) => log.timestamp);

    if (!idlePeriods.length) return [];

    return [
      createLineTrace({
        x: timestamps,
        y: idlePeriods,
        name: "Idle Periods (sec)",
        hovertemplate: "%{x}<br>Idle: %{y} sec<extra></extra>",
      }),
    ];
  }

  /**
   * Stacked bar chart showing cumulative action durations per action type
   */
  public getPlotlyActionDurationsBar(
    color: string = DEFAULT_COLORS.green
  ): BarChartTrace[] {
    const durations = this.getActionDurations();

    return [
      createBarTrace({
        name: "Action Durations (sec)",
        x: Object.keys(durations),
        y: Object.values(durations),
        color: color,
        hovertemplate: "%{x}: %{y} sec<extra></extra>",
      }),
    ];
  }

  /**
   * Line chart showing action entropy over time
   */
  public getPlotlyEntropyTrend(): TimeSeriesTrace[] {
    const studentLogs = this.getStudentLogs();
    if (!studentLogs.length) return [];

    const timestamps: string[] = [];
    const entropies: number[] = [];
    const windowSize = 10; // entropy calculated per 10 logs

    for (let i = 0; i < studentLogs.length; i++) {
      if (i < windowSize) continue;

      const slice = studentLogs.slice(i - windowSize, i);
      const counts: Record<string, number> = {};
      slice.forEach(
        (log) => (counts[log.actionType] = (counts[log.actionType] ?? 0) + 1)
      );
      const total = slice.length;
      let entropy = 0;
      for (const key in counts) {
        const p = counts[key] / total;
        entropy -= p * Math.log2(p);
      }

      timestamps.push(studentLogs[i].timestamp);
      entropies.push(Number(entropy.toFixed(2)));
    }

    if (!timestamps.length) return [];

    return [
      createLineTrace({
        x: timestamps,
        y: entropies,
        name: "Action Entropy",
        hovertemplate: "%{x}<br>Entropy: %{y}<extra></extra>",
      }),
    ];
  }

  /**
   * Bar chart showing repetitive action bursts
   */
  public getPlotlyRepetitiveActionBurstsBar(
    color: string = DEFAULT_COLORS.red
  ): BarChartTrace[] {
    const bursts = this.getRepetitiveActionBursts();
    if (!bursts.length) return [];

    const counts: Record<string, number> = {};
    bursts.forEach((a) => (counts[a] = (counts[a] ?? 0) + 1));

    return [
      createBarTrace({
        name: "Repetitive Action Bursts",
        x: Object.keys(counts),
        y: Object.values(counts),
        hovertemplate: "%{x}: %{y} bursts<extra></extra>",
        color: color,
      }),
    ];
  }

  /**
   * Pie chart showing authenticity score vs potential issues
   */
  public getPlotlyAuthenticityScorePie(
    colors: string[] = [DEFAULT_COLORS.green, DEFAULT_COLORS.red]
  ): PieChartTrace[] {
    const score = this.getAuthenticityScore();
    const remaining = 100 - score;

    return [
      createPieTrace({
        labels: ["Score", "Issues"],
        values: [score, remaining],
        colors: colors,
        name: "Health Status",
        hovertemplate: "%{label}: %{value}<extra></extra>",
      }),
    ];
  }

  /**
   * Bar chart showing flags detected (if any)
   */
  public getPlotlySuspiciousFlagsBar(
    color: string = DEFAULT_COLORS.red
  ): BarChartTrace[] {
    const flags = this.detectSuspiciousPatterns();
    if (!flags.length) return [];

    const counts: Record<string, number> = {};
    flags.forEach((f) => (counts[f] = (counts[f] ?? 0) + 1));

    return [
      createBarTrace({
        name: "Detected Flags",
        x: Object.keys(counts),
        y: Object.values(counts),
        hovertemplate: "%{x}: %{y}<extra></extra>",
        color: color,
      }),
    ];
  }

  // ---------------------------
  // Export & Reporting
  // ---------------------------

  /**
   * Static method to parse a JSON string or object into a `MajikBlenderEdu` instance.
   *
   * @param json - A JSON string or plain object to be parsed.
   * @returns {MajikBlenderEdu} - A new MajikBlenderEdu instance based on the parsed JSON.
   * @throws Will throw an error if required properties are missing.
   */

  static parseFromJSON(json: string | MajikBlenderEduJSON): MajikBlenderEdu {
    // If the input is a string, parse it as JSON
    const rawParse: MajikBlenderEduJSON =
      typeof json === "string"
        ? JSON.parse(json)
        : structuredClone
        ? structuredClone(json)
        : JSON.parse(JSON.stringify(json));

    const logs = rawParse.data.map(MajikBlenderEdu.transposeLog);

    return new MajikBlenderEdu(
      rawParse?.id,
      logs,
      rawParse?.data,
      rawParse.period,
      {
        v: rawParse.stats.vertex,
        f: rawParse.stats.face,
        o: rawParse.stats.object,
      },
      rawParse?.total_working_time,
      rawParse?.timestamp,
      rawParse?.secret_key,
      rawParse?.student_id
    );
  }

  /**
   * Export logs to JSON
   * @returns JSON
   */
  public toJSON(): MajikBlenderEduJSON {
    return {
      id: this.id,
      timestamp: this.timestamp,
      period: this.period,
      total_working_time: this.total_working_time,
      data: this._raw_logs,
      secret_key: this.secret_key,
      student_id: this.student_id,
      stats: this.sceneStats,
    };
  }

  /**
   * Export logs as CSV
   * @returns CSV string
   */
  public exportCSV(): string {
    const header =
      "timestamp,actionType,name,type,duration,vertex,face,object\n";
    const rows = this.logs.map(
      (log) =>
        `${log.timestamp},${log.actionType},${log.name},${log.type},${log.duration},${log.sceneStats.vertex},${log.sceneStats.face},${log.sceneStats.object}`
    );
    return header + rows.join("\n");
  }
}

/**
 * Generates a unique, URL-safe ID for an item based on its name and current timestamp.
 *
 * @param prefix - The prefix string name to add.
 * @returns A unique ID string prefixed.
 */
function autogenerateID(prefix: string = "majik"): string {
  // Create the generator function ONCE with your custom alphabet and length
  const generateID = customAlphabet(
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    8
  );

  // Call the generator function to produce the actual ID string
  const genUID = generateID(); // Example output: 'G7K2aZp9'

  return `${prefix}-${genUID}`;
}
