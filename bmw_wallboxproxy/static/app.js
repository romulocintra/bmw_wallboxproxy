var autoRefreshEnabled = true;

const OUTPUT_REGISTERS = [
  { group: 'Voltage & Frequency' },
  { addr: '0x5000', key: 'voltage_avg', label: 'Voltage avg', unit: 'V', decimals: 1 },
  { addr: '0x5002', key: 'u1', label: 'Voltage L1', unit: 'V', decimals: 1 },
  { addr: '0x5004', key: 'u2', label: 'Voltage L2', unit: 'V', decimals: 1 },
  { addr: '0x5006', key: 'u3', label: 'Voltage L3', unit: 'V', decimals: 1 },
  { addr: '0x5008', key: 'freq', label: 'Frequency', unit: 'Hz', decimals: 2 },
  { group: 'Current' },
  { addr: '0x500A', key: 'current_total', label: 'Current total', unit: 'A', decimals: 2 },
  { addr: '0x500C', key: 'i1', label: 'Current L1', unit: 'A', decimals: 2 },
  { addr: '0x500E', key: 'i2', label: 'Current L2', unit: 'A', decimals: 2 },
  { addr: '0x5010', key: 'i3', label: 'Current L3', unit: 'A', decimals: 2 },
  { group: 'Active Power' },
  { addr: '0x5012', key: 'p_total', label: 'Total active power', unit: 'kW', decimals: 3 },
  { addr: '0x5014', key: 'p1', label: 'Active power L1', unit: 'kW', decimals: 3 },
  { addr: '0x5016', key: 'p2', label: 'Active power L2', unit: 'kW', decimals: 3 },
  { addr: '0x5018', key: 'p3', label: 'Active power L3', unit: 'kW', decimals: 3 },
  { group: 'Reactive Power' },
  { addr: '0x501A', key: 'q_total', label: 'Total reactive power', unit: 'kvar', decimals: 3 },
  { addr: '0x501C', key: 'q1', label: 'Reactive power L1', unit: 'kvar', decimals: 3 },
  { addr: '0x501E', key: 'q2', label: 'Reactive power L2', unit: 'kvar', decimals: 3 },
  { addr: '0x5020', key: 'q3', label: 'Reactive power L3', unit: 'kvar', decimals: 3 },
  { group: 'Apparent Power' },
  { addr: '0x5022', key: 's_total', label: 'Total apparent power', unit: 'kVA', decimals: 3 },
  { addr: '0x5024', key: 's1', label: 'Apparent power L1', unit: 'kVA', decimals: 3 },
  { addr: '0x5026', key: 's2', label: 'Apparent power L2', unit: 'kVA', decimals: 3 },
  { addr: '0x5028', key: 's3', label: 'Apparent power L3', unit: 'kVA', decimals: 3 },
  { group: 'Power Factor' },
  { addr: '0x502A', key: 'pf_total', label: 'Power factor total', unit: '—', decimals: 3 },
  { addr: '0x502C', key: 'pf1', label: 'Power factor L1', unit: '—', decimals: 3 },
  { addr: '0x502E', key: 'pf2', label: 'Power factor L2', unit: '—', decimals: 3 },
  { addr: '0x5030', key: 'pf3', label: 'Power factor L3', unit: '—', decimals: 3 },
  { group: 'Energy' },
  { addr: '0x6000', key: 'e_total', label: 'Total active energy', unit: 'kWh', decimals: 3 },
  { addr: '0x600C', key: 'e_import', label: 'Forward active energy (import)', unit: 'kWh', decimals: 3 },
  { addr: '0x6018', key: 'e_export', label: 'Reverse active energy (export)', unit: 'kWh', decimals: 3 },
];

