'use strict';

(() => {
  const byId = (id) => document.getElementById(id);
  const form = byId('download-form');
  const fields = byId('download-fields');
  const urlInput = byId('url');
  const submitButton = byId('submit-btn');
  const panel = byId('status-panel');
  const videoFormat = byId('video-format');
  const audioFormat = byId('audio-format');
  const retryButton = byId('retry-status');
  const stages = document.querySelectorAll('[data-step]');
  const states = {
    pending: { title: '正在準備你的下載', badge: '準備中', icon: 'download', step: 0 },
    downloading: { title: '精彩內容，正在路上', badge: '下載中', icon: 'download', step: 1 },
    postprocessing: { title: '即將完成，正在處理檔案', badge: '處理中', icon: 'refresh', step: 2 },
    completed: { title: '下載完成，隨時可以播放', badge: '已完成', icon: 'check', step: 3 },
    failed: { title: '這次下載沒有完成', badge: '下載失敗', icon: 'alert', step: -1 },
    disconnected: { title: '暫時無法取得下載狀態', badge: '連線中斷', icon: 'alert', step: -1 },
  };
  let busy = false;
  let taskId = null;
  let pollTimer = null;
  let pollFailures = 0;
  let lastProgress = 0;
  let toastTimer = null;

  // JavaScript supplies inline validation; native validation remains available without it.
  form.noValidate = true;

  function syncFormat() {
    const isVideo = byId('type-video').checked;
    byId('video-format-group').hidden = !isVideo;
    byId('audio-format-group').hidden = isVideo;
    videoFormat.disabled = !isVideo;
    audioFormat.disabled = isVideo;
  }
  document.querySelectorAll('input[name="download_type"]').forEach((radio) => {
    radio.addEventListener('change', syncFormat);
  });
  syncFormat();

  function setBusy(value, label = '下載進行中…') {
    busy = value;
    fields.disabled = value;
    submitButton.disabled = value;
    byId('submit-label').textContent = value ? label : '開始下載';
    form.setAttribute('aria-busy', String(value));
  }

  function setProgress(value) {
    const number = Number(value);
    lastProgress = Number.isFinite(number) ? Math.max(0, Math.min(100, number)) : 0;
    const percentage = Number(lastProgress.toFixed(1));
    byId('progress-bar').style.width = `${percentage}%`;
    byId('progress-track').setAttribute('aria-valuenow', String(percentage));
    byId('progress-value').replaceChildren(document.createTextNode(String(percentage)));
    const unit = document.createElement('span');
    unit.textContent = '%';
    byId('progress-value').append(unit);
  }

  function showState(state, message, progress = lastProgress) {
    const meta = states[state] || states.pending;
    panel.dataset.state = state;
    byId('status-badge').textContent = meta.badge;
    byId('status-title').textContent = meta.title;
    byId('status-message').textContent = message;
    byId('status-icon').setAttribute('href', `#icon-${meta.icon}`);
    byId('progress-label').textContent = state === 'postprocessing' ? '下載完成，正在處理' : '下載進度';
    setProgress(progress);
    stages.forEach((stage) => {
      const index = Number(stage.dataset.step);
      stage.classList.toggle('is-current', index === meta.step);
      stage.classList.toggle('is-done', index < meta.step);
      if (index === meta.step) stage.setAttribute('aria-current', 'step');
      else stage.removeAttribute('aria-current');
    });
  }

  function showError(message) {
    byId('error-message').textContent = message;
    byId('error-details').hidden = false;
  }

  function renderStatus(data) {
    const complete = data.status === 'completed';
    const failed = data.status === 'failed';
    const downloading = data.status === 'downloading';
    let message = data.message || '正在取得下載資訊…';
    if (complete) message = data.file_path ? '檔案已儲存，讓喜歡的內容隨時陪伴你。' : '任務已完成，請至儲存目錄確認檔案。';
    if (failed) message = '請查看錯誤詳情，調整連結或設定後再試一次。';
    if (data.status === 'postprocessing') message = '正在合併或轉換檔案，完成後會自動儲存。';
    showState(data.status, message, complete ? 100 : data.progress);
    byId('download-speed').textContent = downloading && data.speed ? data.speed : '—';
    byId('download-eta').textContent = downloading && data.eta ? data.eta : '—';
    byId('download-metrics').hidden = complete || failed;
    byId('error-details').hidden = !failed;
    retryButton.hidden = true;
    if (failed) showError(data.message || '下載過程發生錯誤，請稍後再試。');
    byId('file-result').hidden = !(complete && data.file_path);
    byId('status-footnote').hidden = complete || failed;
    if (complete && data.file_path) {
      const path = String(data.file_path);
      // File names and server messages are always text, never HTML.
      byId('file-name').textContent = path.split(/[\\/]/).pop() || path;
      byId('file-path').textContent = path;
    }
  }

  async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      // Read the body before clearing the timeout, including slow/stalled responses.
      const body = await response.text();
      let data = null;
      try { data = JSON.parse(body); } catch { /* Non-JSON errors get a readable fallback. */ }
      return { response, data };
    } finally {
      clearTimeout(timeout);
    }
  }

  function errorMessage(data, fallback) {
    if (typeof data?.detail === 'string') return data.detail;
    if (Array.isArray(data?.detail)) return data.detail.map((error) => error.msg).filter(Boolean).join('；') || fallback;
    return fallback;
  }

  async function pollStatus() {
    clearTimeout(pollTimer);
    retryButton.hidden = true;
    try {
      const { response, data } = await fetchWithTimeout(`/api/status/${encodeURIComponent(taskId)}`, { cache: 'no-store' });
      if (response.status === 404) {
        showState('failed', '找不到這筆任務，服務可能已重新啟動。請先檢查儲存目錄再重新下載。');
        byId('download-metrics').hidden = true;
        setBusy(false);
        taskId = null;
        return;
      }
      if (!response.ok || !data || !states[data.status]) throw new Error('無法取得任務狀態');
      pollFailures = 0;
      renderStatus(data);
      if (['completed', 'failed'].includes(data.status)) {
        setBusy(false);
        byId('submit-label').textContent = data.status === 'completed' ? '下載下一個' : '重新下載';
        taskId = null;
        return;
      }
      // Schedule only after this response settles to avoid overlapping requests.
      pollTimer = setTimeout(pollStatus, 1200);
    } catch {
      pollFailures += 1;
      byId('download-speed').textContent = '—';
      byId('download-eta').textContent = '—';
      showState('disconnected', pollFailures < 3
        ? '下載可能仍在進行，正在嘗試恢復連線…'
        : '下載可能仍在進行。請重新連線以確認結果。');
      if (pollFailures < 3) pollTimer = setTimeout(pollStatus, 2400);
      else retryButton.hidden = false;
      // Keep the form locked: a status request failure does not cancel the download.
    }
  }

  retryButton.addEventListener('click', () => {
    if (!taskId) return;
    pollFailures = 0;
    showState('pending', '正在重新連線，確認下載狀態…');
    void pollStatus();
  });

  urlInput.addEventListener('input', () => {
    urlInput.removeAttribute('aria-invalid');
    byId('url-error').hidden = true;
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy) return;
    const url = urlInput.value.trim();
    try {
      const parsed = new URL(url);
      if (!['https:', 'http:'].includes(parsed.protocol) || !parsed.hostname) throw new Error('invalid');
    } catch {
      byId('url-error').textContent = '請輸入有效的 http:// 或 https:// 影片連結。';
      byId('url-error').hidden = false;
      urlInput.setAttribute('aria-invalid', 'true');
      urlInput.focus();
      return;
    }
    const downloadType = byId('type-video').checked ? 'video' : 'audio';
    const formatOption = downloadType === 'video' ? videoFormat.value : audioFormat.value;
    clearTimeout(pollTimer);
    pollFailures = 0;
    taskId = null;
    byId('error-details').hidden = true;
    byId('error-details').open = false;
    byId('file-result').hidden = true;
    byId('file-result').querySelector('details').open = false;
    byId('file-path').textContent = '';
    byId('file-name').textContent = '';
    retryButton.hidden = true;
    byId('download-metrics').hidden = false;
    byId('download-speed').textContent = '—';
    byId('download-eta').textContent = '—';
    byId('status-footnote').hidden = false;
    byId('task-summary').hidden = false;
    byId('task-source').textContent = new URL(url).hostname;
    byId('task-source').title = url;
    byId('task-format').textContent = `${downloadType === 'video' ? '影片' : '音訊'} · ${formatOption}`;
    setBusy(true, '正在建立下載…');
    showState('pending', '正在送出下載請求…', 0);
    if (window.matchMedia('(max-width: 800px)').matches) {
      panel.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
    }
    try {
      const { response, data } = await fetchWithTimeout('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, download_type: downloadType, format_option: formatOption }),
      });
      if (!response.ok) throw new Error(errorMessage(data, `建立任務失敗（${response.status}），請稍後再試。`));
      if (!data || typeof data.task_id !== 'string' || !data.task_id) throw new Error('未取得任務編號。請先檢查儲存目錄，再重新嘗試。');
      taskId = data.task_id;
      setBusy(true);
      await pollStatus();
    } catch (error) {
      showState('failed', '無法確認下載是否建立，請查看詳情後再試。', 0);
      showError(error.name === 'AbortError' || error instanceof TypeError
        ? '連線逾時或中斷。任務可能已建立，請先檢查儲存目錄，避免重複下載。'
        : error.message);
      byId('download-metrics').hidden = true;
      setBusy(false);
    }
  });

  function toast(message) {
    clearTimeout(toastTimer);
    byId('toast').textContent = message;
    byId('toast').hidden = false;
    toastTimer = setTimeout(() => { byId('toast').hidden = true; }, 4500);
  }

  async function copyPath(element, successMessage) {
    if (!element.textContent.trim()) return;
    try {
      await navigator.clipboard.writeText(element.textContent.trim());
      toast(successMessage);
    } catch {
      const details = element.closest('details');
      if (details) details.open = true;
      const range = document.createRange();
      range.selectNodeContents(element);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      toast('瀏覽器無法自動複製。已選取路徑，請手動複製。');
    }
  }
  byId('copy-directory').addEventListener('click', () => { void copyPath(byId('download-directory'), '已複製儲存目錄'); });
  byId('copy-file').addEventListener('click', () => { void copyPath(byId('file-path'), '已複製檔案路徑'); });
})();
