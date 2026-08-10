/* ── Встроенные пресеты ─────────────────────────────────────────────
   l, w, h  — габариты КОРПУСА
   ll       — выступ вывода за корпус по длине (на каждую сторону, мм)
   lw       — выступ вывода за корпус по ширине (на каждую сторону, мм)
   Если ll / lw не указаны — считаются равными 0 (безвыводный корпус).
   ──────────────────────────────────────────────────────────────────── */
const builtinPresets = {
  // ── Пассивные SMD (безвыводные) ──
  '0201': { category:'Пассивные SMD', name:'0201 (0.6 × 0.3)', l:0.6, w:0.3, h:0.3 },
  '0402': { category:'Пассивные SMD', name:'0402 (1.0 × 0.5)', l:1, w:0.5, h:0.55 },
  '0603': { category:'Пассивные SMD', name:'0603 (1.6 × 0.8)', l:1.6, w:0.8, h:0.6 },
  '0805': { category:'Пассивные SMD', name:'0805 (2.0 × 1.25)', l:2, w:1.25, h:0.7 },
  '1206': { category:'Пассивные SMD', name:'1206 (3.2 × 1.6)', l:3.2, w:1.6, h:0.8 },
  '1210': { category:'Пассивные SMD', name:'1210 (3.2 × 2.5)', l:3.2, w:2.5, h:0.8 },
  '1812': { category:'Пассивные SMD', name:'1812 (4.5 × 3.2)', l:4.5, w:3.2, h:1 },
  '2512': { category:'Пассивные SMD', name:'2512 (6.3 × 3.2)', l:6.3, w:3.2, h:0.9 },

  // ── Индуктивности и кварцы ──
  inductor2016:  { category:'Индуктивности и кварцы', name:'Индуктивность 2016', l:2, w:1.6, h:1.2 },
  inductor2520:  { category:'Индуктивности и кварцы', name:'Индуктивность 2520', l:2.5, w:2, h:1.5 },
  inductor3225:  { category:'Индуктивности и кварцы', name:'Индуктивность 3225', l:3.2, w:2.5, h:2 },
  inductor4532:  { category:'Индуктивности и кварцы', name:'Индуктивность 4532', l:4.5, w:3.2, h:2.5 },
  vls6045ex_3r3n:{ category:'Индуктивности и кварцы', name:'TDK VLS6045EX-3R3N', l:6, w:6, h:4.5 },
  crystal2016:   { category:'Индуктивности и кварцы', name:'Кварц 2016', l:2, w:1.6, h:0.6 },
  crystal2520:   { category:'Индуктивности и кварцы', name:'Кварц 2520', l:2.5, w:2, h:0.7 },
  crystal3225:   { category:'Индуктивности и кварцы', name:'Кварц 3225', l:3.2, w:2.5, h:0.8 },
  crystal4025:   { category:'Индуктивности и кварцы', name:'Кварц 4025', l:4, w:2.5, h:0.9 },
  crystal5032:   { category:'Индуктивности и кварцы', name:'Кварц 5032', l:5, w:3.2, h:1.1 },
  crystal7050:   { category:'Индуктивности и кварцы', name:'Кварц 7050', l:7, w:5, h:1.4 },
  hc49sm:        { category:'Индуктивности и кварцы', name:'HC-49SM / HC-49S-SMD', l:11.05, w:4.65, h:3.7, ll:1.2 },
  smd49s4:       { category:'Индуктивности и кварцы', name:'SMD49S4', l:11.1, w:4.7, h:4.2, ll:1.0 },

  // ── Транзисторы и регуляторы (выводы по ширине) ──
  sot23:   { category:'Транзисторы и регуляторы', name:'SOT-23', l:3, w:1.3, h:1.45, lw:0.55 },
  sot23_6: { category:'Транзисторы и регуляторы', name:'SOT-23-6', l:3, w:1.3, h:1.45, lw:0.55 },
  sot323:  { category:'Транзисторы и регуляторы', name:'SOT-323 / SC-70', l:2.2, w:1.3, h:1.1, lw:0.5 },
  sot353:  { category:'Транзисторы и регуляторы', name:'SOT-353 / SC-88', l:2.9, w:1.6, h:1.1, lw:0.5 },
  sot89:   { category:'Транзисторы и регуляторы', name:'SOT-89', l:4.5, w:2.5, h:1.6, lw:0.75 },
  sot223:  { category:'Транзисторы и регуляторы', name:'SOT-223', l:6.5, w:3.5, h:1.8, lw:1.5 },
  sot252:  { category:'Транзисторы и регуляторы', name:'SOT-252 / DPAK', l:6.6, w:6.1, h:2.3, lw:1.0 },
  sot263:  { category:'Транзисторы и регуляторы', name:'SOT-263 / D2PAK', l:10, w:9.8, h:4.8, lw:1.5 },

  // ── Диоды (выводы по длине) ──
  sod323: { category:'Диоды', name:'SOD-323', l:2.5, w:1.3, h:1.1, ll:0.4 },
  sod523: { category:'Диоды', name:'SOD-523', l:1.7, w:1.2, h:0.8, ll:0.3 },
  sod123: { category:'Диоды', name:'SOD-123', l:3.7, w:1.8, h:1.35, ll:0.6 },
  sod128: { category:'Диоды', name:'SOD-128', l:3.6, w:2.7, h:1.2, ll:0.4 },
  sma:    { category:'Диоды', name:'SMA / DO-214AC', l:4.6, w:2.9, h:2.4 },
  smb:    { category:'Диоды', name:'SMB / DO-214AA', l:5.4, w:3.6, h:2.7 },
  smc:    { category:'Диоды', name:'SMC / DO-214AB', l:7.9, w:6, h:3 },

  // ── Светодиоды (безвыводные) ──
  led0603: { category:'Светодиоды', name:'LED 0603', l:1.6, w:0.8, h:0.8 },
  led0805: { category:'Светодиоды', name:'LED 0805', l:2, w:1.25, h:1 },
  led1206: { category:'Светодиоды', name:'LED 1206', l:3.2, w:1.6, h:1.1 },
  led3528: { category:'Светодиоды', name:'LED 3528', l:3.5, w:2.8, h:1.9 },
  plcc2:   { category:'Светодиоды', name:'PLCC-2 / 3528', l:3.5, w:2.8, h:1.9 },
  plcc4:   { category:'Светодиоды', name:'PLCC-4 / 5050', l:5, w:5, h:1.6 },

  // ── Микросхемы с выводами (gull-wing по ширине) ──
  soic8:   { category:'Микросхемы с выводами', name:'SO-8 / SOIC-8', l:5, w:4, h:1.75, lw:1.0 },
  soic14:  { category:'Микросхемы с выводами', name:'SO-14 / SOIC-14', l:8.7, w:4, h:1.75, lw:1.0 },
  soic16:  { category:'Микросхемы с выводами', name:'SO-16 / SOIC-16', l:10.3, w:4, h:1.75, lw:1.0 },
  sop8:    { category:'Микросхемы с выводами', name:'SOP-8 (широкий)', l:6, w:5, h:1.75, lw:1.0 },
  sop16:   { category:'Микросхемы с выводами', name:'SOP-16 (широкий)', l:10, w:5, h:1.75, lw:1.0 },
  msop8:   { category:'Микросхемы с выводами', name:'MSOP-8', l:3, w:3, h:1.1, lw:0.5 },
  tssop8:  { category:'Микросхемы с выводами', name:'TSSOP-8', l:3, w:4.4, h:1.2, lw:0.5 },
  tssop14: { category:'Микросхемы с выводами', name:'TSSOP-14', l:5, w:4.4, h:1.2, lw:0.5 },
  tssop16: { category:'Микросхемы с выводами', name:'TSSOP-16', l:5, w:4.4, h:1.2, lw:0.5 },
  ssop20:  { category:'Микросхемы с выводами', name:'SSOP-20', l:7.2, w:5.3, h:1.8, lw:0.65 },
  ssop28:  { category:'Микросхемы с выводами', name:'SSOP-28', l:10.2, w:5.6, h:2, lw:0.65 },

  // ── Безвыводные микросхемы ──
  dfn6:   { category:'Безвыводные микросхемы', name:'DFN-6 (2 × 2)', l:2, w:2, h:0.8 },
  dfn8:   { category:'Безвыводные микросхемы', name:'DFN-8 (2 × 2)', l:2, w:2, h:0.8 },
  wson8:  { category:'Безвыводные микросхемы', name:'WSON-8 (3 × 3)', l:3, w:3, h:0.8 },
  lga16:  { category:'Безвыводные микросхемы', name:'LGA-16 (3 × 3)', l:3, w:3, h:0.9 },
  qfn16:  { category:'Безвыводные микросхемы', name:'QFN-16 (3 × 3)', l:3, w:3, h:0.9 },
  qfn20:  { category:'Безвыводные микросхемы', name:'QFN-20 (4 × 4)', l:4, w:4, h:0.9 },
  qfn32:  { category:'Безвыводные микросхемы', name:'QFN-32 (5 × 5)', l:5, w:5, h:0.9 },
  qfn48:  { category:'Безвыводные микросхемы', name:'QFN-48 (7 × 7)', l:7, w:7, h:0.9 },
  qfn64:  { category:'Безвыводные микросхемы', name:'QFN-64 (9 × 9)', l:9, w:9, h:1 },
  bga48:  { category:'Безвыводные микросхемы', name:'BGA-48 (6 × 6)', l:6, w:6, h:1.2 },
  bga64:  { category:'Безвыводные микросхемы', name:'BGA-64 (8 × 8)', l:8, w:8, h:1.2 },

  // ── Квадратные микросхемы (выводы на 4 стороны) ──
  qfp32:   { category:'Квадратные микросхемы', name:'LQFP-32 (7 × 7)', l:7, w:7, h:1.6, ll:1.5, lw:1.5 },
  qfp48:   { category:'Квадратные микросхемы', name:'LQFP-48 (7 × 7)', l:7, w:7, h:1.6, ll:1.5, lw:1.5 },
  qfp64:   { category:'Квадратные микросхемы', name:'LQFP-64 (10 × 10)', l:10, w:10, h:1.6, ll:1.5, lw:1.5 },
  qfp100:  { category:'Квадратные микросхемы', name:'LQFP-100 (14 × 14)', l:14, w:14, h:1.6, ll:1.5, lw:1.5 },
  tqfp144: { category:'Квадратные микросхемы', name:'TQFP-144 (20 × 20)', l:20, w:20, h:1.6, ll:1.5, lw:1.5 },

  // ── Свой размер ──
  custom: { category:'Свой размер', name:'Свой размер', l:10, w:4, h:1.8 }
};

