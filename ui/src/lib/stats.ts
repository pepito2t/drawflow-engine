import { plural } from "../i18n";
import { t } from "../i18n/settings";
import { z } from "zod";
import { parseJsonOrNull } from "./json";

const MINUTES_PER_HOUR = 60;
const HOURS_PER_DAY = 8;

const featureStatsSchema = z.object({
  module: z.string(),
  module_name: z.string(),
  runs: z.number().int().nonnegative(),
  files: z.number().int().nonnegative(),
  minutes_saved: z.number().int().nonnegative(),
});

const usageStatsSchema = z.object({
  since: z.string().nullable(),
  features: z.array(featureStatsSchema),
});

export type FeatureStats = z.infer<typeof featureStatsSchema>;
export type UsageStats = z.infer<typeof usageStatsSchema>;

export class StatsError extends Error {
  override name = "StatsError";
}

export function parseUsageStats(rawJson: string): UsageStats {
  const parsed = usageStatsSchema.safeParse(parseJsonOrNull(rawJson));
  if (!parsed.success) {
    throw new StatsError(t("stats.invalid"));
  }
  return parsed.data;
}

export function totalsOf(stats: UsageStats): FeatureStats {
  return stats.features.reduce(
    (total, feature) => ({
      ...total,
      runs: total.runs + feature.runs,
      files: total.files + feature.files,
      minutes_saved: total.minutes_saved + feature.minutes_saved,
    }),
    { module: "total", module_name: "Total", runs: 0, files: 0, minutes_saved: 0 },
  );
}

/** Working days of eight hours, then hours, then minutes: what a draftsman can picture. */
export function formatSavedTime(minutes: number): string {
  if (minutes < MINUTES_PER_HOUR) {
    return t("stats.minutes", { count: minutes });
  }
  const hours = Math.round(minutes / MINUTES_PER_HOUR);
  if (hours < HOURS_PER_DAY) {
    return t("stats.hours", { count: hours });
  }
  const days = Math.floor(hours / HOURS_PER_DAY);
  const remaining = hours % HOURS_PER_DAY;
  const dayPart = plural(days, t("stats.day.one"), t("stats.day.other"));
  return remaining === 0 ? dayPart : `${dayPart} ${t("stats.hours", { count: remaining })}`;
}
