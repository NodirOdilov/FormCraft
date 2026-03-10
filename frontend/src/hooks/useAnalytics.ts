/**
 * Custom hook for fetching and managing form analytics data.
 */
import { useCallback, useEffect, useState } from 'react';
import { getFieldDropoff, getFormOverview } from '../api/analytics';
import type { FieldDropoff, FormOverview } from '../api/analytics';

export function useAnalytics(formId: string, days: number = 30) {
  const [overview, setOverview] = useState<FormOverview | null>(null);
  const [dropoffs, setDropoffs] = useState<FieldDropoff[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOverview = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await getFormOverview(formId, days);
      setOverview(data);
    } catch (err: any) {
      setError(err?.response?.data?.error || 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  }, [formId, days]);

  const fetchDropoffs = useCallback(async () => {
    try {
      const { data } = await getFieldDropoff(formId, days);
      setDropoffs(data);
    } catch {
      // Silently fail on dropoff data -- it's supplementary
    }
  }, [formId, days]);

  useEffect(() => {
    if (formId) {
      fetchOverview();
      fetchDropoffs();
    }
  }, [formId, days, fetchOverview, fetchDropoffs]);

  return {
    overview,
    dropoffs,
    isLoading,
    error,
    refetch: () => {
      fetchOverview();
      fetchDropoffs();
    },
  };
}
