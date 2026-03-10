/**
 * Dashboard page showing a list of all user's forms with create/delete actions.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  createForm,
  deleteForm,
  listForms,
  type FormSummary,
  type PaginatedResponse,
} from '../api/forms';
import { useAuthStore } from '../store/authStore';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const fetchForms = useCallback(async () => {
    setIsLoading(true);
    try {
      const params: Record<string, string | number> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const { data } = await listForms(params);
      setForms(data.results);
    } catch (err) {
      console.error('Failed to load forms:', err);
    } finally {
      setIsLoading(false);
    }
  }, [search, statusFilter]);

  useEffect(() => {
    fetchForms();
  }, [fetchForms]);

  const handleCreate = useCallback(async () => {
    try {
      const { data } = await createForm({ title: 'Untitled Form' });
      navigate(`/builder/${data.id}`);
    } catch (err) {
      console.error('Failed to create form:', err);
    }
  }, [navigate]);

  const handleDelete = useCallback(
    async (formId: string, e: React.MouseEvent) => {
      e.stopPropagation();
      if (!window.confirm('Delete this form and all its submissions?')) return;
      try {
        await deleteForm(formId);
        setForms((prev) => prev.filter((f) => f.id !== formId));
      } catch (err) {
        console.error('Failed to delete form:', err);
      }
    },
    [],
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">FormCraft</h1>
            <p className="text-sm text-gray-500">
              Welcome back, {user?.full_name || user?.email}
            </p>
          </div>
          <button
            onClick={handleCreate}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
          >
            + New Form
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <input
            type="text"
            placeholder="Search forms..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64 border border-gray-300 rounded-lg px-4 py-2 text-sm outline-none focus:border-indigo-400"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm outline-none bg-white"
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="closed">Closed</option>
            <option value="archived">Archived</option>
          </select>
        </div>

        {/* Form cards */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
          </div>
        ) : forms.length === 0 ? (
          <div className="text-center py-20">
            <h3 className="text-lg font-medium text-gray-700 mb-2">
              No forms yet
            </h3>
            <p className="text-gray-400 mb-4">
              Create your first form to get started.
            </p>
            <button
              onClick={handleCreate}
              className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
            >
              Create Form
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {forms.map((form) => (
              <div
                key={form.id}
                onClick={() => navigate(`/builder/${form.id}`)}
                className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-md transition-shadow cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-semibold text-gray-900 truncate pr-2">
                    {form.title}
                  </h3>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${
                      form.status === 'published'
                        ? 'bg-green-100 text-green-700'
                        : form.status === 'draft'
                          ? 'bg-yellow-100 text-yellow-700'
                          : form.status === 'closed'
                            ? 'bg-gray-100 text-gray-600'
                            : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    {form.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <span>{form.field_count} fields</span>
                  <span>{form.submission_count} submissions</span>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <span className="text-xs text-gray-400">
                    Updated {new Date(form.updated_at).toLocaleDateString()}
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/forms/${form.id}/submissions`);
                      }}
                      className="text-xs text-indigo-600 hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Submissions
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/forms/${form.id}/analytics`);
                      }}
                      className="text-xs text-indigo-600 hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Analytics
                    </button>
                    <button
                      onClick={(e) => handleDelete(form.id, e)}
                      className="text-xs text-red-500 hover:underline opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
