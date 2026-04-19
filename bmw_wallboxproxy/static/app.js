var transportModeOptions = [];
var transportModeDirty = false;
var transportModeApplying = false;
var floatWordOrderOptions = [];
var floatWordOrderDirty = false;
var floatWordOrderApplying = false;
var registerAliasModeOptions = [];
var registerAliasModeDirty = false;
var registerAliasModeApplying = false;
var compatibilityProfileOptions = [];
var compatibilityProfileDirty = false;
var compatibilityProfileApplying = false;
var haLiveDataDirty = false;
var haLiveDataApplying = false;
var autoRefreshEnabled = true;
var haLiveDataAutosaveTimer = null;

const HA_AUTOSAVE_DELAY_MS = 900;

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
  const relativePath = String(path).replace(/^\//, '');
  const basePath = `${window.location.pathname.replace(/\/?$/, '/')}`;
  return `${basePath}${relativePath}`;
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

function bindIfPresent(id, eventName, handler) {
  const element = byId(id);
  if (element) {
    element.addEventListener(eventName, handler);
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

function updateTransportModeSelect(settings, stats) {
  const select = byId('transport_mode_select');
  if (!select) {
    return;
  }

  const current = settings?.transport_mode || stats.transport_mode;
  const options = settings?.transport_mode_options || transportModeOptions;

  if (options.length && JSON.stringify(options) !== JSON.stringify(transportModeOptions)) {
    transportModeOptions = options.slice();
    select.innerHTML = '';
    for (const mode of transportModeOptions) {
      const option = document.createElement('option');
      option.value = mode;
      option.textContent = mode;
      select.appendChild(option);
    }
  }

  if (current && !transportModeDirty && !transportModeApplying) {
    select.value = current;
  }
}

function updateSettingSelect(selectId, settingsKey, optionsKey, optionsStoreName, dirtyFlag, applyingFlag, settings, stats) {
  const select = byId(selectId);
  if (!select) {
    return;
  }

  const current = settings?.[settingsKey] || stats[settingsKey];
  const options = settings?.[optionsKey] || window[optionsStoreName];

  if (options.length && JSON.stringify(options) !== JSON.stringify(window[optionsStoreName])) {
    window[optionsStoreName] = options.slice();
    select.innerHTML = '';
    for (const value of window[optionsStoreName]) {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    }
  }

  if (current && !window[dirtyFlag] && !window[applyingFlag]) {
    select.value = current;
  }
}

function updateHaLiveDataSettings(settings) {
  const urlInput = byId('ha_url_input');
  const verifyTlsSelect = byId('ha_verify_tls_select');
  if (!settings) {
    return;
  }

  if (urlInput && verifyTlsSelect && !haLiveDataDirty && !haLiveDataApplying) {
    urlInput.value = settings.ha_url || '';
    verifyTlsSelect.value = settings.ha_verify_tls ? 'true' : 'false';
  }

  if (!haLiveDataDirty && !haLiveDataApplying) {
    const entities = settings.ha_entities || {};
    document.querySelectorAll('.ha-entity-input').forEach((input) => {
      const key = input.dataset.entityKey;
      if (key && Object.prototype.hasOwnProperty.call(entities, key)) {
        input.value = entities[key];
      }
    });
  }
}

function collectHaEntitySettings() {
  const entities = {};
  document.querySelectorAll('.ha-entity-input').forEach((input) => {
    const key = input.dataset.entityKey;
    if (key) {
      entities[key] = input.value.trim();
    }
  });
  return entities;
}

function updateRefreshWidgets() {
  setText('refresh_state', autoRefreshEnabled ? 'Live every 1s' : 'Paused');
  setText('refresh_toggle_button', autoRefreshEnabled ? 'Pause' : 'Resume');
}

async function refreshData() {
  if (!autoRefreshEnabled) {
    return;
  }

  const response = await fetch(appEndpoint('api/state'));
  const data = await response.json();
  const values = data.values;
  const stats = data.stats;

  updateTransportModeSelect(data.settings, stats);
  updateSettingSelect('compatibility_profile_select', 'compatibility_profile', 'compatibility_profile_options', 'compatibilityProfileOptions', 'compatibilityProfileDirty', 'compatibilityProfileApplying', data.settings, stats);
  updateSettingSelect('float_word_order_select', 'float_word_order', 'float_word_order_options', 'floatWordOrderOptions', 'floatWordOrderDirty', 'floatWordOrderApplying', data.settings, stats);
  updateSettingSelect('register_alias_mode_select', 'register_alias_mode', 'register_alias_mode_options', 'registerAliasModeOptions', 'registerAliasModeDirty', 'registerAliasModeApplying', data.settings, stats);
  updateHaLiveDataSettings(data.settings);

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

  renderDecodedRequestFeed('modbus_decoded_log', buildDecodedRequestEntries(data.modbus_log));
  renderLogFeed('modbus_log', buildRawModbusEntries(data.modbus_log), 'Waiting for Modbus trace data...');
  setText('net_log', data.net_log.join('\n'));
  setText('tcp_raw_log', data.tcp_raw_log.join('\n'));
}

async function applyTransportMode() {
  const select = byId('transport_mode_select');
  const note = byId('transport_mode_note');
  if (!select || !note) {
    return;
  }

  if (transportModeApplying) {
    return;
  }

  transportModeApplying = true;
  note.textContent = 'Saving transport mode...';

  try {
    const response = await fetch(appEndpoint('api/settings/transport-mode'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: select.value })
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'failed to update transport mode');
    }

    transportModeDirty = false;
    note.textContent = payload.changed
      ? `Transport mode saved as ${payload.transport_mode}. Waiting for TCP client reconnect.`
      : `Transport mode already set to ${payload.transport_mode}.`;
    await refreshData();
  } catch (error) {
    note.textContent = `Mode change failed: ${error.message}`;
  } finally {
    transportModeApplying = false;
  }
}

async function applyCompatibilitySetting(config) {
  const select = byId(config.selectId);
  const note = byId(config.noteId);
  if (!select || !note) {
    return;
  }

  if (window[config.applyingFlag]) {
    return;
  }

  window[config.applyingFlag] = true;
  note.textContent = `Saving ${config.label}...`;

  try {
    const response = await fetch(appEndpoint(config.endpoint), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ [config.bodyKey]: select.value })
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || `failed to update ${config.label}`);
    }

    window[config.dirtyFlag] = false;
    note.textContent = payload.changed ? `${config.label} set to ${payload[config.responseKey]}.` : `${config.label} already set to ${payload[config.responseKey]}.`;
    await refreshData();
  } catch (error) {
    note.textContent = `${config.label} change failed: ${error.message}`;
  } finally {
    window[config.applyingFlag] = false;
  }
}

