export class RunSocket {
  constructor(url = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws/run`) {
    this.url = url;
    this.socket = null;
    this.handlers = {
      started: () => {},
      attached: () => {},
      exit: () => {},
      error: () => {},
      output: () => {},
      stopping: () => {},
    };
    this._connectPromise = null;
  }

  on(event, handler) {
    this.handlers[event] = handler;
  }

  connect() {
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) {
      return Promise.resolve();
    }
    this._connectPromise = new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url);
      this.socket.binaryType = 'arraybuffer';
      this.socket.addEventListener('open', () => resolve());
      this.socket.addEventListener('error', (event) => reject(event));
      this.socket.addEventListener('message', (event) => {
        if (typeof event.data === 'string') {
          const payload = JSON.parse(event.data);
          const handler = this.handlers[payload.type];
          if (handler) {
            handler(payload);
          }
          return;
        }
        this.handlers.output(event.data);
      });
    });
    return this._connectPromise;
  }

  async send(payload) {
    await this.connect();
    this.socket.send(JSON.stringify(payload));
  }

  async start(entryId, cols, rows) {
    await this.send({ type: 'start', entry_id: entryId, cols, rows });
  }

  async attach(runId) {
    await this.send({ type: 'attach', run_id: runId });
  }

  async input(data) {
    await this.send({ type: 'input', data });
  }

  async resize(cols, rows) {
    await this.send({ type: 'resize', cols, rows });
  }

  async signal(signalName = 'SIGINT') {
    await this.send({ type: 'signal', signal: signalName });
  }

  async stop() {
    await this.send({ type: 'stop' });
  }

  close() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}