/* ── Пользовательские пресеты из localStorage ── */
const STORAGE_KEY = 'trayforge_custom_presets';

function loadCustomPresets() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; }
  catch { return {}; }
}

function saveCustomPresets(custom) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(custom));
}

/* Объединяем встроенные + пользовательские */
let presets = {};
function mergePresets() {
  presets = {};
  Object.assign(presets, builtinPresets);
  const custom = loadCustomPresets();
  Object.assign(presets, custom);
}
mergePresets();

/* ── DOM ── */
const form = document.querySelector('#tray-form');
const get = id => document.querySelector(`#${id}`);

/* ── Заполнение <select> ── */
function rebuildSelect(selectValue) {
  const sel = get('preset');
  sel.innerHTML = '';
  const groups = {};
  Object.entries(presets).forEach(([id, p]) => (groups[p.category] ??= []).push([id, p]));
  Object.entries(groups).forEach(([name, items]) => {
    const group = document.createElement('optgroup');
    group.label = name;
    items.forEach(([id, p]) => group.append(new Option(p.name, id)));
    sel.add(group);
  });
  if (selectValue && presets[selectValue]) sel.value = selectValue;
  else sel.value = 'sot223';
  applyPreset();
}
rebuildSelect('sot223');

/* ── Вспомогательные ── */
function num(id) { return Math.max(0, Number(get(id).value) || 0); }
function numMin(id, min) { return Math.max(min, Number(get(id).value) || min); }