const REGISTER_GROUPS = [
  { start: 0x5000, end: 0x5001, label: 'Voltage' },
  { start: 0x5002, end: 0x5003, label: 'Voltage L1' },
  { start: 0x5004, end: 0x5005, label: 'Voltage L2' },
  { start: 0x5006, end: 0x5007, label: 'Voltage L3' },
  { start: 0x5008, end: 0x5009, label: 'Frequency' },
  { start: 0x500A, end: 0x500B, label: 'Current' },
  { start: 0x500C, end: 0x500D, label: 'Current L1' },
  { start: 0x500E, end: 0x500F, label: 'Current L2' },
  { start: 0x5010, end: 0x5011, label: 'Current L3' },
  { start: 0x5012, end: 0x5013, label: 'Total active power' },
  { start: 0x5014, end: 0x5015, label: 'Active power L1' },
  { start: 0x5016, end: 0x5017, label: 'Active power L2' },
  { start: 0x5018, end: 0x5019, label: 'Active power L3' },
  { start: 0x501A, end: 0x501B, label: 'Total reactive power' },
  { start: 0x501C, end: 0x501D, label: 'Reactive power L1' },
  { start: 0x501E, end: 0x501F, label: 'Reactive power L2' },
  { start: 0x5020, end: 0x5021, label: 'Reactive power L3' },
  { start: 0x5022, end: 0x5023, label: 'Total apparent power' },
  { start: 0x5024, end: 0x5025, label: 'Apparent power L1' },
  { start: 0x5026, end: 0x5027, label: 'Apparent power L2' },
  { start: 0x5028, end: 0x5029, label: 'Apparent power L3' },
  { start: 0x502A, end: 0x502B, label: 'Power factor' },
  { start: 0x502C, end: 0x502D, label: 'Power factor L1' },
  { start: 0x502E, end: 0x502F, label: 'Power factor L2' },
  { start: 0x5030, end: 0x5031, label: 'Power factor L3' },
  { start: 0x6000, end: 0x6001, label: 'Total active energy' },
  { start: 0x6002, end: 0x6003, label: 'T1 total active energy' },
  { start: 0x6004, end: 0x6005, label: 'T2 total active energy' },
  { start: 0x6006, end: 0x6007, label: 'L1 total active energy' },
  { start: 0x6008, end: 0x6009, label: 'L2 total active energy' },
  { start: 0x600A, end: 0x600B, label: 'L3 total active energy' },
  { start: 0x600C, end: 0x600D, label: 'Forward active energy' },
  { start: 0x600E, end: 0x600F, label: 'T1 forward active energy' },
  { start: 0x6010, end: 0x6011, label: 'T2 forward active energy' },
  { start: 0x6012, end: 0x6013, label: 'L1 forward active energy' },
  { start: 0x6014, end: 0x6015, label: 'L2 forward active energy' },
  { start: 0x6016, end: 0x6017, label: 'L3 forward active energy' },
  { start: 0x6018, end: 0x6019, label: 'Reverse active energy' },
  { start: 0x601A, end: 0x601B, label: 'T1 reverse active energy' },
  { start: 0x601C, end: 0x601D, label: 'T2 reverse active energy' },
  { start: 0x601E, end: 0x601F, label: 'L1 reverse active energy' },
  { start: 0x6020, end: 0x6021, label: 'L2 reverse active energy' },
  { start: 0x6022, end: 0x6023, label: 'L3 reverse active energy' }
];

function byId(id) {
  return document.getElementById(id);
}

