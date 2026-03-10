/**
 * Custom hook wrapping the form builder store with API persistence.
 * Provides save, auto-save, field CRUD with server sync.
 */
import { useCallback, useEffect, useRef } from 'react';
import {
  createField,
  deleteField,
  getForm,
  reorderFields,
  updateField as apiUpdateField,
  updateForm,
} from '../api/forms';
import { useFormBuilderStore } from '../store/formBuilderStore';
import type { FormField } from '../api/forms';

const AUTO_SAVE_DELAY_MS = 3000;

export function useFormBuilder(formId: string) {
  const store = useFormBuilderStore();
  const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Load form on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const { data } = await getForm(formId);
        if (!cancelled) {
          store.setForm(data);
        }
      } catch (err) {
        console.error('Failed to load form:', err);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formId]);

  // Auto-save when dirty
  useEffect(() => {
    if (!store.isDirty) return;
    if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    autoSaveTimer.current = setTimeout(() => {
      saveFieldOrder();
    }, AUTO_SAVE_DELAY_MS);
    return () => {
      if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.isDirty, store.fields]);

  const saveFieldOrder = useCallback(async () => {
    if (!store.form) return;
    store.setSaving(true);
    try {
      const orderPayload = store.fields.map((f, i) => ({
        id: f.id,
        order: i,
        page: f.page,
      }));
      await reorderFields(store.form.id, orderPayload);
      store.markClean();
    } catch (err) {
      console.error('Failed to save field order:', err);
    } finally {
      store.setSaving(false);
    }
  }, [store]);

  const addNewField = useCallback(
    async (fieldType: string, label: string) => {
      if (!store.form) return;
      store.pushHistory(`Add ${fieldType} field`);
      try {
        const { data } = await createField(store.form.id, {
          field_type: fieldType,
          label,
          order: store.fields.length,
          page: store.activePage,
          required: false,
        });
        store.addField(data);
        store.selectField(data.id);
      } catch (err) {
        console.error('Failed to add field:', err);
        store.undo();
      }
    },
    [store],
  );

  const editField = useCallback(
    async (fieldId: string, updates: Partial<FormField>) => {
      if (!store.form) return;
      store.pushHistory(`Edit field`);
      store.updateField(fieldId, updates);
      try {
        await apiUpdateField(store.form.id, fieldId, updates);
      } catch (err) {
        console.error('Failed to update field:', err);
        store.undo();
      }
    },
    [store],
  );

  const removeField = useCallback(
    async (fieldId: string) => {
      if (!store.form) return;
      store.pushHistory('Remove field');
      store.removeField(fieldId);
      try {
        await deleteField(store.form.id, fieldId);
      } catch (err) {
        console.error('Failed to delete field:', err);
        store.undo();
      }
    },
    [store],
  );

  const moveFieldByDrag = useCallback(
    (fromIndex: number, toIndex: number) => {
      store.pushHistory('Reorder fields');
      store.moveField(fromIndex, toIndex);
    },
    [store],
  );

  const updateFormMeta = useCallback(
    async (updates: Record<string, unknown>) => {
      if (!store.form) return;
      try {
        await updateForm(store.form.id, updates as any);
        const { data } = await getForm(store.form.id);
        store.setForm(data);
      } catch (err) {
        console.error('Failed to update form:', err);
      }
    },
    [store],
  );

  return {
    form: store.form,
    fields: store.fields,
    selectedFieldId: store.selectedFieldId,
    activePage: store.activePage,
    isDirty: store.isDirty,
    isSaving: store.isSaving,

    selectField: store.selectField,
    setActivePage: store.setActivePage,
    addNewField,
    editField,
    removeField,
    moveFieldByDrag,
    updateFormMeta,
    undo: store.undo,
    redo: store.redo,
    canUndo: store.historyIndex > 0,
    canRedo: store.historyIndex < store.history.length - 1,
  };
}
