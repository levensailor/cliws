import { openIconPicker } from './iconpicker.js';

export function openEntryModal({ subsectionId, initial = {}, onSave }) {
  const root = document.getElementById('modal-root');
  root.classList.remove('hidden');
  root.setAttribute('aria-hidden', 'false');

  let selectedIcon = initial.icon || 'fa-solid fa-terminal';

  root.innerHTML = `
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modal-header">
        <h2 class="modal-title">Add Entry</h2>
        <button type="button" class="btn" data-action="close">Close</button>
      </div>
      <div class="modal-body">
        <div class="form-field">
          <label for="entry-name">Name</label>
          <input id="entry-name" type="text" value="${escapeHtml(initial.name || '')}" />
        </div>
        <div class="form-field">
          <label for="entry-cmd">CMD</label>
          <input id="entry-cmd" type="text" value="${escapeHtml(initial.cmd || '')}" />
        </div>
        <div class="form-field">
          <label>Icon</label>
          <button type="button" class="icon-preview-btn" id="icon-preview">
            <i class="${selectedIcon}"></i>
            <span>${selectedIcon}</span>
          </button>
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn" data-action="close">Cancel</button>
        <button type="button" class="btn btn-primary" data-action="save">Save</button>
      </div>
    </div>
  `;

  const close = () => {
    root.classList.add('hidden');
    root.setAttribute('aria-hidden', 'true');
    root.innerHTML = '';
  };

  root.querySelectorAll('[data-action="close"]').forEach((button) => button.addEventListener('click', close));
  root.addEventListener('click', (event) => {
    if (event.target === root) close();
  });

  const preview = root.querySelector('#icon-preview');
  preview.addEventListener('click', () => {
    openIconPicker(selectedIcon, (icon) => {
      selectedIcon = icon;
      preview.querySelector('i').className = icon;
      preview.querySelector('span').textContent = icon;
    });
  });

  root.querySelector('[data-action="save"]').addEventListener('click', async () => {
    const name = root.querySelector('#entry-name').value.trim();
    const cmd = root.querySelector('#entry-cmd').value.trim();
    if (!name || !cmd) return;
    await onSave({
      subsection_id: subsectionId,
      name,
      cmd,
      icon: selectedIcon,
    });
    close();
  });
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
