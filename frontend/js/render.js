import { state } from './state.js';

function createDeleteButton(label, onConfirm) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'entry-delete';
  button.textContent = '×';
  button.title = `Delete ${label}`;
  button.addEventListener('click', (event) => {
    event.stopPropagation();
    const existing = button.parentElement.querySelector('.confirm-inline');
    if (existing) {
      existing.remove();
      return;
    }
    const confirm = document.createElement('div');
    confirm.className = 'confirm-inline';
    confirm.innerHTML = 'Delete?<button type="button" class="danger">Yes</button><button type="button">No</button>';
    confirm.addEventListener('click', (innerEvent) => innerEvent.stopPropagation());
    confirm.querySelector('.danger').addEventListener('click', () => onConfirm());
    confirm.querySelector('button:not(.danger)').addEventListener('click', () => confirm.remove());
    button.parentElement.appendChild(confirm);
  });
  return button;
}

function bindEditable(element, getValue, onSave) {
  element.classList.add('editable');
  element.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      element.blur();
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      element.textContent = getValue();
      element.blur();
    }
  });
  element.addEventListener('blur', async () => {
    const next = element.textContent.trim();
    const current = getValue();
    if (next && next !== current) {
      await onSave(next);
    } else {
      element.textContent = current;
    }
  });
}

export function renderDashboard(root, handlers) {
  root.innerHTML = '';
  for (const section of state.tree.sections) {
    root.appendChild(renderSection(section, handlers));
  }
  if (state.editMode) {
    const addSection = document.createElement('button');
    addSection.type = 'button';
    addSection.className = 'ghost-add';
    addSection.textContent = '+ ADD SECTION';
    addSection.addEventListener('click', () => handlers.onAddSection());
    root.appendChild(addSection);
  }
}

function renderSection(section, handlers) {
  const sectionEl = document.createElement('section');
  sectionEl.className = `section section-${section.layout}`;
  sectionEl.dataset.sectionId = section.id;
  sectionEl.draggable = state.editMode;

  const headerWrap = document.createElement('div');
  headerWrap.className = 'section-header-wrap';
  const handle = document.createElement('span');
  handle.className = 'drag-handle';
  handle.textContent = '⋮⋮';
  const header = document.createElement('h2');
  header.className = 'section-header editable';
  header.textContent = section.name;
  headerWrap.appendChild(handle);
  headerWrap.appendChild(header);
  if (state.editMode) {
    bindEditable(header, () => section.name, (name) => handlers.onUpdateSection(section.id, { name }));
    headerWrap.appendChild(createDeleteButton('section', () => handlers.onDeleteSection(section.id)));
    sectionEl.addEventListener('dragstart', (event) => handlers.onDragStart(event, 'sections', section.id));
    sectionEl.addEventListener('dragover', (event) => handlers.onDragOver(event));
    sectionEl.addEventListener('drop', (event) => handlers.onDrop(event, 'sections', section.id));
  }
  sectionEl.appendChild(headerWrap);

  if (section.layout === 'grid') {
    for (const subsection of section.subsections) {
      sectionEl.appendChild(renderGridSubsection(subsection, handlers));
    }
  } else {
    const columns = document.createElement('div');
    columns.className = 'subsection-columns';
    for (const subsection of section.subsections) {
      columns.appendChild(renderListSubsection(subsection, handlers));
    }
    sectionEl.appendChild(columns);
    if (state.editMode) {
      const addSub = document.createElement('button');
      addSub.type = 'button';
      addSub.className = 'ghost-add';
      addSub.textContent = '+ ADD SUBSECTION';
      addSub.addEventListener('click', () => handlers.onAddSubsection(section.id));
      sectionEl.appendChild(addSub);
    }
  }

  return sectionEl;
}

function renderGridSubsection(subsection, handlers) {
  const wrap = document.createElement('div');
  wrap.className = 'subsection';
  wrap.dataset.subsectionId = subsection.id;

  const headerWrap = document.createElement('div');
  headerWrap.className = 'subsection-header-wrap';
  const header = document.createElement('h3');
  header.className = 'subsection-header editable';
  header.textContent = subsection.name;
  headerWrap.appendChild(header);
  if (state.editMode) {
    bindEditable(header, () => subsection.name, (name) => handlers.onUpdateSubsection(subsection.id, { name }));
    headerWrap.appendChild(createDeleteButton('subsection', () => handlers.onDeleteSubsection(subsection.id)));
  }
  wrap.appendChild(headerWrap);

  const body = document.createElement('div');
  body.className = 'subsection-body';
  for (const entry of subsection.entries) {
    body.appendChild(renderEntryCard(entry, subsection.id, handlers));
  }
  if (state.editMode) {
    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'ghost-add';
    add.textContent = '+ ADD ENTRY';
    add.addEventListener('click', () => handlers.onAddEntry(subsection.id));
    body.appendChild(add);
  }
  wrap.appendChild(body);
  return wrap;
}

