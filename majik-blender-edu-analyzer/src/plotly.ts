// eslint-disable-next-line @typescript-eslint/no-explicit-any
export interface PlotlyTrace<TX = any, TY = any> {
  x?: TX[];
  y?: TY[];

  type: "scatter" | "bar" | "pie" | "waterfall";
  mode?: "lines" | "markers" | "lines+markers";
  name?: string;

  line?: {
    shape?: "linear" | "spline";
    smoothing?: number;
    width?: number;
    dash?: "solid" | "dot" | "dash";
  };

  marker?: {
    size?: number;
    color?: string | string[];
  };

  hovertemplate?: string;

  // Pie-specific
  labels?: string[];
  values?: number[];
}

export type TimeSeriesTrace = PlotlyTrace<string, number>;
export type CurrencySeriesTrace = PlotlyTrace<string, number>;

export interface PieChartTrace {
  type: "scatter" | "bar" | "pie" | "waterfall";
  mode?: "lines" | "markers" | "lines+markers";
  name?: string;

  line?: {
    shape?: "linear" | "spline";
    smoothing?: number;
    width?: number;
    dash?: "solid" | "dot" | "dash";
  };

  marker?: {
    size?: number;
    color?: string | string[];
  };

  hovertemplate?: string;

  // Pie-specific
  labels?: string[];
  values?: number[];
}

export interface BarChartTrace {
  type: "bar"; // always "bar" for bar charts
  name: string; // legend name
  x: (string | number)[]; // x-axis labels (e.g., months)
  y: number[]; // y-axis values
  marker?: {
    color?: string | string[]; // optional bar color
    line?: {
      color?: string;
      width?: number;
    };
  };
  text?: string[]; // optional labels on bars
  hovertemplate?: string; // optional hover format
  orientation?: "v" | "h"; // vertical or horizontal bars (default "v")
}