function values() {
  return {
    l:    numMin('partL', 0.1),
    w:    numMin('partW', 0.1),
    h:    numMin('partH', 0.1),
    ll:   num('leadL'),
    lw:   num('leadW'),
    cols:  Math.max(1, Math.round(num('cols'))),
    rows:  Math.max(1, Math.round(num('rows'))),
    clear: numMin('clearance', 0.05),
    div:   numMin('divider', 0.5),
    base:  numMin('base', 0.6),
    wallH: numMin('wallH', 1),
    wallT: numMin('wallT', 0.8),
    margin:num('margin'),
    vacuum:get('vacuum').checked
  };
}

/* ── Расчёт размеров ──
   fl, fw  — полный габарит компонента с выводами
   pl, pw  — внутренний размер ячейки (габарит + зазор)
   tl, tw  — общий размер лотка */
function dimensions(v) {
  const fl = v.l + 2 * v.ll;            // footprint length
  const fw = v.w + 2 * v.lw;            // footprint width
  const pl = fl + 2 * v.clear;          // pocket length
  const pw = fw + 2 * v.clear;          // pocket width
  return {
    fl, fw, pl, pw,
    tl: 2 * (v.wallT + v.margin) + v.cols * pl + (v.cols - 1) * v.div,
    tw: 2 * (v.wallT + v.margin) + v.rows * pw + (v.rows - 1) * v.div
  };
}

