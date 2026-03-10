/**
 * API functions for analytics: views, overview, field dropoff.
 */
import client from './client';

export interface FormOverview {
  total_views: number;
  unique_views: number;
  total_submissions: number;
  completion_rate: number;
  avg_duration_seconds: number;
  views_trend: Array<{ date: string; count: number }>;
  submissions_trend: Array<{ date: string; count: number }>;
  device_breakdown: { desktop: number; mobile: number; tablet: number };
  top_referrers: Array<{ referrer: string; count: number }>;
  top_countries: Array<{ country: string; count: number }>;
}

export interface FieldDropoff {
  field__id: string;
  field__label: string;
  field__order: number;
  total_dropoffs: number;
}

export function recordFormView(formId: string, referrer?: string) {
  return client.post('/analytics/view/', {
    form_id: formId,
    referrer: referrer || document.referrer,
  });
}

export function getFormOverview(formId: string, days: number = 30) {
  return client.get<FormOverview>(`/analytics/${formId}/overview/`, {
    params: { days },
  });
}

export function getFieldDropoff(formId: string, days: number = 30) {
  return client.get<FieldDropoff[]>(`/analytics/${formId}/dropoff/`, {
    params: { days },
  });
}
