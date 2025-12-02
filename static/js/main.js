// static/js/main.js

let selectedFile = null;

// 文件选择按钮
document.getElementById('browseBtn').addEventListener('click', () => {
  document.getElementById('fileInput').click();
});

// 监听文件选择
document.getElementById('fileInput').addEventListener('change', (e) => {
  const file = e.target.files[0];
  selectedFile = file;
  if (file) {
    document.getElementById('fileName').innerText = file.name;
    document.getElementById('status').innerText = '已选择文件，点击“开始转录”';
  } else {
    document.getElementById('fileName').innerText = '';
    document.getElementById('status').innerText = '等待上传...';
  }
});

// 开始转录按钮
document.getElementById('startBtn').addEventListener('click', async () => {
  if (!selectedFile) {
    alert('❌ 请先选择一个音频或视频文件');
    return;
  }

  const formData = new FormData();
  formData.append('file', selectedFile);

  const statusEl = document.getElementById('status');
  statusEl.innerText = '正在上传并转录...';

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || `服务器返回错误: ${res.status}`);
    }

    // === 渲染带时间轴的字幕预览 ===
    const resultDiv = document.getElementById('resultText');
    resultDiv.innerHTML = '';

    if (data.segments && data.segments.length > 0) {
      data.segments.forEach(seg => {
        const line = document.createElement('div');
        line.className = 'subtitle-line';

        const start = formatTimestamp(seg.start);
        const end = formatTimestamp(seg.end);

        line.innerHTML = `<span class="time">${start} → ${end}</span><br><span class="text">${seg.text.trim()}</span>`;
        resultDiv.appendChild(line);
      });
    } else {
      // fallback to plain text
      resultDiv.innerText = data.text || '无转录结果';
    }

    // === 显示下载按钮 ===
    const downloadBar = document.getElementById('downloadBar');
    const downloadButtons = document.getElementById('downloadButtons');
    downloadButtons.innerHTML = '';

    data.available_formats.forEach(fmt => {
      const btn = document.createElement('button');
      btn.className = 'btn-download';
      btn.innerText = `下载 .${fmt}`;
      btn.onclick = () => {
        window.location.href = `/api/download/${data.filename_base}/${fmt}`;
      };
      downloadButtons.appendChild(btn);
    });

    downloadBar.style.display = 'block';
    statusEl.innerText = '✅ 转录完成！';

  } catch (err) {
    console.error('转录失败:', err);
    statusEl.innerText = '❌ 转录失败';
    alert('错误: ' + (err.message || '未知错误，请查看控制台'));
  }
});

// 赞助弹窗（可选）
function closeSponsor() {
  document.getElementById('sponsorModal').style.display = 'none';
}

// 时间戳格式化：秒 → HH:MM:SS.mmm
function formatTimestamp(seconds) {
  const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
  const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  const ms = Math.floor((seconds % 1) * 1000).toString().padStart(3, '0');
  return `${h}:${m}:${s}.${ms}`;
}