import { api } from './api.js';
import { state } from './state.js';

let iconsCache = null;
let renderFrame = null;

async function loadIcons() {
  if (iconsCache) return iconsCache;
  if (state.icons.length) {
    iconsCache = state.icons;
    return iconsCache;
  }
  iconsCache = await api.getIcons();
  return iconsCache;
}

export function openIconPicker(currentIcon, onSelect) {
  const root = document.getElementById('icon-picker-root');
  root.classList.remove('hidden');
  root.setAttribute('aria-hidden', 'false');

  root.innerHTML = `
    <div class="icon-picker" role="dialog" aria-modal="true">
      <div class="icon-picker-header">
        <h2 class="modal-title">Choose Icon</h2>
        <button type="button" class="btn" data-action="close">Close</button>
      </div>
      <div class="icon-picker-toolbar">
        <input type="search" id="icon-search" placeholder="Search icons..." />
      </div>
      <div class="icon-categories" id="icon-categories"></div>
      <div class="icon-grid" id="icon-grid"></div>
    </div>
  `;

  const close = () => {
    root.classList.add('hidden');
    root.setAttribute('aria-hidden', 'true');
    root.innerHTML = '';
    if (renderFrame) cancelAnimationFrame(renderFrame);
  };

  root.querySelector('[data-action="close"]').addEventListener('click', close);
  root.addEventListener('click', (event) => {
    if (event.target === root) close();
  });

  const searchInput = root.querySelector('#icon-search');
  const categoriesEl = root.querySelector('#icon-categories');
  const gridEl = root.querySelector('#icon-grid');

  let activeCategory = 'all';
  let focusedIndex = 0;

  loadIcons().then((icons) => {
    const categories = ['all', ...new Set(icons.flatMap((icon) => icon.categories || []))].slice(0, 24);
    categories.forEach((category) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = `category-chip${category === 'all' ? ' active' : ''}`;
      chip.textContent = category;
      chip.addEventListener('click', () => {
        activeCategory = category;
        categoriesEl.querySelectorAll('.category-chip').forEach((el) => el.classList.remove('active'));
        chip.classList.add('active');
        render();
      });
      categoriesEl.appendChild(chip);
    });
    render();
    searchInput.focus();
  });

  function filteredIcons() {
    const query = searchInput.value.trim().toLowerCase();
    return (iconsCache || []).filter((icon) => {
      const className = `${icon.style} fa-${icon.name}`;
      if (currentIcon && className === currentIcon) return true;
      const categoryMatch = activeCategory === 'all' || (icon.categories || []).includes(activeCategory);
      if (!categoryMatch) return false;
      if (!query) return true;
      const haystack = [icon.label, icon.name, ...(icon.terms || [])].join(' ').toLowerCase();
      return haystack.includes(query);
    });
  }

  function render() {
    if (renderFrame) cancelAnimationFrame(renderFrame);
    renderFrame = requestAnimationFrame(() => {
      const icons = filteredIcons();
      gridEl.innerHTML = '';
      const batchSize = 120;
      let index = 0;

      function renderBatch() {
        const slice = icons.slice(index, index + batchSize);
        slice.forEach((icon, offset) => {
          const absoluteIndex = index + offset;
          const className = `${icon.style} fa-${icon.name}`;
          const button = document.createElement('button');
          button.type = 'button';
          button.className = `icon-item${className === currentIcon ? ' selected' : ''}${absoluteIndex === focusedIndex ? ' focused' : ''}`;
          button.innerHTML = `<i class="${className}"></i><span>${icon.label || icon.name}</span>`;
          button.addEventListener('click', () => {
            onSelect(className);
            close();
          });
          gridEl.appendChild(button);
        });
        index += batchSize;
        if (index < icons.length) {
          requestAnimationFrame(renderBatch);
        }
      }

      renderBatch();
    });
  }

  searchInput.addEventListener('input', () => {
    focusedIndex = 0;
    render();
  });

  root.addEventListener('keydown', (event) => {
    const icons = filteredIcons();
    if (!icons.length) return;
    if (event.key === 'ArrowRight') focusedIndex = Math.min(focusedIndex + 1, icons.length - 1);
    if (event.key === 'ArrowLeft') focusedIndex = Math.max(focusedIndex - 1, 0);
    if (event.key === 'ArrowDown') focusedIndex = Math.min(focusedIndex + 6, icons.length - 1);
    if (event.key === 'ArrowUp') focusedIndex = Math.max(focusedIndex - 6, 0);
    if (['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp'].includes(event.key)) {
      event.preventDefault();
      render();
      const focused = gridEl.querySelector('.focused');
      if (focused) focused.scrollIntoView({ block: 'nearest' });
    }
    if (event.key === 'Enter') {
      const icon = icons[focusedIndex];
      if (!icon) return;
      onSelect(`${icon.style} fa-${icon.name}`);
      close();
    }
    if (event.key === 'Escape') close();
  });
}