function renderListSubsection(subsection, handlers) {
  const wrap = document.createElement('div');
  wrap.className = 'subsection';
  wrap.dataset.subsectionId = subsection.id;
  wrap.draggable = state.editMode;

  const headerWrap = document.createElement('div');
  headerWrap.className = 'subsection-header-wrap';
  const handle = document.createElement('span');
  handle.className = 'drag-handle';
  handle.textContent = '⋮⋮';
  const header = document.createElement('h3');
  header.className = 'subsection-header editable';
  header.textContent = subsection.name;
  headerWrap.appendChild(handle);
  headerWrap.appendChild(header);
  if (state.editMode) {
    bindEditable(header, () => subsection.name, (name) => handlers.onUpdateSubsection(subsection.id, { name }));
    headerWrap.appendChild(createDeleteButton('subsection', () => handlers.onDeleteSubsection(subsection.id)));
    wrap.addEventListener('dragstart', (event) => handlers.onDragStart(event, 'subsections', subsection.id));
    wrap.addEventListener('dragover', (event) => handlers.onDragOver(event));
    wrap.addEventListener('drop', (event) => handlers.onDrop(event, 'subsections', subsection.id));
  }
  wrap.appendChild(headerWrap);

  for (const entry of subsection.entries) {
    wrap.appendChild(renderEntryRow(entry, subsection.id, handlers));
  }
  if (state.editMode) {
    const add = document.createElement('button');
    add.type = 'button';
    add.className = 'ghost-add';
    add.textContent = '+ ADD ENTRY';
    add.addEventListener('click', () => handlers.onAddEntry(subsection.id));
    wrap.appendChild(add);
  }
  return wrap;
}

function renderEntryCard(entry, subsectionId, handlers) {
  const card = document.createElement('div');
  card.className = 'entry-card';
  card.dataset.entryId = entry.id;
  card.draggable = state.editMode;

  const icon = document.createElement('i');
  icon.className = `${entry.icon} entry-icon`;
  const text = document.createElement('div');
  text.className = 'entry-text';
  const name = document.createElement('p');
  name.className = 'entry-name editable';
  name.textContent = entry.name;
  const cmd = document.createElement('p');
  cmd.className = 'entry-cmd editable';
  cmd.textContent = entry.cmd;
  text.appendChild(name);
  text.appendChild(cmd);
  card.appendChild(icon);
  card.appendChild(text);

  if (state.editMode) {
    bindEditable(name, () => entry.name, (value) => handlers.onUpdateEntry(entry.id, { name: value }));
    bindEditable(cmd, () => entry.cmd, (value) => handlers.onUpdateEntry(entry.id, { cmd: value }));
    icon.addEventListener('click', (event) => {
      event.stopPropagation();
      handlers.onPickIcon(entry.id, entry.icon);
    });
    card.appendChild(createDeleteButton('entry', () => handlers.onDeleteEntry(entry.id)));
    card.addEventListener('dragstart', (event) => handlers.onDragStart(event, 'entries', entry.id));
    card.addEventListener('dragover', (event) => handlers.onDragOver(event));
    card.addEventListener('drop', (event) => handlers.onDrop(event, 'entries', entry.id));
  } else {
    card.addEventListener('click', () => handlers.onRunEntry(entry));
  }

  return card;
}

function renderEntryRow(entry, subsectionId, handlers) {
  const row = document.createElement('div');
  row.className = 'entry-row';
  row.dataset.entryId = entry.id;
  row.draggable = state.editMode;

  const icon = document.createElement('i');
  icon.className = `${entry.icon} entry-icon`;
  const name = document.createElement('p');
  name.className = 'entry-name editable';
  name.textContent = entry.name;
  row.appendChild(icon);
  row.appendChild(name);

  if (state.editMode) {
    bindEditable(name, () => entry.name, (value) => handlers.onUpdateEntry(entry.id, { name: value }));
    icon.addEventListener('click', (event) => {
      event.stopPropagation();
      handlers.onPickIcon(entry.id, entry.icon);
    });
    row.appendChild(createDeleteButton('entry', () => handlers.onDeleteEntry(entry.id)));
    row.addEventListener('dragstart', (event) => handlers.onDragStart(event, 'entries', entry.id));
    row.addEventListener('dragover', (event) => handlers.onDragOver(event));
    row.addEventListener('drop', (event) => handlers.onDrop(event, 'entries', entry.id));
  } else {
    row.addEventListener('click', () => handlers.onRunEntry(entry));
  }

  return row;
}

export function updateHeader() {
  const dateLine = document.getElementById('date-line');
  const greeting = document.getElementById('greeting');
  const now = new Date();
  dateLine.textContent = now.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).toUpperCase();
  const hour = now.getHours();
  let text = 'Good evening!';
  if (hour < 12) text = 'Good morning!';
  else if (hour < 18) text = 'Good afternoon!';
  greeting.textContent = text;
}
