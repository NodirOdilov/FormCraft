/**
 * Custom hook for listing, viewing, and managing form submissions.
 */
import { useCallback, useEffect, useState } from 'react';
import {
  deleteSubmission,
  exportSubmissions,
  getSubmission,
  listSubmissions,
  markSubmissionSpam,
} from '../api/submissions';
import type { SubmissionDetail, SubmissionSummary } from '../api/submissions';

interface UseSubmissionsOptions {
  formId?: string;
  page?: number;
  pageSize?: number;
}

export function useSubmissions(options: UseSubmissionsOptions = {}) {
  const { formId, page = 1, pageSize = 20 } = options;

  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubmissions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (formId) params.form = formId;

      const { data } = await listSubmissions(params);
      setSubmissions(data.results);
      setTotalCount(data.count);
      setTotalPages(data.total_pages);
    } catch (err: any) {
      setError(err?.response?.data?.errors?.[0]?.message || 'Failed to load submissions');
    } finally {
      setIsLoading(false);
    }
  }, [formId, page, pageSize]);

  useEffect(() => {
    fetchSubmissions();
  }, [fetchSubmissions]);

  const viewSubmission = useCallback(async (submissionId: string): Promise<SubmissionDetail | null> => {
    try {
      const { data } = await getSubmission(submissionId);
      return data;
    } catch {
      return null;
    }
  }, []);

  const removeSubmission = useCallback(
    async (submissionId: string) => {
      await deleteSubmission(submissionId);
      setSubmissions((prev) => prev.filter((s) => s.id !== submissionId));
      setTotalCount((prev) => prev - 1);
    },
    [],
  );

  const flagSpam = useCallback(
    async (submissionId: string) => {
      await markSubmissionSpam(submissionId);
      setSubmissions((prev) =>
        prev.map((s) => (s.id === submissionId ? { ...s, status: 'spam' } : s)),
      );
    },
    [],
  );

  const downloadCsv = useCallback(
    async (targetFormId: string) => {
      const blob = await exportSubmissions(targetFormId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `submissions_${targetFormId}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },
    [],
  );

  return {
    submissions,
    totalCount,
    totalPages,
    isLoading,
    error,
    refetch: fetchSubmissions,
    viewSubmission,
    removeSubmission,
    flagSpam,
    downloadCsv,
  };
}
