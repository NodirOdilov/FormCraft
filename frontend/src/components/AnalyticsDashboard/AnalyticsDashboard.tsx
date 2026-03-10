/**
 * Analytics dashboard for a form: KPI cards, trends chart, device breakdown,
 * top referrers, and field dropoff report.
 */
import React, { useState } from 'react';
import { useAnalytics } from '../../hooks/useAnalytics';
import { formatDuration } from '../../utils/validation';

interface AnalyticsDashboardProps {
  formId: string;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  formId,
}) => {
  const [days, setDays] = useState(30);
  const { overview, dropoffs, isLoading, error } = useAnalytics(formId, days);

  if (isLoading && !overview) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  if (!overview) return null;

  const maxTrendCount = Math.max(
    ...overview.views_trend.map((t) => t.count),
    ...overview.submissions_trend.map((t) => t.count),
    1,
  );

  return (
    <div className="space-y-8">
      {/* Period selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Analytics</h2>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded-md ${
                days === d
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <KpiCard
          label="Total Views"
          value={overview.total_views.toLocaleString()}
        />
        <KpiCard
          label="Unique Views"
          value={overview.unique_views.toLocaleString()}
        />
        <KpiCard
          label="Submissions"
          value={overview.total_submissions.toLocaleString()}
        />
        <KpiCard
          label="Completion Rate"
          value={`${overview.completion_rate}%`}
        />
        <KpiCard
          label="Avg Duration"
          value={formatDuration(Math.round(overview.avg_duration_seconds))}
        />
      </div>

      {/* Trend visualization using CSS bars */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          Views & Submissions Trend
        </h3>
        <div className="flex items-end gap-1 h-40">
          {overview.views_trend.map((point, i) => {
            const subPoint = overview.submissions_trend[i];
            const viewHeight = (point.count / maxTrendCount) * 100;
            const subHeight = subPoint
              ? (subPoint.count / maxTrendCount) * 100
              : 0;

            return (
              <div
                key={point.date}
                className="flex-1 flex flex-col items-center gap-0.5"
                title={`${point.date}: ${point.count} views, ${subPoint?.count || 0} submissions`}
              >
                <div className="w-full flex flex-col items-center justify-end h-32">
                  <div
                    className="w-full bg-indigo-200 rounded-t"
                    style={{ height: `${viewHeight}%`, minHeight: point.count > 0 ? '2px' : 0 }}
                  />
                  <div
                    className="w-full bg-indigo-600 rounded-t -mt-px"
                    style={{ height: `${subHeight}%`, minHeight: subPoint?.count > 0 ? '2px' : 0 }}
                  />
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex gap-4 mt-3 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-indigo-200 rounded" /> Views
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-indigo-600 rounded" /> Submissions
          </span>
        </div>
      </div>

      {/* Device breakdown and Top referrers */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Device breakdown */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Device Breakdown
          </h3>
          <div className="space-y-3">
            <DeviceBar
              label="Desktop"
              count={overview.device_breakdown.desktop}
              total={overview.total_views}
              color="#4F46E5"
            />
            <DeviceBar
              label="Mobile"
              count={overview.device_breakdown.mobile}
              total={overview.total_views}
              color="#7C3AED"
            />
            <DeviceBar
              label="Tablet"
              count={overview.device_breakdown.tablet}
              total={overview.total_views}
              color="#A78BFA"
            />
          </div>
        </div>

        {/* Top referrers */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Top Referrers
          </h3>
          {overview.top_referrers.length === 0 ? (
            <p className="text-sm text-gray-400">No referrer data yet.</p>
          ) : (
            <div className="space-y-2">
              {overview.top_referrers.map((ref, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 truncate max-w-[200px]">
                    {ref.referrer}
                  </span>
                  <span className="text-gray-400 font-medium">
                    {ref.count}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Field dropoff */}
      {dropoffs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">
            Field Dropoff
          </h3>
          <p className="text-xs text-gray-400 mb-3">
            Fields where users stop filling out the form.
          </p>
          <div className="space-y-2">
            {dropoffs.map((d) => {
              const maxDropoff = Math.max(
                ...dropoffs.map((dd) => dd.total_dropoffs),
                1,
              );
              const pct = (d.total_dropoffs / maxDropoff) * 100;
              return (
                <div key={d.field__id} className="flex items-center gap-3">
                  <span className="text-sm text-gray-700 w-40 truncate">
                    {d.field__label}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div
                      className="bg-red-400 h-2 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 w-10 text-right">
                    {d.total_dropoffs}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

const KpiCard: React.FC<{ label: string; value: string }> = ({
  label,
  value,
}) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4">
    <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
    <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
  </div>
);

const DeviceBar: React.FC<{
  label: string;
  count: number;
  total: number;
  color: string;
}> = ({ label, count, total, color }) => {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="text-gray-400">
          {count.toLocaleString()} ({pct}%)
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
