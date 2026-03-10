/**
 * Main drag-and-drop form builder component.
 * Three-column layout: field palette | form canvas | field properties panel.
 */
import React, { useCallback } from 'react';
import { useFormBuilder } from '../../hooks/useFormBuilder';
import { FIELD_TYPES, type FieldTypeMeta } from '../../utils/fieldTypes';
import { FieldPalette } from './FieldPalette';
import { BuilderCanvas } from './BuilderCanvas';
import { FieldPropertiesPanel } from './FieldPropertiesPanel';

interface FormBuilderProps {
  formId: string;
}

export const FormBuilder: React.FC<FormBuilderProps> = ({ formId }) => {
  const builder = useFormBuilder(formId);

  const handleAddField = useCallback(
    (meta: FieldTypeMeta) => {
      builder.addNewField(meta.type, meta.label);
    },
    [builder],
  );

  const selectedField = builder.fields.find(
    (f) => f.id === builder.selectedFieldId,
  );

  if (!builder.form) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Header bar */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-white border-b border-gray-200 h-14 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-gray-900 truncate max-w-xs">
            {builder.form.title}
          </h1>
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              builder.form.status === 'published'
                ? 'bg-green-100 text-green-700'
                : builder.form.status === 'draft'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-600'
            }`}
          >
            {builder.form.status}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={builder.undo}
            disabled={!builder.canUndo}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-30"
            title="Undo"
          >
            Undo
          </button>
          <button
            onClick={builder.redo}
            disabled={!builder.canRedo}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-30"
            title="Redo"
          >
            Redo
          </button>
          {builder.isSaving && (
            <span className="text-xs text-gray-400">Saving...</span>
          )}
          {!builder.isSaving && !builder.isDirty && (
            <span className="text-xs text-green-500">Saved</span>
          )}
        </div>
      </div>

      {/* Main three-column layout */}
      <div className="flex w-full pt-14">
        {/* Left: Field palette */}
        <aside className="w-64 bg-white border-r border-gray-200 overflow-y-auto p-4">
          <FieldPalette onAddField={handleAddField} />
        </aside>

        {/* Center: Canvas */}
        <main className="flex-1 overflow-y-auto p-8">
          <BuilderCanvas
            fields={builder.fields.filter((f) => f.page === builder.activePage)}
            selectedFieldId={builder.selectedFieldId}
            onSelectField={builder.selectField}
            onMoveField={builder.moveFieldByDrag}
            onRemoveField={builder.removeField}
            formTitle={builder.form.title}
            primaryColor={builder.form.primary_color}
          />

          {builder.form.is_multi_page && (
            <div className="flex items-center gap-2 mt-6 justify-center">
              {Array.from(
                new Set(builder.fields.map((f) => f.page)),
              )
                .sort()
                .map((page) => (
                  <button
                    key={page}
                    onClick={() => builder.setActivePage(page)}
                    className={`px-3 py-1 rounded text-sm ${
                      builder.activePage === page
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    Page {page}
                  </button>
                ))}
            </div>
          )}
        </main>

        {/* Right: Properties panel */}
        <aside className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
          {selectedField ? (
            <FieldPropertiesPanel
              field={selectedField}
              onUpdate={(updates) => builder.editField(selectedField.id, updates)}
              onClose={() => builder.selectField(null)}
            />
          ) : (
            <div className="p-6 text-center text-gray-400 mt-20">
              <p className="text-sm">Select a field to edit its properties</p>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
};

export default FormBuilder;