function appEndpoint(path) {
  const paths = window.APP_PATHS || {};
  if (Object.prototype.hasOwnProperty.call(paths, path)) {
    return paths[path];
  }

  const relativePath = String(path).replace(/^\//, '');
  return `./${relativePath}`;
}

function setText(id, value) {
  const element = byId(id);
  if (element) {
    element.textContent = value;
  }
}

function setHtml(id, value) {
  const element = byId(id);
  if (element) {
    element.innerHTML = value;
  }
}

function formatHexWord(value) {
  return `0x${value.toString(16).toUpperCase().padStart(4, '0')}`;
}

function describeRegisterRange(startAddr, quantity) {
  const endAddr = startAddr + quantity - 1;
  const overlaps = REGISTER_GROUPS
    .filter((group) => group.end >= startAddr && group.start <= endAddr)
    .map((group) => group.label);

  if (overlaps.length) {
    return overlaps.join(', ');
  }

  if (startAddr >= 0x5000 && endAddr <= 0x50FF) {
    return 'Measurement register block';
  }
  if (startAddr >= 0x6000 && endAddr <= 0x60FF) {
    return 'Energy register block';
  }
  return 'Unmapped or vendor-specific block';
}

function parseWordList(wordsText) {
  if (!wordsText) {
    return [];
  }
  return wordsText.trim().split(/\s+/).filter(Boolean);
}

function countNonZeroWords(words) {
  return words.reduce((count, word) => count + (word !== '0000' ? 1 : 0), 0);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatTransportLabel(mode) {
  if (mode === 'rtu_over_tcp') {
    return 'RTU over TCP';
  }
  if (mode === 'modbus_tcp') {
    return 'Modbus TCP';
  }
  return mode;
}

function summarizeWords(words) {
  if (!words.length) {
    return 'No register data returned';
  }

  const preview = words.slice(0, 6).join(' ');
  const suffix = words.length > 6 ? ` +${words.length - 6} more` : '';
  return `${preview}${suffix}`;
}

function buildRawModbusEntries(logLines) {
  return logLines.slice(0, 80).map((line) => {
    const match = line.match(/^(\d{2}:\d{2}:\d{2})\s+(.*)$/);
    const timestamp = match ? match[1] : '--:--:--';
    const message = match ? match[2] : line;

    let tone = 'meta';
    let kind = 'Info';
    let icon = 'i';
    let title = message;
    let body = '';
    let chips = [];

    const decMatch = message.match(/^DEC mode=([^\s]+) slave=(\d+) fc=(\d+) start=0x([0-9A-F]+) qty=(\d+)$/);
    if (decMatch) {
      const startAddr = parseInt(decMatch[4], 16);
      const quantity = Number(decMatch[5]);
      const endAddr = startAddr + quantity - 1;
      tone = 'request';
      kind = 'Request';
      icon = 'RX';
      title = `${formatTransportLabel(decMatch[1])} read request`;
      body = `${describeRegisterRange(startAddr, quantity)} from ${formatHexWord(startAddr)} to ${formatHexWord(endAddr)}.`;
      chips = [`Slave ${decMatch[2]}`, `FC ${decMatch[3]}`, `Qty ${quantity}`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const mapMatch = message.match(/^MAP slave=(\d+) fc=(\d+) addr=0x([0-9A-F]+)-0x([0-9A-F]+) words=(.*)$/);
    if (mapMatch) {
      const words = parseWordList(mapMatch[5]);
      tone = 'response';
      kind = 'Response';
      icon = 'TX';
      title = `Mapped ${words.length} holding registers`;
      body = summarizeWords(words);
      chips = [`Slave ${mapMatch[1]}`, `FC ${mapMatch[2]}`, `${formatHexWord(parseInt(mapMatch[3], 16))}-${formatHexWord(parseInt(mapMatch[4], 16))}`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const excMatch = message.match(/^EXC slave=(\d+) fc=(\d+) code=(\d+) reason=(.*)$/);
    if (excMatch) {
      tone = 'error';
      kind = 'Exception';
      icon = '!';
      title = `Modbus exception code ${excMatch[3]}`;
      body = excMatch[4];
      chips = [`Slave ${excMatch[1]}`, `FC ${excMatch[2]}`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const rxMatch = message.match(/^RX (RTU|TCP) (.*)$/);
    if (rxMatch) {
      const bytes = parseWordList(rxMatch[2]);
      tone = 'request';
      kind = 'Inbound';
      icon = 'RX';
      title = `${rxMatch[1]} frame received`;
      body = summarizeWords(bytes);
      chips = [`${bytes.length} bytes`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const txMatch = message.match(/^TX ([^\s]+) (.*)$/);
    if (txMatch) {
      const bytes = parseWordList(txMatch[2]);
      tone = 'response';
      kind = 'Outbound';
      icon = 'TX';
      title = `${formatTransportLabel(txMatch[1])} response sent`;
      body = summarizeWords(bytes);
      chips = [`${bytes.length} bytes`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const crcMatch = message.match(/^CRC mode=([^\s]+) recv=(0x[0-9A-F]+) expected=(0x[0-9A-F]+)$/);
    if (crcMatch) {
      tone = 'meta';
      kind = 'CRC';
      icon = 'OK';
      title = `${formatTransportLabel(crcMatch[1])} CRC verified`;
      body = `Received ${crcMatch[2]} and expected ${crcMatch[3]}.`;
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const mbapMatch = message.match(/^MBAP txid=(0x[0-9A-F]+) proto=(\d+) len=(\d+) unit=(\d+)$/);
    if (mbapMatch) {
      tone = 'meta';
      kind = 'MBAP';
      icon = 'MB';
      title = `Modbus TCP header parsed`;
      body = `Transaction ${mbapMatch[1]} for unit ${mbapMatch[4]} with payload length ${mbapMatch[3]}.`;
      chips = [`Proto ${mbapMatch[2]}`];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const bufMatch = message.match(/^BUF mode=([^\s]+) len=(\d+)$/);
    if (bufMatch) {
      tone = 'buffer';
      kind = 'Buffer';
      icon = 'BF';
      title = `${formatTransportLabel(bufMatch[1])} buffer updated`;
      body = `${bufMatch[2]} bytes currently waiting in the parser buffer.`;
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const waitMatch = message.match(/^BUF waiting for complete (.+) frame$/);
    if (waitMatch) {
      tone = 'buffer';
      kind = 'Buffer';
      icon = 'BF';
      title = `Waiting for more payload`;
      body = `The ${formatTransportLabel(waitMatch[1])} frame is not complete yet.`;
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const trailingMatch = message.match(/^BUF trailing=(\d+) bytes after frame extraction$/);
    if (trailingMatch) {
      tone = 'buffer';
      kind = 'Buffer';
      icon = 'BF';
      title = `Trailing bytes remain after parsing`;
      body = `${trailingMatch[1]} bytes are still buffered for the next frame.`;
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const ignMatch = message.match(/^IGN wrong slave id (\d+)$/);
    if (ignMatch) {
      tone = 'error';
      kind = 'Ignored';
      icon = 'IG';
      title = `Frame ignored for another slave`;
      body = `The request targeted slave ${ignMatch[1]}, so it was ignored.`;
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    const errMatch = message.match(/^ERR (.*)$/);
    if (errMatch) {
      tone = 'error';
      kind = 'Issue';
      icon = '!';
      title = errMatch[1];
      return { timestamp, tone, kind, icon, title, body, chips };
    }

    return { timestamp, tone, kind, icon, title, body, chips };
  });
}

function renderLogFeed(targetId, entries, emptyText) {
  const container = byId(targetId);
  if (!container) {
    return;
  }

  if (!entries.length) {
    container.innerHTML = `<div class="log-empty">${escapeHtml(emptyText)}</div>`;
    return;
  }

  container.innerHTML = entries.map((entry) => {
    const chips = entry.chips.map((chip) => `<span class="log-chip">${escapeHtml(chip)}</span>`).join('');
    const body = entry.body ? `<div class="log-body">${escapeHtml(entry.body)}</div>` : '';
    return `
      <article class="log-entry ${entry.tone}">
        <div class="log-entry-head">
          <div class="log-entry-main">
            <div class="log-timestamp">${escapeHtml(entry.timestamp)}</div>
            <div class="log-title">${escapeHtml(entry.title)}</div>
          </div>
          <span class="log-kind kind-${entry.tone}">${escapeHtml(entry.icon)} ${escapeHtml(entry.kind)}</span>
        </div>
        ${body}
        ${chips ? `<div class="log-meta">${chips}</div>` : ''}
      </article>`;
  }).join('');
}

function buildDecodedRequestEntries(logLines) {
  const decoded = [];
  let pendingRequest = null;

  for (let index = logLines.length - 1; index >= 0; index -= 1) {
    const line = logLines[index];
    const mapMatch = line.match(/^(\d{2}:\d{2}:\d{2})\s+MAP slave=(\d+) fc=(\d+) addr=0x([0-9A-F]+)-0x([0-9A-F]+) words=(.*)$/);
    if (mapMatch) {
      if (
        pendingRequest &&
        pendingRequest.slave === Number(mapMatch[2]) &&
        pendingRequest.functionCode === Number(mapMatch[3]) &&
        pendingRequest.startAddr === parseInt(mapMatch[4], 16) &&
        pendingRequest.endAddr === parseInt(mapMatch[5], 16)
      ) {
        const words = parseWordList(mapMatch[6]);
        const nonZeroWords = countNonZeroWords(words);
        pendingRequest.responseSummary = `${words.length} regs returned, ${nonZeroWords} non-zero`;
        pendingRequest.wordsPreview = summarizeWords(words);
        pendingRequest.tone = words.length ? 'response' : 'meta';
        pendingRequest = null;
      }
      continue;
    }

    const excMatch = line.match(/^(\d{2}:\d{2}:\d{2})\s+EXC slave=(\d+) fc=(\d+) code=(\d+) reason=(.*)$/);
    if (excMatch && pendingRequest && pendingRequest.slave === Number(excMatch[2]) && pendingRequest.functionCode === Number(excMatch[3])) {
      pendingRequest.responseSummary = `Exception code ${excMatch[4]}`;
      pendingRequest.wordsPreview = excMatch[5];
      pendingRequest.tone = 'error';
      pendingRequest = null;
      continue;
    }

    const decMatch = line.match(/^(\d{2}:\d{2}:\d{2})\s+DEC mode=([^\s]+) slave=(\d+) fc=(\d+) start=0x([0-9A-F]+) qty=(\d+)$/);
    if (!decMatch) {
      continue;
    }

    const timestamp = decMatch[1];
    const transport = decMatch[2];
    const slave = Number(decMatch[3]);
    const functionCode = Number(decMatch[4]);
    const startAddr = parseInt(decMatch[5], 16);
    const quantity = Number(decMatch[6]);
    const endAddr = startAddr + quantity - 1;

    const entry = {
      timestamp,
      tone: 'request',
      slave,
      functionCode,
      startAddr,
      endAddr,
      transport,
      quantity,
      description: describeRegisterRange(startAddr, quantity),
      responseSummary: 'Response pending',
      wordsPreview: 'No mapped response seen yet'
    };

    pendingRequest = entry;
    decoded.push(entry);
  }

  return decoded.slice(-20).reverse();
}

function renderDecodedRequestFeed(targetId, entries) {
  const container = byId(targetId);
  if (!container) {
    return;
  }

  if (!entries.length) {
    container.innerHTML = '<div class="log-empty">Waiting for decoded Modbus traffic...</div>';
    return;
  }

  container.innerHTML = entries.map((entry) => `
    <article class="decoded-entry ${entry.tone}">
      <div class="decoded-entry-head">
        <div class="decoded-title">
          <div class="decoded-subtitle">${escapeHtml(entry.timestamp)} · ${escapeHtml(formatTransportLabel(entry.transport))}</div>
          <div class="decoded-title-text">Read ${escapeHtml(entry.description)}</div>
        </div>
        <span class="log-kind kind-${entry.tone}">${entry.tone === 'error' ? '!' : entry.tone === 'response' ? 'TX' : 'RX'} ${entry.tone === 'error' ? 'Issue' : entry.tone === 'response' ? 'Response' : 'Request'}</span>
      </div>
      <div class="decoded-summary">${escapeHtml(entry.wordsPreview)}</div>
      <div class="decoded-grid">
        <div class="decoded-stat">
          <div class="decoded-stat-label">Address range</div>
          <div class="decoded-stat-value">${escapeHtml(formatHexWord(entry.startAddr))}-${escapeHtml(formatHexWord(entry.endAddr))}</div>
        </div>
        <div class="decoded-stat">
          <div class="decoded-stat-label">Request</div>
          <div class="decoded-stat-value">Slave ${escapeHtml(entry.slave)} · FC ${escapeHtml(entry.functionCode)} · Qty ${escapeHtml(entry.quantity)}</div>
        </div>
        <div class="decoded-stat">
          <div class="decoded-stat-label">Response state</div>
          <div class="decoded-stat-value">${escapeHtml(entry.responseSummary)}</div>
        </div>
        <div class="decoded-stat">
          <div class="decoded-stat-label">Transport</div>
          <div class="decoded-stat-value">${escapeHtml(formatTransportLabel(entry.transport))}</div>
        </div>
      </div>
    </article>`).join('');
}

function setBadge(id, text, tone) {
  const badge = byId(id);
  if (!badge) {
    return;
  }
  badge.className = `badge ${tone}`;
  badge.innerHTML = `<span class="badge-dot"></span><span>${text}</span>`;
}

function formatConnectionSummary(stats) {
  if (stats.tcp_connected) {
    return 'Client connected';
  }
  if (stats.tcp_connects > 0) {
    return 'Waiting for reconnect';
  }
  return 'Idle';
}

function formatLastRequest(stats) {
  if (stats.last_fc === '-' || stats.last_start_addr === '-') {
    return 'No decoded frame yet';
  }
  return `FC ${stats.last_fc} / ${stats.last_start_addr} / ${stats.last_quantity}`;
}

function formatSessionSnapshot(stats) {
  if (stats.tcp_connected) {
    return `Connected since ${stats.last_connect}`;
  }
  if (stats.last_disconnect && stats.last_disconnect !== '-') {
    return `Last disconnect ${stats.last_disconnect}`;
  }
  return 'Waiting';
}

function updateRefreshWidgets() {
  setText('refresh_state', autoRefreshEnabled ? 'Live every 1s' : 'Paused');
  setText('refresh_toggle_button', autoRefreshEnabled ? 'Pause' : 'Resume');
}

async function refreshData() {
  if (!autoRefreshEnabled) {
    return;
  }

  try {
    const response = await fetch(appEndpoint('apiState'));
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const data = await response.json();
    const values = data.values;
    const stats = data.stats;

    setText('u1', `${values.u1.toFixed(1)} V`);
    setText('u2', `${values.u2.toFixed(1)} V`);
    setText('u3', `${values.u3.toFixed(1)} V`);
    setText('i1', `${values.i1.toFixed(2)} A`);
    setText('i2', `${values.i2.toFixed(2)} A`);
    setText('i3', `${values.i3.toFixed(2)} A`);
    setText('p_total', `${values.p_total.toFixed(0)} W`);
    setText('freq', `${values.freq.toFixed(2)} Hz`);
    setText('p_phases', `${values.p1.toFixed(0)} / ${values.p2.toFixed(0)} / ${values.p3.toFixed(0)} W`);
    setText('eimp', `${values.e_import_total.toFixed(3)}`);
    setText('eexp', `${values.e_export_total.toFixed(3)}`);

    const connectionTone = stats.tcp_connected ? 'good' : (stats.tcp_connects > 0 ? 'warn' : 'neutral');
    const reachabilityTone = stats.transport_reachability_code === 'valid_modbus_seen'
      ? 'good'
      : (stats.transport_reachability_code === 'payload_seen' || stats.transport_reachability_code === 'connected_no_payload' ? 'warn' : 'neutral');

    setText('tcp_connected', stats.tcp_connected ? 'Connected' : 'Disconnected');
    setText('transport_mode', stats.transport_mode);
    setText('hero_transport_mode', stats.transport_mode);
    setText('float_word_order', stats.float_word_order);
    setText('compatibility_profile', stats.compatibility_profile);
    setText('transport_reachability', stats.transport_reachability);
    setText('last_connect', stats.last_connect);
    setText('last_disconnect', stats.last_disconnect);
    setText('register_alias_mode', stats.register_alias_mode);
    setText('tcp_accept_errors', stats.tcp_accept_errors);
    setText('rx_frames', stats.rx_frames);
    setText('tx_frames', stats.tx_frames);
    setText('crc_fail', stats.crc_fail);
    setText('wrong_slave', stats.wrong_slave);
    setText('short_frames', stats.short_frames);
    setText('illegal_quantity', stats.illegal_quantity);
    setText('unsupported_fc', stats.unsupported_fc);
    setText('bytes_flow', `${stats.bytes_rx} / ${stats.bytes_tx}`);
    setText('last_fc', stats.last_fc);
    setText('last_addr_qty', `${stats.last_start_addr} / ${stats.last_quantity}`);
    setText('last_crc', `${stats.last_crc_received} / ${stats.last_crc_expected}`);
    setText('last_transaction_id', stats.last_transaction_id);
    setText('last_exception', stats.last_exception);
    setText('last_buffer_len', stats.last_buffer_len);

    setText('hero_connection_text', formatConnectionSummary(stats));
    setText('hero_reachability_text', stats.transport_reachability);
    setText('hero_last_request', formatLastRequest(stats));
    setText('session_snapshot', formatSessionSnapshot(stats));
    setText('last_refresh', new Date().toLocaleTimeString());

    setBadge('hero_connection_badge', stats.tcp_connected ? 'Session live' : formatConnectionSummary(stats), connectionTone);
    setBadge('hero_profile_badge', `Profile: ${stats.compatibility_profile}`, 'neutral');
    setBadge('hero_reachability_badge', stats.transport_reachability, reachabilityTone);

    const offsetOverride = stats.power_offset_override;
    const entityOffsetWatts = (data.values && data.values.power_offset) || 0;
    const effectiveOffset = offsetOverride !== null && offsetOverride !== undefined ? offsetOverride : entityOffsetWatts;
    const offsetSource = (offsetOverride !== null && offsetOverride !== undefined) ? 'Override' : 'Entity';
    setBadge('offset_active_badge', `${offsetSource}: ${effectiveOffset >= 0 ? '+' : ''}${effectiveOffset} W`, effectiveOffset !== 0 ? 'warn' : 'neutral');
    const offsetInput = byId('power_offset_input');
    if (offsetInput && document.activeElement !== offsetInput) {
      offsetInput.value = (offsetOverride !== null && offsetOverride !== undefined) ? offsetOverride : '';
    }

    const currentOrder = stats.phase_order || '1,2,3';
    syncPhaseButtons(currentOrder);
    setBadge('phase_order_badge', currentOrder, currentOrder !== '1,2,3' ? 'warn' : 'neutral');

    renderOutputTable(data.output);
    renderDecodedRequestFeed('modbus_decoded_log', buildDecodedRequestEntries(data.modbus_log));
    renderLogFeed('modbus_log', buildRawModbusEntries(data.modbus_log), 'Waiting for Modbus trace data...');
    setText('net_log', data.net_log.join('\n'));
    setText('tcp_raw_log', data.tcp_raw_log.join('\n'));
  } catch (error) {
    setText('session_snapshot', 'API error');
    setText('last_refresh', 'Update failed');
    setBadge('hero_connection_badge', 'Dashboard update failed', 'bad');
    setText('net_log', `Dashboard refresh failed: ${error.message}`);
  }
}

function renderOutputTable(output) {
  const tbody = byId('output_table_body');
  if (!tbody || !output) {
    return;
  }
  tbody.innerHTML = OUTPUT_REGISTERS.map((reg) => {
    if (reg.group) {
      return `<tr class="out-group"><td colspan="4">${escapeHtml(reg.group)}</td></tr>`;
    }
    const val = output[reg.key];
    const formatted = val === undefined ? '—' : val.toFixed(reg.decimals);
    const negative = val !== undefined && val < 0;
    return `<tr>
      <td class="out-addr">${escapeHtml(reg.addr)}</td>
      <td>${escapeHtml(reg.label)}</td>
      <td class="out-val${negative ? ' negative' : ''}">${escapeHtml(formatted)}</td>
      <td class="out-unit">${escapeHtml(reg.unit)}</td>
    </tr>`;
  }).join('');
}

async function applyPhaseOrder(order) {
  const statusEl = byId('phase_order_status');
  try {
    const response = await fetch(appEndpoint('apiPhaseOrder'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ order }),
    });
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
    if (statusEl) {
      statusEl.textContent = `Phase order set to ${order}`;
      statusEl.className = 'offset-status small ok';
    }
    syncPhaseButtons(order);
    setBadge('phase_order_badge', order, order !== '1,2,3' ? 'warn' : 'neutral');
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.className = 'offset-status small err';
    }
  }
}

function syncPhaseButtons(order) {
  document.querySelectorAll('.phase-btn').forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.order === order);
  });
}

async function applyPowerOffset(watts) {
  const statusEl = byId('offset_status');
  try {
    const response = await fetch(appEndpoint('apiPowerOffset'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ watts }),
    });
    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }
    if (statusEl) {
      if (watts === null) {
        statusEl.textContent = 'Override cleared — using HA entity value';
      } else {
        statusEl.textContent = `Override set to ${watts >= 0 ? '+' : ''}${watts} W`;
      }
      statusEl.className = 'offset-status small ok';
    }
  } catch (error) {
    if (statusEl) {
      statusEl.textContent = `Error: ${error.message}`;
      statusEl.className = 'offset-status small err';
    }
  }
}

function initializeControls() {
  const refreshToggle = byId('refresh_toggle_button');
  if (refreshToggle) {
    refreshToggle.addEventListener('click', async () => {
      autoRefreshEnabled = !autoRefreshEnabled;
      updateRefreshWidgets();
      if (autoRefreshEnabled) {
        await refreshData();
      }
    });
  }

  const applyBtn = byId('power_offset_apply');
  if (applyBtn) {
    applyBtn.addEventListener('click', async () => {
      const input = byId('power_offset_input');
      const watts = input ? parseFloat(input.value) || 0 : 0;
      await applyPowerOffset(watts);
    });
  }

  const clearBtn = byId('power_offset_clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      const input = byId('power_offset_input');
      if (input) {
        input.value = '';
      }
      await applyPowerOffset(null);
    });
  }

  document.querySelectorAll('.phase-btn').forEach((btn) => {
    btn.addEventListener('click', async () => {
      await applyPhaseOrder(btn.dataset.order);
    });
  });
}

initializeControls();
updateRefreshWidgets();
setInterval(refreshData, 1000);
refreshData();