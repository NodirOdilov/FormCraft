/**
 * Modal showing the full detail of a single submission with all answers.
 */
import React from 'react';
import type { SubmissionDetail } from '../../api/submissions';
import { formatDuration, formatFileSize } from '../../utils/validation';

interface SubmissionDetailModalProps {
  submission: SubmissionDetail;
  onClose: () => void;
}

export const SubmissionDetailModal: React.FC<SubmissionDetailModalProps> = ({
  submission,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-40"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Submission Detail
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">
              {submission.form_title}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="overflow-y-auto px-6 py-4" style={{ maxHeight: '60vh' }}>
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-lg text-sm">
            <div>
              <span className="text-gray-400">Respondent</span>
              <p className="font-medium text-gray-700">
                {submission.respondent_email || 'Anonymous'}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Status</span>
              <p className="font-medium">
                <span
                  className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${
                    submission.status === 'complete'
                      ? 'bg-green-100 text-green-700'
                      : submission.status === 'spam'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-yellow-100 text-yellow-700'
                  }`}
                >
                  {submission.status}
                </span>
              </p>
            </div>
            <div>
              <span className="text-gray-400">Submitted</span>
              <p className="font-medium text-gray-700">
                {new Date(submission.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Duration</span>
              <p className="font-medium text-gray-700">
                {submission.duration_seconds
                  ? formatDuration(submission.duration_seconds)
                  : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-400">IP Address</span>
              <p className="font-medium text-gray-700">
                {submission.ip_address || 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-400">Referrer</span>
              <p className="font-medium text-gray-700 truncate">
                {submission.referrer || 'Direct'}
              </p>
            </div>
          </div>

          {/* Answers */}
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Answers</h4>
          <div className="space-y-4">
            {submission.answers.map((answer) => (
              <div
                key={answer.id}
                className="border border-gray-100 rounded-lg p-4"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-gray-400 uppercase">
                    {answer.field_type}
                  </span>
                  <h5 className="text-sm font-medium text-gray-700">
                    {answer.field_label}
                  </h5>
                </div>

                {answer.file_upload ? (
                  <div className="mt-1">
                    <a
                      href={answer.file_upload.file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-indigo-600 hover:underline"
                    >
                      {answer.file_upload.original_filename}
                    </a>
                    <span className="text-xs text-gray-400 ml-2">
                      ({formatFileSize(answer.file_upload.file_size)})
                    </span>
                  </div>
                ) : (
                  <p className="text-sm text-gray-800 mt-1 whitespace-pre-wrap">
                    {answer.value || (
                      <span className="text-gray-400 italic">No answer</span>
                    )}
                  </p>
                )}
              </div>
            ))}
          </div>

          {submission.answers.length === 0 && (
            <p className="text-sm text-gray-400 text-center py-8">
              No answers recorded.
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-3 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubmissionDetailModal;
