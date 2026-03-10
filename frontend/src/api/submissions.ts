/**
 * API functions for submissions and file uploads.
 */
import client from './client';
import { PaginatedResponse } from './forms';

export interface SubmissionAnswer {
  id: string;
  field: string;
  field_label: string;
  field_type: string;
  value: string;
  file_upload: FileUpload | null;
  created_at: string;
}

export interface SubmissionSummary {
  id: string;
  form: string;
  respondent_email: string | null;
  status: string;
  ip_address: string | null;
  duration_seconds: number | null;
  answer_count: number;
  created_at: string;
}

export interface SubmissionDetail {
  id: string;
  form: string;
  form_title: string;
  respondent_email: string | null;
  status: string;
  ip_address: string | null;
  user_agent: string;
  referrer: string;
  duration_seconds: number | null;
  metadata: Record<string, unknown>;
  answers: SubmissionAnswer[];
  created_at: string;
  updated_at: string;
}

export interface FileUpload {
  id: string;
  file: string;
  original_filename: string;
  file_size: number;
  content_type: string;
  created_at: string;
}

export interface SubmissionCreatePayload {
  form_id: string;
  answers: Array<{
    field_id: string;
    value: string;
    file_upload_id?: string;
  }>;
  duration_seconds?: number;
  metadata?: Record<string, unknown>;
}

export function listSubmissions(params?: Record<string, string | number>) {
  return client.get<PaginatedResponse<SubmissionSummary>>('/submissions/', {
    params,
  });
}

export function getSubmission(submissionId: string) {
  return client.get<SubmissionDetail>(`/submissions/${submissionId}/`);
}

export function createSubmission(data: SubmissionCreatePayload) {
  return client.post<SubmissionDetail>('/submissions/', data);
}

export function deleteSubmission(submissionId: string) {
  return client.delete(`/submissions/${submissionId}/`);
}

export function markSubmissionSpam(submissionId: string) {
  return client.post(`/submissions/${submissionId}/mark-spam/`);
}

export function exportSubmissions(formId: string): Promise<Blob> {
  return client
    .get(`/submissions/export/`, {
      params: { form: formId },
      responseType: 'blob',
    })
    .then((res) => res.data);
}

export function uploadFile(formId: string, file: File) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('form_id', formId);
  return client.post<FileUpload>('/submissions/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}