/* ── Обновление превью ── */
function update() {
  const v = values(), d = dimensions(v);
  const preview = get('tray-preview');
  preview.innerHTML = '';
  preview.style.gridTemplateColumns = `repeat(${v.cols}, minmax(19px, ${Math.min(64, Math.max(19, d.pl * 5))}px))`;
  preview.style.gridTemplateRows    = `repeat(${v.rows}, minmax(15px, ${Math.min(52, Math.max(15, d.pw * 5))}px))`;
  for (let i = 0; i < v.cols * v.rows; i++) preview.insertAdjacentHTML('beforeend', '<i class="cell"></i>');

  get('size').textContent    = `${d.tl.toFixed(1)} × ${d.tw.toFixed(1)} × ${(v.base + v.wallH).toFixed(1)}`;
  get('count').textContent   = v.cols * v.rows;
  get('pocket').textContent  = `${d.pl.toFixed(1)} × ${d.pw.toFixed(1)}`;
  get('footprint').textContent = (v.ll > 0 || v.lw > 0)
    ? `${d.fl.toFixed(1)} × ${d.fw.toFixed(1)}`
    : `${v.l.toFixed(1)} × ${v.w.toFixed(1)} (без выводов)`;
}

/* ── Применить пресет ── */
function applyPreset() {
  const p = presets[get('preset').value];
  if (!p) return;
  get('partL').value = p.l;
  get('partW').value = p.w;
  get('partH').value = p.h;
  get('leadL').value = p.ll || 0;
  get('leadW').value = p.lw || 0;
  // Кнопка удаления доступна только для пользовательских пресетов
  get('btn-delete').disabled = !!builtinPresets[get('preset').value];
  update();
}

get('preset').addEventListener('change', applyPreset);
form.addEventListener('input', update);

