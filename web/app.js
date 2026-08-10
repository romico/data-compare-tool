const encodingEl = document.getElementById("encoding");
const fileAEl = document.getElementById("file-a");
const fileBEl = document.getElementById("file-b");
const metaAEl = document.getElementById("meta-a");
const metaBEl = document.getElementById("meta-b");
const columnAEl = document.getElementById("column-a");
const columnBEl = document.getElementById("column-b");
const compareBtn = document.getElementById("compare");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");

const state = {
  fileA: null,
  fileB: null,
  columnsA: [],
  columnsB: [],
};

function formatNumber(value) {
  if (Number.isInteger(value)) return value.toLocaleString("en-US");
  return value.toLocaleString("en-US", { maximumFractionDigits: 6 });
}

function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(2)} GB`;
}

function parseCsvLine(line) {
  const out = [];
  let cur = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          cur += '"';
          i += 1;
        } else {
          inQuotes = false;
        }
      } else {
        cur += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      out.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

function normalizeHeader(name) {
  return String(name ?? "").replace(/^\uFEFF/, "").trim();
}

async function decodeFileText(file, encoding) {
  const buf = await file.arrayBuffer();
  const label = encoding === "euc-kr" ? "euc-kr" : "utf-8";
  try {
    return new TextDecoder(label, { fatal: false }).decode(buf);
  } catch {
    throw new Error(`이 브라우저는 ${label} 디코딩을 지원하지 않습니다.`);
  }
}

async function readColumns(file, encoding) {
  // 헤더만 빠르게 읽기 위해 앞부분만 디코드
  const slice = file.slice(0, Math.min(file.size, 256 * 1024));
  const text = await decodeFileText(slice, encoding);
  const firstLine = text.split(/\r?\n/).find((line) => line.trim() !== "");
  if (!firstLine) throw new Error("헤더가 비어 있습니다.");
  return parseCsvLine(firstLine).map(normalizeHeader).filter(Boolean);
}

async function sumColumn(file, column, encoding, onProgress) {
  const text = await decodeFileText(file, encoding);
  const lines = text.split(/\r?\n/);
  if (lines.length === 0) throw new Error("빈 파일입니다.");

  let headerLine = "";
  let startIdx = 0;
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].trim() !== "") {
      headerLine = lines[i];
      startIdx = i + 1;
      break;
    }
  }

  const headers = parseCsvLine(headerLine).map(normalizeHeader);
  const colIndex = headers.indexOf(column);
  if (colIndex < 0) {
    throw new Error(`컬럼 '${column}'을(를) 찾을 수 없습니다: ${file.name}`);
  }

  let total = 0;
  let valid = 0;
  let rows = 0;
  const totalLines = Math.max(lines.length - startIdx, 1);

  for (let i = startIdx; i < lines.length; i += 1) {
    const line = lines[i];
    if (line.trim() === "") continue;
    rows += 1;
    const cols = parseCsvLine(line);
    const raw = (cols[colIndex] ?? "").trim().replace(/,/g, "");
    if (raw !== "") {
      const num = Number(raw);
      if (!Number.isNaN(num)) {
        total += num;
        valid += 1;
      }
    }
    if (onProgress && rows % 200000 === 0) {
      onProgress(Math.min(99, Math.round((rows / totalLines) * 100)));
      await new Promise((r) => setTimeout(r, 0));
    }
  }

  if (onProgress) onProgress(100);
  return { total, valid, rows };
}

function fillSelect(select, columns, preferred) {
  select.innerHTML = "";
  columns.forEach((col) => {
    const opt = document.createElement("option");
    opt.value = col;
    opt.textContent = col;
    select.appendChild(opt);
  });
  select.disabled = columns.length === 0;
  if (preferred && columns.includes(preferred)) {
    select.value = preferred;
  }
}

function updateCompareEnabled() {
  compareBtn.disabled = !(
    state.fileA &&
    state.fileB &&
    columnAEl.value &&
    columnBEl.value
  );
}

async function onFileChange(side) {
  const input = side === "a" ? fileAEl : fileBEl;
  const meta = side === "a" ? metaAEl : metaBEl;
  const select = side === "a" ? columnAEl : columnBEl;
  const file = input.files?.[0] ?? null;

  resultEl.hidden = true;
  statusEl.textContent = "";

  if (!file) {
    if (side === "a") {
      state.fileA = null;
      state.columnsA = [];
    } else {
      state.fileB = null;
      state.columnsB = [];
    }
    meta.textContent = "선택된 파일 없음";
    fillSelect(select, []);
    updateCompareEnabled();
    return;
  }

  meta.textContent = `${file.name} (${formatBytes(file.size)})`;
  statusEl.textContent = `${side.toUpperCase()} 헤더 읽는 중...`;
  try {
    const columns = await readColumns(file, encodingEl.value);
    if (side === "a") {
      state.fileA = file;
      state.columnsA = columns;
      fillSelect(columnAEl, columns);
      if (state.columnsB.includes(columnAEl.value)) {
        columnBEl.value = columnAEl.value;
      }
    } else {
      state.fileB = file;
      state.columnsB = columns;
      const preferred = state.columnsA.includes(columnAEl.value)
        ? columnAEl.value
        : undefined;
      fillSelect(columnBEl, columns, preferred);
    }
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = err.message || String(err);
    if (side === "a") {
      state.fileA = null;
      state.columnsA = [];
    } else {
      state.fileB = null;
      state.columnsB = [];
    }
    fillSelect(select, []);
  }
  updateCompareEnabled();
}

function renderResult(payload) {
  const matched = Math.abs(payload.diff) < 1e-9;
  resultEl.hidden = false;
  resultEl.innerHTML = `
    <div class="badge ${matched ? "ok" : "bad"}">
      ${matched ? "합계가 일치합니다." : "합계가 일치하지 않습니다."}
    </div>
    <div class="metrics">
      <div class="metric"><span class="label">A 합계</span><span class="value">${formatNumber(payload.sumA)}</span></div>
      <div class="metric"><span class="label">B 합계</span><span class="value">${formatNumber(payload.sumB)}</span></div>
      <div class="metric"><span class="label">차이 (A − B)</span><span class="value">${formatNumber(payload.diff)}</span></div>
      <div class="metric"><span class="label">차이율 (대비 B)</span><span class="value">${payload.diffPct}</span></div>
    </div>
    <table>
      <thead>
        <tr><th>항목</th><th>A</th><th>B</th></tr>
      </thead>
      <tbody>
        <tr><td>파일</td><td>${payload.nameA}</td><td>${payload.nameB}</td></tr>
        <tr><td>컬럼</td><td>${payload.colA}</td><td>${payload.colB}</td></tr>
        <tr><td>전체 행 수</td><td>${payload.rowsA.toLocaleString()}</td><td>${payload.rowsB.toLocaleString()}</td></tr>
        <tr><td>숫자 행 수</td><td>${payload.validA.toLocaleString()}</td><td>${payload.validB.toLocaleString()}</td></tr>
        <tr><td>합계</td><td>${formatNumber(payload.sumA)}</td><td>${formatNumber(payload.sumB)}</td></tr>
      </tbody>
    </table>
  `;
}

async function runCompare() {
  if (!state.fileA || !state.fileB) return;
  compareBtn.disabled = true;
  resultEl.hidden = true;

  try {
    statusEl.textContent = "파일 A 합계 계산 중...";
    const a = await sumColumn(state.fileA, columnAEl.value, encodingEl.value, (p) => {
      statusEl.textContent = `파일 A 합계 계산 중... ${p}%`;
    });

    statusEl.textContent = "파일 B 합계 계산 중...";
    const b = await sumColumn(state.fileB, columnBEl.value, encodingEl.value, (p) => {
      statusEl.textContent = `파일 B 합계 계산 중... ${p}%`;
    });

    const diff = a.total - b.total;
    let diffPct = "N/A (B 합계 0)";
    if (b.total !== 0) diffPct = `${((diff / b.total) * 100).toFixed(6)}%`;
    else if (a.total === 0) diffPct = "0%";

    renderResult({
      sumA: a.total,
      sumB: b.total,
      diff,
      diffPct,
      nameA: state.fileA.name,
      nameB: state.fileB.name,
      colA: columnAEl.value,
      colB: columnBEl.value,
      rowsA: a.rows,
      rowsB: b.rows,
      validA: a.valid,
      validB: b.valid,
    });
    statusEl.textContent = "완료";
  } catch (err) {
    statusEl.textContent = err.message || String(err);
  } finally {
    updateCompareEnabled();
  }
}

fileAEl.addEventListener("change", () => onFileChange("a"));
fileBEl.addEventListener("change", () => onFileChange("b"));
encodingEl.addEventListener("change", async () => {
  if (state.fileA) await onFileChange("a");
  if (state.fileB) await onFileChange("b");
});
columnAEl.addEventListener("change", () => {
  if (state.columnsB.includes(columnAEl.value)) {
    columnBEl.value = columnAEl.value;
  }
  updateCompareEnabled();
});
columnBEl.addEventListener("change", updateCompareEnabled);
compareBtn.addEventListener("click", runCompare);
