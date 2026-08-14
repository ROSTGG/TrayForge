const form = document.querySelector('#converter');
const fileInput = document.querySelector('#file');
const dropzone = document.querySelector('#dropzone');
const fileLabel = document.querySelector('#file-label');
const preview = document.querySelector('#preview');
const message = document.querySelector('#message');
const submit = document.querySelector('#submit');

function showFile(file) {
  if (!file) return;
  fileLabel.textContent = file.name;
  dropzone.classList.add('has-file');
}

fileInput.addEventListener('change', () => showFile(fileInput.files[0]));
['dragenter', 'dragover'].forEach(event => dropzone.addEventListener(event, e => {
  e.preventDefault(); dropzone.classList.add('drag');
}));
['dragleave', 'drop'].forEach(event => dropzone.addEventListener(event, e => {
  e.preventDefault(); dropzone.classList.remove('drag');
}));
dropzone.addEventListener('drop', e => {
  if (!e.dataTransfer.files.length) return;
  const transfer = new DataTransfer();
  transfer.items.add(e.dataTransfer.files[0]);
  fileInput.files = transfer.files;
  showFile(fileInput.files[0]);
});

function setBusy(isBusy) {
  submit.disabled = isBusy;
  submit.querySelector('span').textContent = isBusy ? 'Строим геометрию…' : 'Построить трафарет';
  preview.classList.toggle('loading', isBusy);
}

function showError(text) {
  message.textContent = text;
  message.classList.remove('hidden');
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  message.classList.add('hidden');
  document.querySelector('#result-actions').classList.add('hidden');
  if (!fileInput.files.length) { showError('Выберите Gerber-файл.'); return; }
  setBusy(true);
  try {
    const response = await fetch('/api/convert', { method: 'POST', body: new FormData(form) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Не удалось построить трафарет.');

    preview.innerHTML = data.preview_svg;
    preview.classList.remove('empty');
    const r = data.report;
    document.querySelector('#size-metric').textContent = `${r.sheet_width_mm.toFixed(2)} × ${r.sheet_height_mm.toFixed(2)} × ${r.thickness_mm.toFixed(2)} мм`;
    document.querySelector('#openings-metric').textContent = `${r.opening_count} · ${r.opening_area_mm2.toFixed(1)} мм²`;
    document.querySelector('#mesh-metric').textContent = `${r.vertex_count} вершин`;
    document.querySelector('#water-metric').textContent = r.watertight ? 'ГЕРМЕТИЧЕН ✓' : 'НЕ ПРОЙДЕНА';
    document.querySelector('#metrics').classList.remove('hidden');
    document.querySelector('#download-stl').href = data.downloads.stl;
    document.querySelector('#download-json').href = data.downloads.report;
    document.querySelector('#download-svg').href = data.downloads.preview;
    document.querySelector('#result-actions').classList.remove('hidden');
    if (r.warnings?.length) showError(r.warnings.join(' '));
  } catch (error) {
    showError(error.message);
  } finally {
    setBusy(false);
  }
});