async function applyCompatibilityProfile(profileName) {
  const note = byId('compatibility_note');
  if (!note) {
    return;
  }

  note.textContent = `Applying ${profileName}...`;

  try {
    const response = await fetch(appEndpoint('api/settings/compatibility-profile'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile: profileName })
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'failed to update compatibility profile');
    }

    compatibilityProfileDirty = false;
    note.textContent = payload.changed ? `Compatibility profile set to ${payload.compatibility_profile}.` : `Compatibility profile already set to ${payload.compatibility_profile}.`;
    await refreshData();
  } catch (error) {
    note.textContent = `Compatibility profile change failed: ${error.message}`;
  }
}

async function applyHaLiveDataSettings() {
  const note = byId('ha_live_data_note');
  const urlInput = byId('ha_url_input');
  const verifyTlsSelect = byId('ha_verify_tls_select');
  if (!note || haLiveDataApplying) {
    return;
  }

  haLiveDataApplying = true;
  note.textContent = 'Saving Home Assistant settings...';

  try {
    const response = await fetch(appEndpoint('api/settings/ha-live-data'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ha_url: urlInput ? urlInput.value.trim() : '',
        ha_verify_tls: verifyTlsSelect ? verifyTlsSelect.value === 'true' : false,
        entities: collectHaEntitySettings()
      })
    });
    const payload = await response.json();

    if (!response.ok || !payload.ok) {
      throw new Error(payload.error || 'failed to save Home Assistant source settings');
    }

    haLiveDataDirty = false;
    note.textContent = payload.changed
      ? `Home Assistant settings saved to ${payload.settings_store_path} (${payload.saved_entity_count} entity fields set).`
      : `Home Assistant settings were already up to date in ${payload.settings_store_path}.`;
    await refreshData();
  } catch (error) {
    note.textContent = `HA settings failed: ${error.message}`;
  } finally {
    haLiveDataApplying = false;
  }
}

