import React from 'react';

interface TextInputProps {
  type?: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  inputMode?: React.HTMLAttributes<HTMLInputElement>['inputMode'];
}

export const TextInput: React.FC<TextInputProps> = ({
  type = 'text',
  value,
  onChange,
  placeholder,
  inputMode,
}) => {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      inputMode={inputMode}
      className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-sm text-gray-900 focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none transition-colors"
    />
  );
};

export default TextInput;
