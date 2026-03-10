/**
 * Public-facing form page. Renders the form using FieldRenderer components
 * and handles submission to the API.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getPublicForm, type FormDetail } from '../api/forms';
import { createSubmission } from '../api/submissions';
import { recordFormView } from '../api/analytics';
import { FieldRenderer } from '../components/FieldComponents/FieldRenderer';
import { validateForm } from '../utils/validation';

const PublicFormPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [form, setForm] = useState<FormDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [errors, setErrors] = useState<Map<string, string>>(new Map());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [startTime] = useState(() => Date.now());
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    if (!slug) return;
    getPublicForm(slug)
      .then(({ data }) => {
        setForm(data);
        recordFormView(data.id);
        // Set default values
        const defaults: Record<string, string> = {};
        data.fields_data?.forEach((field) => {
          if (field.default_value) {
            defaults[field.id] = field.default_value;
          }
        });
        setAnswers(defaults);
      })
      .catch(() => setLoadError('Form not found or is no longer available.'));
  }, [slug]);

  const handleChange = useCallback((fieldId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [fieldId]: value }));
    setErrors((prev) => {
      const next = new Map(prev);
      next.delete(fieldId);
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!form) return;

      const fieldsToValidate = form.fields_data || [];
      const currentPageFields = form.is_multi_page
        ? fieldsToValidate.filter((f) => f.page === currentPage)
        : fieldsToValidate;

      // If multi-page and not on last page, advance
      const pages = [...new Set(fieldsToValidate.map((f) => f.page))].sort();
      const isLastPage = !form.is_multi_page || currentPage === pages[pages.length - 1];

      const validationErrors = validateForm(currentPageFields, answers);
      if (validationErrors.size > 0) {
        setErrors(validationErrors);
        return;
      }

      if (!isLastPage) {
        setCurrentPage((p) => p + 1);
        return;
      }

      // Submit
      setIsSubmitting(true);
      try {
        const durationSeconds = Math.round((Date.now() - startTime) / 1000);
        await createSubmission({
          form_id: form.id,
          answers: Object.entries(answers)
            .filter(([, v]) => v !== '')
            .map(([fieldId, value]) => ({ field_id: fieldId, value })),
          duration_seconds: durationSeconds,
        });
        setIsSubmitted(true);

        if (form.redirect_url) {
          setTimeout(() => {
            window.location.href = form.redirect_url;
          }, 1500);
        }
      } catch (err: any) {
        const msg =
          err?.response?.data?.errors?.[0]?.message || 'Submission failed.';
        setErrors(new Map([['_form', msg]]));
      } finally {
        setIsSubmitting(false);
      }
    },
    [form, answers, currentPage, startTime],
  );

  if (loadError) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">Form Not Found</h1>
          <p className="text-gray-500">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!form) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (isSubmitted) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: form.background_color }}
      >
        <div className="text-center max-w-md px-6">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
            style={{ backgroundColor: form.primary_color }}
          >
            <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {form.success_message}
          </h2>
        </div>
      </div>
    );
  }

  const allFields = form.fields_data || [];
  const displayFields = form.is_multi_page
    ? allFields.filter((f) => f.page === currentPage)
    : allFields;

  const pages = form.is_multi_page
    ? [...new Set(allFields.map((f) => f.page))].sort()
    : [1];

  return (
    <div
      className="min-h-screen py-8 px-4"
      style={{ backgroundColor: form.background_color }}
    >
      <div className="max-w-xl mx-auto">
        {/* Form header */}
        <div className="mb-8 text-center">
          {form.cover_image && (
            <img
              src={form.cover_image}
              alt=""
              className="w-full h-48 object-cover rounded-lg mb-4"
            />
          )}
          <h1 className="text-3xl font-bold text-gray-900">{form.title}</h1>
          {form.description && (
            <p className="text-gray-500 mt-2">{form.description}</p>
          )}
        </div>

        {/* Form body */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 md:p-8"
        >
          {/* Form-level error */}
          {errors.get('_form') && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {errors.get('_form')}
            </div>
          )}

          {/* Fields */}
          {displayFields.map((field) => (
            <FieldRenderer
              key={field.id}
              field={field}
              value={answers[field.id] || ''}
              onChange={(v) => handleChange(field.id, v)}
              error={errors.get(field.id)}
              primaryColor={form.primary_color}
            />
          ))}

          {/* Page navigation and submit */}
          <div className="flex items-center justify-between mt-6">
            {form.is_multi_page && currentPage > pages[0] && (
              <button
                type="button"
                onClick={() => setCurrentPage((p) => p - 1)}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50"
              >
                Previous
              </button>
            )}
            <div className="ml-auto">
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2.5 text-sm font-medium text-white rounded-lg transition-opacity disabled:opacity-50"
                style={{ backgroundColor: form.primary_color }}
              >
                {isSubmitting
                  ? 'Submitting...'
                  : form.is_multi_page &&
                      currentPage !== pages[pages.length - 1]
                    ? 'Next'
                    : form.submit_button_text}
              </button>
            </div>
          </div>

          {/* Page indicator */}
          {form.is_multi_page && pages.length > 1 && (
            <div className="flex justify-center gap-1.5 mt-4">
              {pages.map((p) => (
                <span
                  key={p}
                  className={`w-2 h-2 rounded-full ${
                    p === currentPage ? 'bg-indigo-600' : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>
          )}
        </form>

        {/* Custom CSS */}
        {form.settings?.custom_css && (
          <style dangerouslySetInnerHTML={{ __html: form.settings.custom_css }} />
        )}
      </div>
    </div>
  );
};

export default PublicFormPage;
