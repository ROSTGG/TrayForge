let currentFile = null;

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('gerber-file');
const fileNameDisplay = document.getElementById('file-name-display');
const btnPreview = document.getElementById('btn-preview');
const btnExport = document.getElementById('btn-export');
const loader = document.getElementById('loader');
const previewSvg = document.getElementById('preview-svg');

// Drag & drop обработчики
dropzone.addEventListener('click', () => fileInput.click());

dropzone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) {
    handleFile(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener('change', () => {
  if (fileInput.files.length > 0) {
    handleFile(fileInput.files[0]);
  }
});

function handleFile(file) {
  currentFile = file;
  fileNameDisplay.textContent = file.name;
  loadPreview();
}

function getFormData() {
  const data = new FormData();
  if (currentFile) data.append('file', currentFile);
  data.append('thickness', document.getElementById('thickness').value);
  data.append('margin', document.getElementById('margin').value);
  data.append('pad_shrink', document.getElementById('pad-shrink').value);
  data.append('min_feature', document.getElementById('min-feature').value);
  data.append('mirror_x', document.getElementById('mirror-x').checked);
  data.append('add_frame', document.getElementById('add-frame').checked);
  data.append('frame_height', document.getElementById('frame-height').value);
  data.append('frame_width', document.getElementById('frame-width').value);
  return data;
}

async function loadPreview() {
  if (!currentFile) return;

  loader.classList.remove('hidden');
  try {
    const res = await fetch('/api/preview', {
      method: 'POST',
      body: getFormData()
    });

    if (!res.ok) throw new Error('Ошибка генерации превью');

    const data = await res.json();

    // Отрисовка SVG превью
    previewSvg.innerHTML = data.svg_content;
    if (data.view_box) {
      previewSvg.setAttribute('viewBox', data.view_box);
    }

    // Обновление метрик
    document.getElementById('metric-pcb').textContent = `${data.pcb_w} × ${data.pcb_h} мм`;
    document.getElementById('metric-stencil').textContent = `${data.stencil_w} × ${data.stencil_h} мм`;
    document.getElementById('metric-count').textContent = data.aperture_count;
  } catch (err) {
    alert(err.message);
  } finally {
    loader.classList.add('hidden');
  }
}

async function exportSTL() {
  if (!currentFile) {
    alert('Сначала загрузите Gerber-файл');
    return;
  }

  loader.textContent = 'Генерация STL...';
  loader.classList.remove('hidden');

  try {
    const res = await fetch('/api/convert', {
      method: 'POST',
      body: getFormData()
    });

    if (!res.ok) throw new Error('Ошибка создания STL');

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = currentFile.name.replace(/\.[^/.]+$/, "") + "_stencil.stl";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert(err.message);
  } finally {
    loader.textContent = 'Обработка Gerber...';
    loader.classList.add('hidden');
  }
}

btnPreview.addEventListener('click', loadPreview);
btnExport.addEventListener('click', exportSTL);