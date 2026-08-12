/* ── Stencil Generator — Frontend ── */
const $ = id => document.getElementById(id);

const dropzone   = $('dropzone');
const fileInput  = $('gerber-file');
const fileInfo   = $('file-info');
const fileName   = $('file-name');
const btnClear   = $('btn-clear');
const btnPreview = $('btn-preview');
const btnDL      = $('btn-download');
const previewArea= $('preview-area');
const loader     = $('loader');
const loaderText = $('loader-text');

let currentFile = null;

/* ── Drag & Drop ── */
dropzone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

['dragenter','dragover'].forEach(ev =>
  dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('drag-over'); })
);
['dragleave','drop'].forEach(ev =>
  dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('drag-over'); })
);
dropzone.addEventListener('drop', e => {
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

function handleFile(file) {
  if (!file) return;
  currentFile = file;
  fileName.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  fileInfo.classList.remove('hidden');
  dropzone.style.display = 'none';
  btnPreview.disabled = false;
  btnDL.disabled = false;
}

btnClear.addEventListener('click', () => {
  currentFile = null;
  fileInput.value = '';
  fileInfo.classList.add('hidden');
  dropzone.style.display = '';
  btnPreview.disabled = true;
  btnDL.disabled = true;
  previewArea.innerHTML = '<p class="placeholder-text">Загрузите Gerber и нажмите «Предпросмотр»</p>';
  $('m-apertures').textContent = '—';
  $('m-sheet').textContent = '—';
  $('m-status').textContent = '—';
  $('warnings').classList.add('hidden');
});

/* ── Вспомогательные ── */
function showLoader(text) {
  loaderText.textContent = text;
  loader.classList.remove('hidden');
}
function hideLoader() {
  loader.classList.add('hidden');
}

function val(id) {
  const el = $(id);
  if (!el) return undefined;
  if (el.type === 'checkbox') return el.checked;
  const v = parseFloat(el.value);
  return isNaN(v) ? undefined : v;
}

function buildFormData() {
  const fd = new FormData();
  fd.append('file', currentFile);
  fd.append('thickness', val('thickness') || 0.12);
  fd.append('margin', val('margin') ?? 10);
  fd.append('corner_radius', val('corner-radius') ?? 2);
  fd.append('aperture_offset', val('aperture-offset') ?? 0);
  fd.append('arc_tolerance', val('arc-tolerance') || 0.01);
  fd.append('mirror_x', val('mirror-x') ? 'true' : 'false');
  fd.append('mirror_y', val('mirror-y') ? 'true' : 'false');
  fd.append('rotate', val('rotate') ?? 0);

  const sw = val('sheet-width');
  const sh = val('sheet-height');
  if (sw && sw > 0) fd.append('sheet_width', sw);
  if (sh && sh > 0) fd.append('sheet_height', sh);

  return fd;
}

/* ── Предпросмотр ── */
btnPreview.addEventListener('click', async () => {
  if (!currentFile) return;
  showLoader('Генерация предпросмотра…');

  try {
    const fd = new FormData();
    fd.append('file', currentFile);
    fd.append('arc_tolerance', val('arc-tolerance') || 0.01);

    const res = await fetch('api/preview', { method: 'POST', body: fd });
    const data = await res.json();

    if (data.error) {
      previewArea.innerHTML = `<p class="placeholder-text" style="color:#e06b6b">⚠ ${data.error}</p>`;
      $('m-status').textContent = 'Ошибка';
      $('m-status').style.color = '#e06b6b';
      return;
    }

    previewArea.innerHTML = data.svg;
    $('m-apertures').textContent = data.aperture_count;
    $('m-sheet').textContent = `${data.sheet_width} × ${data.sheet_height} мм`;
    $('m-status').textContent = '✓ Готово';
    $('m-status').style.color = '#6be0c8';

    if (data.warnings && data.warnings.length) {
      $('warnings').textContent = data.warnings.join('\n');
      $('warnings').classList.remove('hidden');
    } else {
      $('warnings').classList.add('hidden');
    }
  } catch (err) {
    previewArea.innerHTML = `<p class="placeholder-text" style="color:#e06b6b">Ошибка сети: ${err.message}</p>`;
    $('m-status').textContent = 'Ошибка';
  } finally {
    hideLoader();
  }
});

/* ── Скачать STL ── */
btnDL.addEventListener('click', async () => {
  if (!currentFile) return;
  showLoader('Генерация STL трафарета…');

  try {
    const fd = buildFormData();
    const res = await fetch('api/convert', { method: 'POST', body: fd });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Неизвестная ошибка' }));
      alert(`Ошибка: ${err.error}`);
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    const cd = res.headers.get('content-disposition');
    const match = cd && cd.match(/filename="?([^"]+)"?/);
    a.download = match ? match[1] : currentFile.name.replace(/\.[^.]+$/, '') + '-stencil.stl';

    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);

    // Показываем метаданные из заголовков
    const watertight = res.headers.get('X-Watertight');
    if (watertight === 'True') {
      $('m-status').textContent = '✓ Герметичный STL';
      $('m-status').style.color = '#6be0c8';
    }
  } catch (err) {
    alert(`Ошибка сети: ${err.message}`);
  } finally {
    hideLoader();
  }
});
