(function () {
  function apiStateUrl() {
    const paths = window.APP_PATHS || {};
    return paths.apiState || '/api/state';
  }

  async function getRawLog() {
    const response = await fetch(apiStateUrl(), { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return Array.isArray(data.tcp_raw_log) ? data.tcp_raw_log : [];
  }

  function makeButton(label, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.textContent = label;
    button.addEventListener('click', async () => {
      const original = button.textContent;
      button.disabled = true;
      try {
        await handler();
        button.textContent = 'Done';
        setTimeout(() => { button.textContent = original; }, 1200);
      } catch (error) {
        button.textContent = 'Error';
        setTimeout(() => { button.textContent = original; }, 1600);
        console.error('TCP log action failed', error);
      } finally {
        button.disabled = false;
      }
    });
    return button;
  }

  async function copyRawLog() {
    const lines = await getRawLog();
    const text = lines.join('\n');
    if (!navigator.clipboard || !window.isSecureContext) {
      throw new Error('Clipboard API unavailable; use the download button instead.');
    }
    await navigator.clipboard.writeText(text);
  }

  async function downloadRawLog() {
    const lines = await getRawLog();
    const text = lines.join('\n') + (lines.length ? '\n' : '');
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `bmw-wallboxproxy-tcp-raw-${new Date().toISOString().replace(/[:.]/g, '-')}.log`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  function installControls() {
    document.querySelectorAll('details').forEach((details) => {
      const summary = details.querySelector('summary');
      if (!summary || !summary.textContent.toLowerCase().includes('tcp raw packets')) return;
      if (details.querySelector('.tcp-log-actions')) return;

      const actions = document.createElement('div');
      actions.className = 'tcp-log-actions';
      actions.style.display = 'flex';
      actions.style.gap = '8px';
      actions.style.flexWrap = 'wrap';
      actions.style.margin = '10px 0';
      actions.appendChild(makeButton('Download logs', downloadRawLog));
      actions.appendChild(makeButton('Copy to clipboard', copyRawLog));
      details.insertBefore(actions, summary.nextSibling);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', installControls);
  } else {
    installControls();
  }
}());
