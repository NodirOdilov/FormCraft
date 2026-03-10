/**
 * Right-side panel for editing a selected field's properties:
 * label, placeholder, required, validation, options, etc.
 */
import React, { useCallback, useState } from 'react';
import type { FormField, FieldOption } from '../../api/forms';
import { getFieldTypeMeta } from '../../utils/fieldTypes';

interface FieldPropertiesPanelProps {
  field: FormField;
  onUpdate: (updates: Partial<FormField>) => void;
  onClose: () => void;
}

export const FieldPropertiesPanel: React.FC<FieldPropertiesPanelProps> = ({
  field,
  onUpdate,
  onClose,
}) => {
  const meta = getFieldTypeMeta(field.field_type);
  const [localOptions, setLocalOptions] = useState<FieldOption[]>(
    field.options || [],
  );

  const handleChange = useCallback(
    (key: keyof FormField, value: unknown) => {
      onUpdate({ [key]: value } as Partial<FormField>);
    },
    [onUpdate],
  );

  const handleOptionChange = useCallback(
    (index: number, key: keyof FieldOption, value: string) => {
      const updated = [...localOptions];
      updated[index] = { ...updated[index], [key]: value };
      setLocalOptions(updated);
      onUpdate({ options: updated });
    },
    [localOptions, onUpdate],
  );

  const addOption = useCallback(() => {
    const newOpt: FieldOption = {
      id: `temp-${Date.now()}`,
      label: `Option ${localOptions.length + 1}`,
      value: `option_${localOptions.length + 1}`,
      order: localOptions.length,
      is_default: false,
    };
    const updated = [...localOptions, newOpt];
    setLocalOptions(updated);
    onUpdate({ options: updated });
  }, [localOptions, onUpdate]);

  const removeOption = useCallback(
    (index: number) => {
      const updated = localOptions.filter((_, i) => i !== index);
      setLocalOptions(updated);
      onUpdate({ options: updated });
    },
    [localOptions, onUpdate],
  );

  return (
    <div className="p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-gray-900">
          Field Properties
        </h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 text-lg"
        >
          &times;
        </button>
      </div>

      <div className="space-y-5">
        {/* Field type badge */}
        <div className="text-xs text-indigo-600 bg-indigo-50 px-2 py-1 rounded inline-block">
          {meta?.label || field.field_type}
        </div>

        {/* Label */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Label
          </label>
          <input
            type="text"
            value={field.label}
            onChange={(e) => handleChange('label', e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Description
          </label>
          <textarea
            value={field.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={2}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
            placeholder="Help text shown below the field"
          />
        </div>

        {/* Placeholder */}
        {!['heading', 'paragraph', 'divider', 'hidden', 'rating', 'scale'].includes(field.field_type) && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Placeholder
            </label>
            <input
              type="text"
              value={field.placeholder}
              onChange={(e) => handleChange('placeholder', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
            />
          </div>
        )}

        {/* Required toggle */}
        {!['heading', 'paragraph', 'divider'].includes(field.field_type) && (
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-gray-600">Required</label>
            <button
              onClick={() => handleChange('required', !field.required)}
              className={`relative w-10 h-5 rounded-full transition-colors ${
                field.required ? 'bg-indigo-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                  field.required ? 'translate-x-5' : ''
                }`}
              />
            </button>
          </div>
        )}

        {/* Default value */}
        {field.field_type === 'hidden' && (
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Default Value
            </label>
            <input
              type="text"
              value={field.default_value}
              onChange={(e) => handleChange('default_value', e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
            />
          </div>
        )}

        {/* Validation constraints */}
        {meta?.hasValidation && (
          <div className="border-t border-gray-100 pt-4">
            <h4 className="text-xs font-semibold text-gray-600 mb-3">
              Validation
            </h4>
            <div className="grid grid-cols-2 gap-3">
              {['text', 'textarea', 'email', 'phone', 'url'].includes(field.field_type) && (
                <>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Min length
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={field.min_length ?? ''}
                      onChange={(e) =>
                        handleChange(
                          'min_length',
                          e.target.value ? Number(e.target.value) : null,
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Max length
                    </label>
                    <input
                      type="number"
                      min={0}
                      value={field.max_length ?? ''}
                      onChange={(e) =>
                        handleChange(
                          'max_length',
                          e.target.value ? Number(e.target.value) : null,
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm outline-none"
                    />
                  </div>
                </>
              )}
              {field.field_type === 'number' && (
                <>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Min value
                    </label>
                    <input
                      type="number"
                      value={field.min_value ?? ''}
                      onChange={(e) =>
                        handleChange(
                          'min_value',
                          e.target.value ? Number(e.target.value) : null,
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">
                      Max value
                    </label>
                    <input
                      type="number"
                      value={field.max_value ?? ''}
                      onChange={(e) =>
                        handleChange(
                          'max_value',
                          e.target.value ? Number(e.target.value) : null,
                        )
                      }
                      className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm outline-none"
                    />
                  </div>
                </>
              )}
            </div>
            <div className="mt-3">
              <label className="block text-xs text-gray-500 mb-1">
                Regex pattern
              </label>
              <input
                type="text"
                value={field.pattern}
                onChange={(e) => handleChange('pattern', e.target.value)}
                placeholder="e.g. ^[A-Z].*"
                className="w-full border border-gray-300 rounded-md px-2 py-1.5 text-sm outline-none font-mono"
              />
            </div>
          </div>
        )}

        {/* Options editor for choice fields */}
        {meta?.hasOptions && (
          <div className="border-t border-gray-100 pt-4">
            <h4 className="text-xs font-semibold text-gray-600 mb-3">
              Options
            </h4>
            <div className="space-y-2">
              {localOptions.map((opt, idx) => (
                <div key={opt.id} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={opt.label}
                    onChange={(e) =>
                      handleOptionChange(idx, 'label', e.target.value)
                    }
                    className="flex-1 border border-gray-300 rounded px-2 py-1.5 text-sm outline-none"
                    placeholder="Option label"
                  />
                  <button
                    onClick={() => removeOption(idx)}
                    className="text-gray-400 hover:text-red-500 text-sm px-1"
                  >
                    &times;
                  </button>
                </div>
              ))}
            </div>
            <button
              onClick={addOption}
              className="mt-2 text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              + Add option
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default FieldPropertiesPanel;
