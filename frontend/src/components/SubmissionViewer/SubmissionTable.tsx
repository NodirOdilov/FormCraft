/**
 * Table view of form submissions with sorting, spam marking, and CSV export.
 */
import React, { useCallback, useState } from 'react';
import { useSubmissions } from '../../hooks/useSubmissions';
import { formatDuration } from '../../utils/validation';
import { SubmissionDetailModal } from './SubmissionDetailModal';
import type { SubmissionDetail } from '../../api/submissions';

interface SubmissionTableProps {
  formId: string;
}

export const SubmissionTable: React.FC<SubmissionTableProps> = ({ formId }) => {
  const [page, setPage] = useState(1);
  const [selectedSubmission, setSelectedSubmission] =
    useState<SubmissionDetail | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const {
    submissions,
    totalCount,
    totalPages,
    isLoading,
    error,
    refetch,
    viewSubmission,
    removeSubmission,
    flagSpam,
    downloadCsv,
  } = useSubmissions({ formId, page });

  const handleView = useCallback(
    async (submissionId: string) => {
      const detail = await viewSubmission(submissionId);
      if (detail) {
        setSelectedSubmission(detail);
        setIsModalOpen(true);
      }
    },
    [viewSubmission],
  );

  const handleDelete = useCallback(
    async (submissionId: string) => {
      if (window.confirm('Are you sure you want to delete this submission?')) {
        await removeSubmission(submissionId);
      }
    },
    [removeSubmission],
  );

  const handleSpam = useCallback(
    async (submissionId: string) => {
      await flagSpam(submissionId);
    },
    [flagSpam],
  );

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        <p>{error}</p>
        <button
          onClick={refetch}
          className="mt-2 text-sm text-indigo-600 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Submissions{' '}
          <span className="text-gray-400 font-normal">({totalCount})</span>
        </h2>
        <button
          onClick={() => downloadCsv(formId)}
          className="px-4 py-2 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-gray-700"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Respondent
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Status
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Answers
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Duration
              </th>
              <th className="text-left px-4 py-3 font-medium text-gray-600">
                Submitted
              </th>
              <th className="text-right px-4 py-3 font-medium text-gray-600">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  Loading...
                </td>
              </tr>
            )}
            {!isLoading && submissions.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-400">
                  No submissions yet.
                </td>
              </tr>
            )}
            {submissions.map((sub) => (
              <tr
                key={sub.id}
                className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
                onClick={() => handleView(sub.id)}
              >
                <td className="px-4 py-3 text-gray-700">
                  {sub.respondent_email || (
                    <span className="text-gray-400">Anonymous</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                      sub.status === 'complete'
                        ? 'bg-green-100 text-green-700'
                        : sub.status === 'spam'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {sub.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{sub.answer_count}</td>
                <td className="px-4 py-3 text-gray-600">
                  {sub.duration_seconds
                    ? formatDuration(sub.duration_seconds)
                    : '-'}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs">
                  {new Date(sub.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSpam(sub.id);
                    }}
                    className="text-xs text-gray-400 hover:text-orange-500 mr-2"
                    title="Mark as spam"
                  >
                    Spam
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(sub.id);
                    }}
                    className="text-xs text-gray-400 hover:text-red-500"
                    title="Delete"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Detail modal */}
      {isModalOpen && selectedSubmission && (
        <SubmissionDetailModal
          submission={selectedSubmission}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedSubmission(null);
          }}
        />
      )}
    </div>
  );
};

export default SubmissionTable;
