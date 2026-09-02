import { RunSocket } from './ws.js';

const DRAWER_HEIGHT_KEY = 'cliws.drawerHeight';

export class TerminalDrawer {
  constructor() {
    this.drawer = document.getElementById('terminal-drawer');
    this.tabsEl = document.getElementById('drawer-tabs');
    this.host = document.getElementById('terminal-host');
    this.sessions = new Map();
    this.activeId = null;
    this._bindControls();
    this._bindResize();
    this._restoreHeight();
  }

  _bindControls() {
    document.getElementById('btn-ctrlc').addEventListener('click', () => this.activeSession()?.socket.signal('SIGINT'));
    document.getElementById('btn-stop').addEventListener('click', () => this.activeSession()?.socket.stop());
    document.getElementById('btn-restart').addEventListener('click', () => this.activeSession()?.restart());
    document.getElementById('btn-clear').addEventListener('click', () => this.activeSession()?.term.clear());
    document.getElementById('btn-copy').addEventListener('click', () => {
      const session = this.activeSession();
      if (!session) return;
      const selection = session.term.getSelection();
      if (selection) navigator.clipboard.writeText(selection);
    });
    document.getElementById('btn-download').addEventListener('click', () => {
      const session = this.activeSession();
      if (!session) return;
      const blob = new Blob([session.outputBuffer], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${session.label.replace(/\s+/g, '_')}.log`;
      anchor.click();
      URL.revokeObjectURL(url);
    });
    document.getElementById('btn-collapse').addEventListener('click', () => this.toggleCollapse());
  }

  _bindResize() {
    const resizer = document.getElementById('drawer-resizer');
    let startY = 0;
    let startHeight = 0;
    resizer.addEventListener('mousedown', (event) => {
      startY = event.clientY;
      startHeight = this.drawer.offsetHeight;
      const onMove = (moveEvent) => {
        const delta = startY - moveEvent.clientY;
        const next = Math.max(180, Math.min(window.innerHeight - 120, startHeight + delta));
        this.setHeight(next);
      };
      const onUp = () => {
        window.removeEventListener('mousemove', onMove);
        window.removeEventListener('mouseup', onUp);
        localStorage.setItem(DRAWER_HEIGHT_KEY, String(this.drawer.offsetHeight));
      };
      window.addEventListener('mousemove', onMove);
      window.addEventListener('mouseup', onUp);
    });
  }

  _restoreHeight() {
    const saved = Number(localStorage.getItem(DRAWER_HEIGHT_KEY));
    if (saved) this.setHeight(saved);
  }

  setHeight(height) {
    document.documentElement.style.setProperty('--drawer-height', `${height}px`);
    this.drawer.style.height = `${height}px`;
    this.sessions.forEach((session) => session.fit());
  }

  open() {
    this.drawer.classList.remove('collapsed');
    this.drawer.setAttribute('aria-hidden', 'false');
    document.body.classList.add('drawer-open');
  }

  toggleCollapse() {
    const collapsed = this.drawer.classList.toggle('collapsed');
    this.drawer.setAttribute('aria-hidden', String(collapsed));
    document.body.classList.toggle('drawer-open', !collapsed);
    if (!collapsed) this.activeSession()?.fit();
  }

  activeSession() {
    return this.activeId ? this.sessions.get(this.activeId) : null;
  }

  async runEntry(entry) {
    const sessionId = `entry-${entry.id}-${Date.now()}`;
    const socket = new RunSocket();
    const pane = document.createElement('div');
    pane.className = 'terminal-pane';
    this.host.appendChild(pane);

    const term = new globalThis.Terminal({
      convertEagerly: true,
      fontFamily: 'JetBrains Mono, Fira Code, Consolas, monospace',
      fontSize: 13,
      theme: {
        background: '#1e2127',
        foreground: '#dfd9d6',
        cursor: '#98c379',
        selectionBackground: '#3e4451',
      },
    });
    const fitAddon = new globalThis.FitAddon();
    const webLinksAddon = new globalThis.WebLinksAddon();
    term.loadAddon(fitAddon);
    term.loadAddon(webLinksAddon);
    term.open(pane);

    const session = {
      id: sessionId,
      entry,
      socket,
      term,
      fitAddon,
      pane,
      label: entry.name,
      runId: null,
      outputBuffer: '',
      running: true,
      fit: () => {
        fitAddon.fit();
        const dims = fitAddon.proposeDimensions();
        if (dims && session.runId) {
          socket.resize(dims.cols, dims.rows);
        }
      },
      restart: async () => {
        term.clear();
        session.outputBuffer = '';
        await socket.start(entry.id, term.cols, term.rows);
      },
    };

    socket.on('started', (payload) => {
      session.runId = payload.run_id;
      session.fit();
    });
    socket.on('output', (data) => {
      const text = typeof data === 'string' ? data : new TextDecoder().decode(data);
      session.outputBuffer += text;
      term.write(data);
    });
    socket.on('exit', (payload) => {
      session.running = false;
      this._updateTabStatus(sessionId, false, payload.code);
    });
    socket.on('error', (payload) => {
      term.writeln(`\r\n[cliws error] ${payload.message}`);
    });

    term.onData((data) => socket.input(data));

    const observer = new ResizeObserver(() => session.fit());
    observer.observe(pane);

    this.sessions.set(sessionId, session);
    this._addTab(sessionId, entry.name, true);
    this.setActive(sessionId);
    this.open();

    await socket.start(entry.id, term.cols || 120, term.rows || 30);
  }

  _addTab(sessionId, label, running) {
    const tab = document.createElement('button');
    tab.type = 'button';
    tab.className = 'drawer-tab';
    tab.dataset.sessionId = sessionId;
    tab.innerHTML = `<span class="status-dot${running ? '' : ' exit'}"></span><span>${label}</span>`;
    tab.addEventListener('click', () => this.setActive(sessionId));
    this.tabsEl.appendChild(tab);
  }

  _updateTabStatus(sessionId, running, code) {
    const tab = this.tabsEl.querySelector(`[data-session-id="${sessionId}"] .status-dot`);
    if (!tab) return;
    tab.classList.toggle('exit', !running);
    tab.title = running ? 'Running' : `Exit ${code}`;
  }

  setActive(sessionId) {
    this.activeId = sessionId;
    this.tabsEl.querySelectorAll('.drawer-tab').forEach((tab) => {
      tab.classList.toggle('active', tab.dataset.sessionId === sessionId);
    });
    this.sessions.forEach((session, id) => {
      session.pane.classList.toggle('active', id === sessionId);
      if (id === sessionId) session.fit();
    });
  }
}
