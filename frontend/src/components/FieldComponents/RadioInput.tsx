import React from 'react';
import type { FieldOption } from '../../api/forms';

interface RadioInputProps {
  options: FieldOption[];
  value: string;
  onChange: (value: string) => void;
  layout?: 'vertical' | 'horizontal';
  primaryColor?: string;
}

export const RadioInput: React.FC<RadioInputProps> = ({
  options,
  value,
  onChange,
  layout = 'vertical',
  primaryColor = '#4F46E5',
}) => {
  return (
    <div
      className={`${
        layout === 'horizontal' ? 'flex flex-wrap gap-4' : 'space-y-2'
      }`}
    >
      {options.map((opt) => {
        const isSelected = value === opt.value;
        return (
          <label
            key={opt.id}
            className={`flex items-center gap-3 cursor-pointer px-3 py-2 rounded-lg border transition-colors ${
              isSelected
                ? 'border-indigo-300 bg-indigo-50'
                : 'border-transparent hover:bg-gray-50'
            }`}
            onClick={() => onChange(opt.value)}
          >
            <span
              className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
                isSelected ? 'border-indigo-600' : 'border-gray-300'
              }`}
              style={isSelected ? { borderColor: primaryColor } : {}}
            >
              {isSelected && (
                <span
                  className="w-2.5 h-2.5 rounded-full"
                  style={{ backgroundColor: primaryColor }}
                />
              )}
            </span>
            <span className="text-sm text-gray-700">{opt.label}</span>
          </label>
        );
      })}
    </div>
  );
};

export default RadioInput;
