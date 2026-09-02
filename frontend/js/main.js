import { api } from './api.js';
import { setState } from './state.js';
import { updateHeader } from './render.js';
import { bindEditToggle, createEditHandlers, mountDashboard } from './edit.js';
import { TerminalDrawer } from './terminal.js';

const dashboard = document.getElementById('dashboard');
const terminalDrawer = new TerminalDrawer();

async function refresh() {
  const tree = await api.getTree();
  setState({ tree });
  const handlers = createEditHandlers({
    refresh,
    onRunEntry: (entry) => terminalDrawer.runEntry(entry),
  });
  mountDashboard(dashboard, handlers);
}

async function bootstrap() {
  updateHeader();
  setInterval(updateHeader, 60_000);

  try {
    const icons = await api.getIcons();
    const settings = await api.getSettings();
    setState({ icons, settings: settings.settings || {} });
  } catch (error) {
    console.warn('Optional preload failed', error);
  }

  bindEditToggle(refresh);
  await refresh();
}

bootstrap().catch((error) => {
  console.error(error);
  dashboard.innerHTML = `<p>Failed to load CLIWS dashboard: ${error.message}</p>`;
});
