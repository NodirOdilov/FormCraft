/**
 * API functions for form CRUD, fields, and settings.
 */
import client from './client';

export interface FormField {
  id: string;
  form: string;
  field_type: string;
  label: string;
  description: string;
  placeholder: string;
  required: boolean;
  order: number;
  page: number;
  min_length: number | null;
  max_length: number | null;
  min_value: number | null;
  max_value: number | null;
  pattern: string;
  config: Record<string, unknown>;
  default_value: string;
  options: FieldOption[];
  conditional_rules: ConditionalRule[];
}

export interface FieldOption {
  id: string;
  label: string;
  value: string;
  order: number;
  is_default: boolean;
}

export interface ConditionalRule {
  id: string;
  field: string;
  action: 'show' | 'hide' | 'skip_to';
  source_field: string;
  operator: string;
  value: string;
  target_field: string | null;
}

export interface FormSettings {
  id: string;
  notification_emails: string;
  send_confirmation_email: boolean;
  confirmation_email_subject: string;
  confirmation_email_body: string;
  custom_css: string;
  custom_js: string;
  meta_title: string;
  meta_description: string;
  google_analytics_id: string;
  facebook_pixel_id: string;
  embed_allowed_domains: string;
}

export interface FormSummary {
  id: string;
  title: string;
  slug: string;
  status: string;
  submission_count: number;
  is_accepting_responses: boolean;
  field_count: number;
  created_at: string;
  updated_at: string;
}

export interface FormDetail {
  id: string;
  workspace: string | null;
  created_by_email: string;
  title: string;
  slug: string;
  description: string;
  status: string;
  cover_image: string | null;
  primary_color: string;
  background_color: string;
  submit_button_text: string;
  success_message: string;
  redirect_url: string;
  is_multi_page: boolean;
  allow_multiple_submissions: boolean;
  requires_login: boolean;
  closes_at: string | null;
  max_submissions: number | null;
  submission_count: number;
  is_accepting_responses: boolean;
  fields_data: FormField[];
  settings: FormSettings;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// --- Forms ---

export function listForms(params?: Record<string, string | number>) {
  return client.get<PaginatedResponse<FormSummary>>('/forms/', { params });
}

export function getForm(formId: string) {
  return client.get<FormDetail>(`/forms/${formId}/`);
}

export function createForm(data: {
  title: string;
  description?: string;
  workspace?: string;
}) {
  return client.post<FormDetail>('/forms/', data);
}

export function updateForm(formId: string, data: Partial<FormDetail>) {
  return client.patch<FormDetail>(`/forms/${formId}/`, data);
}

export function deleteForm(formId: string) {
  return client.delete(`/forms/${formId}/`);
}

export function publishForm(formId: string) {
  return client.post(`/forms/${formId}/publish/`);
}

export function closeForm(formId: string) {
  return client.post(`/forms/${formId}/close/`);
}

export function duplicateForm(formId: string) {
  return client.post<FormDetail>(`/forms/${formId}/duplicate/`);
}

export function getEmbedCode(formId: string) {
  return client.get<{ iframe: string; script: string; link: string }>(
    `/forms/${formId}/embed-code/`,
  );
}

export function getPublicForm(slug: string) {
  return client.get<FormDetail>(`/forms/by-slug/${slug}/`);
}

// --- Fields ---

export function listFields(formId: string) {
  return client.get<FormField[]>(`/forms/${formId}/fields/`);
}

export function createField(formId: string, data: Partial<FormField>) {
  return client.post<FormField>(`/forms/${formId}/fields/`, data);
}

export function updateField(formId: string, fieldId: string, data: Partial<FormField>) {
  return client.patch<FormField>(`/forms/${formId}/fields/${fieldId}/`, data);
}

export function deleteField(formId: string, fieldId: string) {
  return client.delete(`/forms/${formId}/fields/${fieldId}/`);
}

export function reorderFields(
  formId: string,
  fields: Array<{ id: string; order: number; page?: number }>,
) {
  return client.post(`/forms/${formId}/reorder-fields/`, { fields });
}

// --- Settings ---

export function getFormSettings(formId: string) {
  return client.get<FormSettings>(`/forms/${formId}/settings/`);
}

export function updateFormSettings(formId: string, data: Partial<FormSettings>) {
  return client.put<FormSettings>(`/forms/${formId}/settings/`, data);
}
