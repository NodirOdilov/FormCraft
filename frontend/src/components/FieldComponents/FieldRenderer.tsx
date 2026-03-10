/**
 * Dynamic field renderer that maps field_type to the correct input component.
 * Used in the public form view and form preview.
 */
import React from 'react';
import type { FormField } from '../../api/forms';
import { TextInput } from './TextInput';
import { TextAreaInput } from './TextAreaInput';
import { SelectInput } from './SelectInput';
import { RadioInput } from './RadioInput';
import { CheckboxInput } from './CheckboxInput';
import { FileUploadInput } from './FileUploadInput';
import { RatingInput } from './RatingInput';
import { ScaleInput } from './ScaleInput';

interface FieldRendererProps {
  field: FormField;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  primaryColor?: string;
}

export const FieldRenderer: React.FC<FieldRendererProps> = ({
  field,
  value,
  onChange,
  error,
  primaryColor = '#4F46E5',
}) => {
  // Layout elements
  if (field.field_type === 'heading') {
    return (
      <div className="py-2">
        <h3 className="text-xl font-semibold text-gray-900">{field.label}</h3>
        {field.description && (
          <p className="text-sm text-gray-500 mt-1">{field.description}</p>
        )}
      </div>
    );
  }

  if (field.field_type === 'paragraph') {
    return (
      <div className="py-2">
        <p className="text-sm text-gray-600">
          {field.description || field.label}
        </p>
      </div>
    );
  }

  if (field.field_type === 'divider') {
    return <hr className="my-4 border-gray-200" />;
  }

  if (field.field_type === 'hidden') {
    return <input type="hidden" value={field.default_value} />;
  }

  // Wrapper for interactive fields
  return (
    <div className="mb-5">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {field.label}
        {field.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      {field.description && (
        <p className="text-xs text-gray-400 mb-2">{field.description}</p>
      )}

      {renderInput(field, value, onChange, primaryColor)}

      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
};

function renderInput(
  field: FormField,
  value: string,
  onChange: (v: string) => void,
  primaryColor: string,
) {
  switch (field.field_type) {
    case 'text':
    case 'email':
    case 'phone':
    case 'url':
    case 'number':
      return (
        <TextInput
          type={field.field_type === 'number' ? 'number' : 'text'}
          value={value}
          onChange={onChange}
          placeholder={field.placeholder}
          inputMode={
            field.field_type === 'email'
              ? 'email'
              : field.field_type === 'phone'
                ? 'tel'
                : field.field_type === 'url'
                  ? 'url'
                  : field.field_type === 'number'
                    ? 'numeric'
                    : 'text'
          }
        />
      );

    case 'textarea':
      return (
        <TextAreaInput
          value={value}
          onChange={onChange}
          placeholder={field.placeholder}
          rows={(field.config as any)?.rows || 4}
        />
      );

    case 'date':
      return (
        <TextInput type="date" value={value} onChange={onChange} placeholder="" />
      );

    case 'time':
      return (
        <TextInput type="time" value={value} onChange={onChange} placeholder="" />
      );

    case 'select':
    case 'multi_select':
      return (
        <SelectInput
          options={field.options || []}
          value={value}
          onChange={onChange}
          placeholder={field.placeholder || 'Select...'}
          multiple={field.field_type === 'multi_select'}
        />
      );

    case 'radio':
      return (
        <RadioInput
          options={field.options || []}
          value={value}
          onChange={onChange}
          layout={(field.config as any)?.layout || 'vertical'}
          primaryColor={primaryColor}
        />
      );

    case 'checkbox':
      return (
        <CheckboxInput
          options={field.options || []}
          value={value}
          onChange={onChange}
          layout={(field.config as any)?.layout || 'vertical'}
          primaryColor={primaryColor}
        />
      );

    case 'file_upload':
      return (
        <FileUploadInput
          value={value}
          onChange={onChange}
          allowedTypes={(field.config as any)?.allowed_types || ['*']}
          maxSizeMb={(field.config as any)?.max_size_mb || 10}
        />
      );

    case 'rating':
      return (
        <RatingInput
          value={value}
          onChange={onChange}
          maxRating={(field.config as any)?.max_rating || 5}
          primaryColor={primaryColor}
        />
      );

    case 'scale':
      return (
        <ScaleInput
          value={value}
          onChange={onChange}
          min={(field.config as any)?.min || 1}
          max={(field.config as any)?.max || 10}
          minLabel={(field.config as any)?.min_label || ''}
          maxLabel={(field.config as any)?.max_label || ''}
          primaryColor={primaryColor}
        />
      );

    default:
      return (
        <TextInput
          type="text"
          value={value}
          onChange={onChange}
          placeholder={field.placeholder}
        />
      );
  }
}

export default FieldRenderer;