/* ── Генерация STL (без изменений — использует pl/pw из dimensions) ── */
// Сетка прямоугольных объёмов, из которой записываются только внешние грани.
// Такой STL не содержит перекрывающихся внутренних стенок и корректно читается слайсерами.
function stl(v) {
  const d = dimensions(v), hole = 1.2;
  const xs = [0, v.wallT, v.wallT + v.margin], ys = [0, v.wallT, v.wallT + v.margin];
  for (let i = 0; i < v.cols; i++) {
    xs.push(v.wallT + v.margin + i * (d.pl + v.div), v.wallT + v.margin + i * (d.pl + v.div) + d.pl);
    if (i < v.cols - 1) xs.push(v.wallT + v.margin + i * (d.pl + v.div) + d.pl + v.div);
  }
  for (let i = 0; i < v.rows; i++) {
    ys.push(v.wallT + v.margin + i * (d.pw + v.div), v.wallT + v.margin + i * (d.pw + v.div) + d.pw);
    if (i < v.rows - 1) ys.push(v.wallT + v.margin + i * (d.pw + v.div) + d.pw + v.div);
  }
  xs.push(d.tl - v.wallT, d.tl);
  ys.push(d.tw - v.wallT, d.tw);
  if (v.vacuum) for (let i = 0; i < v.cols; i++) for (let j = 0; j < v.rows; j++) {
    const cx = v.wallT + v.margin + i * (d.pl + v.div) + d.pl / 2;
    const cy = v.wallT + v.margin + j * (d.pw + v.div) + d.pw / 2;
    xs.push(cx - hole / 2, cx + hole / 2);
    ys.push(cy - hole / 2, cy + hole / 2);
  }
  const uniq = a => [...new Set(a.map(n => +n.toFixed(5)))].sort((a, b) => a - b);
  const X = uniq(xs), Y = uniq(ys), Z = [0, v.base, v.base + v.wallH], cells = [];
  const isHole = (x, y) => v.vacuum && Array.from({length: v.cols}, (_, i) => i).some(i =>
    Array.from({length: v.rows}, (_, j) => j).some(j => {
      const cx = v.wallT + v.margin + i * (d.pl + v.div) + d.pl / 2;
      const cy = v.wallT + v.margin + j * (d.pw + v.div) + d.pw / 2;
      return x > cx - hole / 2 && x < cx + hole / 2 && y > cy - hole / 2 && y < cy + hole / 2;
    }));
  const inDivider = (p, count, pocket) => Array.from({length: count - 1}, (_, i) => {
    const edge = v.wallT + v.margin + i * (pocket + v.div) + pocket;
    return p > edge && p < edge + v.div;
  }).some(Boolean);
  for (let k = 0; k < 2; k++) for (let i = 0; i < X.length - 1; i++) for (let j = 0; j < Y.length - 1; j++) {
    const x = (X[i] + X[i + 1]) / 2, y = (Y[j] + Y[j + 1]) / 2;
    const outer = x < v.wallT || x > d.tl - v.wallT || y < v.wallT || y > d.tw - v.wallT;
    const divider = inDivider(x, v.cols, d.pl) || inDivider(y, v.rows, d.pw);
    if ((k === 0 && !isHole(x, y)) || (k === 1 && (outer || divider))) cells.push([i, j, k]);
  }
  const set = new Set(cells.map(c => c.join(','))), out = [];
  const tri = (a, b, c) => out.push(...a, ...b, ...c);
  const face = (x0, x1, y0, y1, z0, z1, n) => {
    const p = [[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]];
    const q = [[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]][n];
    tri(p[q[0]], p[q[1]], p[q[2]]);
    tri(p[q[0]], p[q[2]], p[q[3]]);
  };
  cells.forEach(([i, j, k]) => {
    const n = [[i,j,k-1],[i,j,k+1],[i,j-1,k],[i+1,j,k],[i,j+1,k],[i-1,j,k]];
    n.forEach((c, q) => { if (!set.has(c.join(','))) face(X[i], X[i+1], Y[j], Y[j+1], Z[k], Z[k+1], q); });
  });
  const triangleCount = out.length / 9;
  const buf = new ArrayBuffer(84 + triangleCount * 50), dv = new DataView(buf);
  for (let i = 0; i < 80; i++) dv.setUint8(i, 0);
  dv.setUint32(80, triangleCount, true);
  let o = 84;
  for (let i = 0; i < triangleCount; i++) {
    o += 12;
    for (let q = 0; q < 9; q++, o += 4) dv.setFloat32(o, out[i * 9 + q], true);
    dv.setUint16(o, 0, true); o += 2;
  }
  return buf;
}

