import { api } from './api.js';
import { setState } from './state.js';
import { renderDashboard } from './render.js';
import { openEntryModal } from './modal.js';
import { openIconPicker } from './iconpicker.js';

let dragContext = null;

export function createEditHandlers({ refresh, onRunEntry }) {
  return {
    onRunEntry,
    onAddSection: async () => {
      await api.createSection({ name: 'NEW SECTION', layout: 'grid' });
      await refresh();
    },
    onAddSubsection: async (sectionId) => {
      await api.createSubsection({ section_id: sectionId, name: 'NEW SUBSECTION' });
      await refresh();
    },
    onAddEntry: async (subsectionId) => {
      openEntryModal({
        subsectionId,
        onSave: async (payload) => {
          await api.createEntry(payload);
          await refresh();
        },
      });
    },
    onUpdateSection: async (id, payload) => {
      await api.updateSection(id, payload);
      await refresh();
    },
    onUpdateSubsection: async (id, payload) => {
      await api.updateSubsection(id, payload);
      await refresh();
    },
    onUpdateEntry: async (id, payload) => {
      await api.updateEntry(id, payload);
      await refresh();
    },
    onDeleteSection: async (id) => {
      await api.deleteSection(id);
      await refresh();
    },
    onDeleteSubsection: async (id) => {
      await api.deleteSubsection(id);
      await refresh();
    },
    onDeleteEntry: async (id) => {
      await api.deleteEntry(id);
      await refresh();
    },
    onPickIcon: (entryId, currentIcon) => {
      openIconPicker(currentIcon, async (icon) => {
        await api.updateEntry(entryId, { icon });
        await refresh();
      });
    },
    onDragStart: (event, entity, id) => {
      dragContext = { entity, id };
      event.dataTransfer.effectAllowed = 'move';
      event.currentTarget.classList.add('dragging');
    },
    onDragOver: (event) => {
      event.preventDefault();
      event.currentTarget.classList.add('drop-target');
    },
    onDrop: async (event, entity, targetId) => {
      event.preventDefault();
      event.currentTarget.classList.remove('drop-target');
      document.querySelectorAll('.dragging').forEach((el) => el.classList.remove('dragging'));
      if (!dragContext || dragContext.entity !== entity || dragContext.id === targetId) {
        dragContext = null;
        return;
      }
      const container = event.currentTarget.closest(entity === 'entries' ? '.subsection-body, .subsection' : '.dashboard, .subsection-columns, #dashboard');
      const selector = entity === 'sections'
        ? '[data-section-id]'
        : entity === 'subsections'
          ? '[data-subsection-id]'
          : '[data-entry-id]';
      const parent = container || document.getElementById('dashboard');
      const items = [...parent.querySelectorAll(selector)];
      const ids = items.map((item) => Number(item.dataset[entity === 'sections' ? 'sectionId' : entity === 'subsections' ? 'subsectionId' : 'entryId']));
      const fromIndex = ids.indexOf(dragContext.id);
      const toIndex = ids.indexOf(targetId);
      if (fromIndex < 0 || toIndex < 0) {
        dragContext = null;
        return;
      }
      ids.splice(fromIndex, 1);
      ids.splice(toIndex, 0, dragContext.id);
      await api.reorder({
        entity,
        items: ids.map((id, position) => ({ id, position })),
      });
      dragContext = null;
      await refresh();
    },
  };
}

export function bindEditToggle(refresh) {
  const toggle = document.getElementById('edit-toggle');
  toggle.addEventListener('click', async () => {
    const next = !document.body.classList.contains('edit-mode');
    document.body.classList.toggle('edit-mode', next);
    toggle.setAttribute('aria-pressed', String(next));
    setState({ editMode: next });
    await refresh();
  });
}

export function mountDashboard(root, handlers) {
  renderDashboard(root, handlers);
}
