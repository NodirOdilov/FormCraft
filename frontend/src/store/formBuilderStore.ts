/**
 * Zustand store for the drag-and-drop form builder.
 * Manages the active form, its fields, drag state, and undo/redo history.
 */
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import type { FormDetail, FormField } from '../api/forms';

interface HistoryEntry {
  fields: FormField[];
  label: string;
}

interface FormBuilderState {
  // Core state
  form: FormDetail | null;
  fields: FormField[];
  selectedFieldId: string | null;
  activePage: number;
  isDirty: boolean;
  isSaving: boolean;

  // Drag state
  draggedFieldIndex: number | null;
  dropTargetIndex: number | null;

  // Undo / redo
  history: HistoryEntry[];
  historyIndex: number;

  // Actions
  setForm: (form: FormDetail) => void;
  setFields: (fields: FormField[]) => void;
  selectField: (fieldId: string | null) => void;
  setActivePage: (page: number) => void;

  addField: (field: FormField) => void;
  updateField: (fieldId: string, updates: Partial<FormField>) => void;
  removeField: (fieldId: string) => void;
  moveField: (fromIndex: number, toIndex: number) => void;

  setDraggedField: (index: number | null) => void;
  setDropTarget: (index: number | null) => void;

  undo: () => void;
  redo: () => void;
  pushHistory: (label: string) => void;

  setSaving: (saving: boolean) => void;
  markClean: () => void;
}

const MAX_HISTORY = 50;

export const useFormBuilderStore = create<FormBuilderState>()(
  immer((set, get) => ({
    form: null,
    fields: [],
    selectedFieldId: null,
    activePage: 1,
    isDirty: false,
    isSaving: false,

    draggedFieldIndex: null,
    dropTargetIndex: null,

    history: [],
    historyIndex: -1,

    setForm: (form) =>
      set((state) => {
        state.form = form;
        state.fields = form.fields_data || [];
        state.isDirty = false;
        state.history = [{ fields: [...(form.fields_data || [])], label: 'Initial' }];
        state.historyIndex = 0;
      }),

    setFields: (fields) =>
      set((state) => {
        state.fields = fields;
        state.isDirty = true;
      }),

    selectField: (fieldId) =>
      set((state) => {
        state.selectedFieldId = fieldId;
      }),

    setActivePage: (page) =>
      set((state) => {
        state.activePage = page;
      }),

    addField: (field) =>
      set((state) => {
        state.fields.push(field);
        state.isDirty = true;
      }),

    updateField: (fieldId, updates) =>
      set((state) => {
        const idx = state.fields.findIndex((f) => f.id === fieldId);
        if (idx !== -1) {
          state.fields[idx] = { ...state.fields[idx], ...updates };
          state.isDirty = true;
        }
      }),

    removeField: (fieldId) =>
      set((state) => {
        state.fields = state.fields.filter((f) => f.id !== fieldId);
        if (state.selectedFieldId === fieldId) {
          state.selectedFieldId = null;
        }
        state.isDirty = true;
      }),

    moveField: (fromIndex, toIndex) =>
      set((state) => {
        const moved = state.fields.splice(fromIndex, 1)[0];
        state.fields.splice(toIndex, 0, moved);
        // Recalculate order values
        state.fields.forEach((f, i) => {
          f.order = i;
        });
        state.isDirty = true;
      }),

    setDraggedField: (index) =>
      set((state) => {
        state.draggedFieldIndex = index;
      }),

    setDropTarget: (index) =>
      set((state) => {
        state.dropTargetIndex = index;
      }),

    pushHistory: (label) =>
      set((state) => {
        const newEntry: HistoryEntry = {
          fields: JSON.parse(JSON.stringify(state.fields)),
          label,
        };
        // Truncate any future history entries if we branched off
        const truncated = state.history.slice(0, state.historyIndex + 1);
        truncated.push(newEntry);
        if (truncated.length > MAX_HISTORY) {
          truncated.shift();
        }
        state.history = truncated;
        state.historyIndex = truncated.length - 1;
      }),

    undo: () =>
      set((state) => {
        if (state.historyIndex > 0) {
          state.historyIndex -= 1;
          state.fields = JSON.parse(
            JSON.stringify(state.history[state.historyIndex].fields),
          );
          state.isDirty = true;
        }
      }),

    redo: () =>
      set((state) => {
        if (state.historyIndex < state.history.length - 1) {
          state.historyIndex += 1;
          state.fields = JSON.parse(
            JSON.stringify(state.history[state.historyIndex].fields),
          );
          state.isDirty = true;
        }
      }),

    setSaving: (saving) =>
      set((state) => {
        state.isSaving = saving;
      }),

    markClean: () =>
      set((state) => {
        state.isDirty = false;
      }),
  })),
);
