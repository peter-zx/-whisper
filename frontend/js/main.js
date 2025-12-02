const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const dropZone = document.getElementById('dropZone');
const fileName = document.getElementById('fileName');
const transcribeBtn = document.getElementById('transcribeBtn');
const processingMsg = document.getElementById('processingMsg');
const resultContainer = document.getElementById('resultContainer');
const subtitlesDisplay = document.getElementById('subtitlesDisplay');
const placeholder = document.getElementById('placeholder');
const copyAllBtn = document.getElementById('copyAllBtn');
const historyList = document.getElementById('historyList');
const adPopup = document.getElementById('adPopup');

browseBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) {
    fileName.textContent = fileInput.files[0].name;
  }
});

['dragover', 'dragenter'].forEach(evt => {
  dropZone.addEventListener(evt, e => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });
});
['dragleave', 'drop'].forEach(evt => {
  dropZone.addEventListener(evt, () => dropZone.classList.remove('drag-over'));
});
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  if (e.dataTransfer.files.length) {
    fileInput.files = e.dataTransfer.files;
    fileName.textContent = fileInput.files[0].name;
  }
});

transcribeBtn.addEventListener('click', async () => {
  if (!fileInput.files.length) return alert('请选择文件');
  
  processingMsg.classList.remove('hidden');
  resultContainer.classList.add('hidden');
  placeholder.classList.add('hidden');

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  formData.append('model', document.getElementById('modelSelect').value);
  formData.append('language', document.getElementById('outputLang').value);

  try {
    const res = await fetch('/transcribe', { method: 'POST', body: formData });
    const data = await res.json();
    
    if (data.error) throw new Error(data.error);

    showResult(data.segments);
    loadHistory();
    setTimeout(() => adPopup.classList.remove('hidden'), 2000);
  } catch (err) {
    alert('❌ ' + err.message);
  } finally {
    processingMsg.classList.add('hidden');
  }
});

function showResult(segments) {
  resultContainer.classList.remove('hidden');
  subtitlesDisplay.innerHTML = segments.map(s => `
    <div class="subtitle-line p-2 border-b border-gray-100">
      <span class="text-blue-600">[${s.start} → ${s.end}]</span><br>
      <span>${s.text}</span>
    </div>
  `).join('');

  copyAllBtn.onclick = () => {
    navigator.clipboard.writeText(segments.map(s => s.text).join('\n\n'))
      .then(() => alert('✅ 已复制全部字幕'));
  };

  document.querySelectorAll('.download-btn').forEach(btn => {
    btn.onclick = () => {
      window.location.href = `/download/${btn.dataset.fmt}`;
    };
  });
}

async function loadHistory() {
  const res = await fetch('/history');
  const history = await res.json();
  historyList.innerHTML = history.length ? 
    history.map(h => `<div class="history-item" onclick="loadFromHistory('${h.id}')">${h.filename}<br><span class="text-xs text-gray-500">${h.created_at}</span></div>`).join('') :
    '<p class="text-gray-500">暂无记录</p>';
}
window.loadFromHistory = async (id) => {
  const res = await fetch('/history');
  const history = await res.json();
  const item = history.find(h => h.id === id);
  if (item) showResult(item.segments);
};

loadHistory();