import React, { useCallback } from 'react';
import type { FieldOption } from '../../api/forms';

interface CheckboxInputProps {
  options: FieldOption[];
  value: string;
  onChange: (value: string) => void;
  layout?: 'vertical' | 'horizontal';
  primaryColor?: string;
}

export const CheckboxInput: React.FC<CheckboxInputProps> = ({
  options,
  value,
  onChange,
  layout = 'vertical',
  primaryColor = '#4F46E5',
}) => {
  const selectedValues = value ? value.split(',').filter(Boolean) : [];

  const toggleValue = useCallback(
    (optValue: string) => {
      let updated: string[];
      if (selectedValues.includes(optValue)) {
        updated = selectedValues.filter((v) => v !== optValue);
      } else {
        updated = [...selectedValues, optValue];
      }
      onChange(updated.join(','));
    },
    [selectedValues, onChange],
  );

  return (
    <div
      className={`${
        layout === 'horizontal' ? 'flex flex-wrap gap-4' : 'space-y-2'
      }`}
    >
      {options.map((opt) => {
        const isChecked = selectedValues.includes(opt.value);
        return (
          <label
            key={opt.id}
            className={`flex items-center gap-3 cursor-pointer px-3 py-2 rounded-lg border transition-colors ${
              isChecked
                ? 'border-indigo-300 bg-indigo-50'
                : 'border-transparent hover:bg-gray-50'
            }`}
            onClick={() => toggleValue(opt.value)}
          >
            <span
              className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                isChecked ? 'border-indigo-600 bg-indigo-600' : 'border-gray-300'
              }`}
              style={
                isChecked
                  ? { borderColor: primaryColor, backgroundColor: primaryColor }
                  : {}
              }
            >
              {isChecked && (
                <svg
                  className="w-3 h-3 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={3}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              )}
            </span>
            <span className="text-sm text-gray-700">{opt.label}</span>
          </label>
        );
      })}
    </div>
  );
};

export default CheckboxInput;
