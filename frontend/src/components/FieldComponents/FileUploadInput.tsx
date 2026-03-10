import React, { useCallback, useRef, useState } from 'react';
import { formatFileSize } from '../../utils/validation';

interface FileUploadInputProps {
  value: string;
  onChange: (value: string) => void;
  allowedTypes?: string[];
  maxSizeMb?: number;
}

export const FileUploadInput: React.FC<FileUploadInputProps> = ({
  value,
  onChange,
  allowedTypes = ['*'],
  maxSizeMb = 10,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string>(value || '');
  const [error, setError] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = useCallback(
    (file: File) => {
      setError('');

      // Check size
      if (file.size > maxSizeMb * 1024 * 1024) {
        setError(`File exceeds ${maxSizeMb}MB limit.`);
        return;
      }

      // Check type
      if (!allowedTypes.includes('*')) {
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        const mimeMatch = allowedTypes.some(
          (t) => file.type.includes(t) || t === `.${ext}`,
        );
        if (!mimeMatch) {
          setError(`File type not allowed. Accepted: ${allowedTypes.join(', ')}`);
          return;
        }
      }

      setFileName(file.name);
      // In a real implementation, this would trigger the upload API
      // and set the file_upload_id. For now, we store the filename.
      onChange(file.name);
    },
    [allowedTypes, maxSizeMb, onChange],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  return (
    <div>
      <div
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          isDragOver
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleInputChange}
          className="hidden"
          accept={
            allowedTypes.includes('*')
              ? undefined
              : allowedTypes.join(',')
          }
        />
        {fileName ? (
          <div className="text-sm text-gray-700">
            <span className="font-medium">{fileName}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setFileName('');
                onChange('');
              }}
              className="ml-2 text-red-500 hover:text-red-700 text-xs"
            >
              Remove
            </button>
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-500 mb-1">
              Click to upload or drag and drop
            </p>
            <p className="text-xs text-gray-400">
              Max {maxSizeMb}MB
              {!allowedTypes.includes('*') &&
                ` | ${allowedTypes.join(', ')}`}
            </p>
          </div>
        )}
      </div>
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
};

export default FileUploadInput;
