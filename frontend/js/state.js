export const state = {
  tree: { sections: [] },
  editMode: false,
  icons: [],
  settings: {},
  listeners: new Set(),
};

export function setState(patch) {
  Object.assign(state, patch);
  state.listeners.forEach((listener) => listener(state));
}

export function subscribe(listener) {
  state.listeners.add(listener);
  return () => state.listeners.delete(listener);
}

export function findEntry(entryId) {
  for (const section of state.tree.sections) {
    for (const subsection of section.subsections) {
      for (const entry of subsection.entries) {
        if (entry.id === entryId) {
          return { section, subsection, entry };
        }
      }
    }
  }
  return null;
}