function scheduleHaLiveDataAutosave() {
  haLiveDataDirty = true;
  const note = byId('ha_live_data_note');
  if (note && !haLiveDataApplying) {
    note.textContent = 'Changes detected. Autosaving...';
  }

  if (haLiveDataAutosaveTimer) {
    clearTimeout(haLiveDataAutosaveTimer);
  }

  haLiveDataAutosaveTimer = setTimeout(() => {
    haLiveDataAutosaveTimer = null;
    applyHaLiveDataSettings();
  }, HA_AUTOSAVE_DELAY_MS);
}

function initializeMenu() {
  const toggle = byId('menu_toggle');
  const panel = byId('site_nav_panel');
  if (!toggle || !panel) {
    return;
  }

  bindIfPresent('menu_toggle', 'click', () => {
    const open = !panel.classList.contains('open');
    panel.hidden = !open;
    panel.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 760) {
      panel.hidden = true;
      panel.classList.remove('open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

function initializeControls() {
  bindIfPresent('ha_url_input', 'input', () => {
    scheduleHaLiveDataAutosave();
  });
  bindIfPresent('ha_verify_tls_select', 'change', () => {
    scheduleHaLiveDataAutosave();
  });
  document.querySelectorAll('.ha-entity-input').forEach((input) => {
    input.addEventListener('input', () => {
      scheduleHaLiveDataAutosave();
    });
    input.addEventListener('change', () => {
      scheduleHaLiveDataAutosave();
    });
  });

  bindIfPresent('transport_mode_select', 'change', () => {
    transportModeDirty = true;
    applyTransportMode();
  });

  bindIfPresent('compatibility_profile_select', 'change', () => {
    compatibilityProfileDirty = true;
    applyCompatibilitySetting({
      selectId: 'compatibility_profile_select',
      noteId: 'compatibility_note',
      endpoint: 'api/settings/compatibility-profile',
      bodyKey: 'profile',
      dirtyFlag: 'compatibilityProfileDirty',
      applyingFlag: 'compatibilityProfileApplying',
      responseKey: 'compatibility_profile',
      label: 'Compatibility profile'
    });
  });

  bindIfPresent('float_word_order_select', 'change', () => {
    floatWordOrderDirty = true;
    applyCompatibilitySetting({
      selectId: 'float_word_order_select',
      noteId: 'compatibility_note',
      endpoint: 'api/settings/float-word-order',
      bodyKey: 'word_order',
      dirtyFlag: 'floatWordOrderDirty',
      applyingFlag: 'floatWordOrderApplying',
      responseKey: 'float_word_order',
      label: 'Float word order'
    });
  });

  bindIfPresent('register_alias_mode_select', 'change', () => {
    registerAliasModeDirty = true;
    applyCompatibilitySetting({
      selectId: 'register_alias_mode_select',
      noteId: 'compatibility_note',
      endpoint: 'api/settings/register-alias-mode',
      bodyKey: 'alias_mode',
      dirtyFlag: 'registerAliasModeDirty',
      applyingFlag: 'registerAliasModeApplying',
      responseKey: 'register_alias_mode',
      label: 'Register alias mode'
    });
  });

  bindIfPresent('quick_profile_rtu', 'click', () => applyCompatibilityProfile('pro380-default'));
  bindIfPresent('quick_profile_tcp', 'click', () => applyCompatibilityProfile('gateway-modbus-tcp'));
  bindIfPresent('refresh_toggle_button', 'click', async () => {
    autoRefreshEnabled = !autoRefreshEnabled;
    updateRefreshWidgets();
    if (autoRefreshEnabled) {
      await refreshData();
    }
  });
}

initializeMenu();
initializeControls();
updateRefreshWidgets();
setInterval(refreshData, 1000);
refreshData();