get('download').addEventListener('click', () => {
  const blob = new Blob([stl(values())], { type: 'model/stl' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `smt-tray-${get('preset').value}.stl`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});

/* ══════════════════════════════════════════════════════════
   Управление пользовательскими пресетами (добавить / редактировать / удалить)
   ══════════════════════════════════════════════════════════ */
const overlay = get('modal-overlay');
let editingId = null;  // null → добавление, строка → редактирование

function openModal(mode) {
  editingId = null;
  if (mode === 'edit') {
    const id = get('preset').value;
    const p = presets[id];
    if (!p) return;
    editingId = id;
    get('modal-title').textContent = 'Редактировать корпус';
    get('m-category').value = p.category;
    get('m-name').value = p.name;
    get('m-l').value = p.l;
    get('m-w').value = p.w;
    get('m-h').value = p.h;
    get('m-ll').value = p.ll || 0;
    get('m-lw').value = p.lw || 0;
  } else {
    get('modal-title').textContent = 'Добавить корпус';
    get('m-category').value = 'Мои корпуса';
    get('m-name').value = '';
    get('m-l').value = 10;
    get('m-w').value = 5;
    get('m-h').value = 1.5;
    get('m-ll').value = 0;
    get('m-lw').value = 0;
  }
  overlay.classList.remove('hidden');
}

function closeModal() {
  overlay.classList.add('hidden');
}

function generateId(name) {
  return 'user_' + name.toLowerCase().replace(/[^a-zа-яё0-9]/gi, '_').replace(/_+/g, '_').substring(0, 30) + '_' + Date.now().toString(36);
}

function saveModal() {
  const name = get('m-name').value.trim();
  if (!name) { get('m-name').focus(); return; }

  const data = {
    category: get('m-category').value.trim() || 'Мои корпуса',
    name:     name,
    l:  Math.max(0.1, parseFloat(get('m-l').value) || 0.1),
    w:  Math.max(0.1, parseFloat(get('m-w').value) || 0.1),
    h:  Math.max(0.1, parseFloat(get('m-h').value) || 0.1),
    ll: Math.max(0, parseFloat(get('m-ll').value) || 0),
    lw: Math.max(0, parseFloat(get('m-lw').value) || 0),
  };
  // Убираем нулевые ll/lw для чистоты
  if (data.ll === 0) delete data.ll;
  if (data.lw === 0) delete data.lw;

  const custom = loadCustomPresets();
  let id;

  if (editingId) {
    id = editingId;
    // Если редактируем встроенный — сохраняем как кастомный с тем же ID (перекрывает)
    custom[id] = data;
  } else {
    id = generateId(name);
    custom[id] = data;
  }

  saveCustomPresets(custom);
  mergePresets();
  rebuildSelect(id);
  closeModal();
}

function deletePreset() {
  const id = get('preset').value;
  if (builtinPresets[id]) return; // нельзя удалить встроенный
  if (!confirm(`Удалить «${presets[id]?.name}»?`)) return;

  const custom = loadCustomPresets();
  delete custom[id];
  saveCustomPresets(custom);
  mergePresets();
  rebuildSelect('sot223');
}

get('btn-add').addEventListener('click', () => openModal('add'));
get('btn-edit').addEventListener('click', () => openModal('edit'));
get('btn-delete').addEventListener('click', deletePreset);
get('modal-save').addEventListener('click', saveModal);
get('modal-cancel').addEventListener('click', closeModal);
overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

/* Инициализация */
applyPreset();
