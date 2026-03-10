import React, { useCallback } from 'react';
import type { FieldOption } from '../../api/forms';

interface SelectInputProps {
  options: FieldOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  multiple?: boolean;
}

export const SelectInput: React.FC<SelectInputProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  multiple = false,
}) => {
  const handleMultiChange = useCallback(
    (e: React.ChangeEvent<HTMLSelectElement>) => {
      if (multiple) {
        const selected = Array.from(e.target.selectedOptions, (opt) => opt.value);
        onChange(selected.join(','));
      } else {
        onChange(e.target.value);
      }
    },
    [multiple, onChange],
  );

  if (multiple) {
    const selectedValues = value ? value.split(',') : [];
    return (
      <select
        multiple
        value={selectedValues}
        onChange={handleMultiChange}
        className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm text-gray-900 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none min-h-[100px]"
      >
        {options.map((opt) => (
          <option key={opt.id} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    );
  }

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm text-gray-900 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none bg-white"
    >
      <option value="">{placeholder}</option>
      {options.map((opt) => (
        <option key={opt.id} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
};

export default SelectInput;
