export interface PeriodValue {
  period: string;
  value: number;
}

export interface AlignedSeries {
  labels: string[];
  data: (number | null)[][];
}

// Merges multiple {period, value}[] series onto a shared, sorted label axis,
// filling gaps with null so Chart.js breaks the line instead of misaligning points.
export function alignByPeriod(series: PeriodValue[][]): AlignedSeries {
  const periods = new Set<string>();
  series.forEach((points) => points.forEach((p) => periods.add(p.period)));
  const labels = Array.from(periods).sort();

  const data = series.map((points) => {
    const byPeriod = new Map(points.map((p) => [p.period, p.value]));
    return labels.map((label) => byPeriod.get(label) ?? null);
  });

  return { labels, data };
}
