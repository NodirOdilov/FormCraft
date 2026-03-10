/**
 * Client-side validation utilities for form submissions.
 * Mirrors the server-side validation rules defined in FormField models.
 */
import type { FormField } from '../api/forms';

export interface ValidationResult {
  valid: boolean;
  message: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const URL_REGEX = /^https?:\/\/[^\s/$.?#].\S*$/i;
const PHONE_REGEX = /^\+?[\d\s\-().]{7,20}$/;

export function validateField(field: FormField, value: string): ValidationResult {
  const trimmed = value.trim();

  // Required check
  if (field.required && !trimmed) {
    return { valid: false, message: `${field.label} is required.` };
  }

  // If empty and not required, skip further validation
  if (!trimmed) {
    return { valid: true, message: '' };
  }

  // Type-specific validation
  switch (field.field_type) {
    case 'email':
      if (!EMAIL_REGEX.test(trimmed)) {
        return { valid: false, message: 'Please enter a valid email address.' };
      }
      break;

    case 'url':
      if (!URL_REGEX.test(trimmed)) {
        return { valid: false, message: 'Please enter a valid URL starting with http:// or https://.' };
      }
      break;

    case 'phone':
      if (!PHONE_REGEX.test(trimmed)) {
        return { valid: false, message: 'Please enter a valid phone number.' };
      }
      break;

    case 'number': {
      const num = Number(trimmed);
      if (isNaN(num)) {
        return { valid: false, message: 'Please enter a valid number.' };
      }
      if (field.min_value !== null && num < field.min_value) {
        return { valid: false, message: `Value must be at least ${field.min_value}.` };
      }
      if (field.max_value !== null && num > field.max_value) {
        return { valid: false, message: `Value must be at most ${field.max_value}.` };
      }
      break;
    }

    case 'rating': {
      const rating = Number(trimmed);
      const maxRating = (field.config as any)?.max_rating || 5;
      if (isNaN(rating) || rating < 1 || rating > maxRating) {
        return { valid: false, message: `Rating must be between 1 and ${maxRating}.` };
      }
      break;
    }

    case 'scale': {
      const scaleVal = Number(trimmed);
      const min = (field.config as any)?.min || 1;
      const max = (field.config as any)?.max || 10;
      if (isNaN(scaleVal) || scaleVal < min || scaleVal > max) {
        return { valid: false, message: `Value must be between ${min} and ${max}.` };
      }
      break;
    }
  }

  // Length constraints
  if (field.min_length !== null && trimmed.length < field.min_length) {
    return {
      valid: false,
      message: `Must be at least ${field.min_length} characters.`,
    };
  }
  if (field.max_length !== null && trimmed.length > field.max_length) {
    return {
      valid: false,
      message: `Must be at most ${field.max_length} characters.`,
    };
  }

  // Regex pattern
  if (field.pattern) {
    try {
      const regex = new RegExp(field.pattern);
      if (!regex.test(trimmed)) {
        return { valid: false, message: `Value does not match the required pattern.` };
      }
    } catch {
      // If pattern is invalid regex, skip
    }
  }

  return { valid: true, message: '' };
}

export function validateForm(
  fields: FormField[],
  answers: Record<string, string>,
): Map<string, string> {
  const errors = new Map<string, string>();

  for (const field of fields) {
    // Skip layout elements
    if (['heading', 'paragraph', 'divider'].includes(field.field_type)) {
      continue;
    }
    const value = answers[field.id] || '';
    const result = validateField(field, value);
    if (!result.valid) {
      errors.set(field.id, result.message);
    }
  }

  return errors;
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${units[i]}`;
}

export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  if (minutes < 60) return `${minutes}m ${remaining}s`;
  const hours = Math.floor(minutes / 60);
  const remainingMin = minutes % 60;
  return `${hours}h ${remainingMin}m`;
}
