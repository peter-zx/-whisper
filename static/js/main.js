// 全局变量
let selectedFile = null;
let progressPolling = null;
let currentTaskId = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initUploadArea();      
    initAdModal();         
    initButtonEvents();    
    loadHistoryGrid();     // 改为加载网格布局的历史
    initProgressDisplay(); 
    initDownloadButtons(); 
    // 默认选中简体中文
    document.getElementById('languageSelect').value = 'zh';
});

// 1. 初始化上传区域
function initUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileName.textContent = `已选择：${selectedFile.name}`;
        }
    });

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '#ebf8ff';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.backgroundColor = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.backgroundColor = '';
        
        if (e.dataTransfer.files.length > 0) {
            selectedFile = e.dataTransfer.files[0];
            fileName.textContent = `已选择：${selectedFile.name}`;
        }
    });
}

// 2. 初始化广告弹窗
function initAdModal() {
    const adModal = document.getElementById('adModal');
    const adOverlay = document.getElementById('adOverlay');
    const adCloseBtn = document.getElementById('adCloseBtn');
    const adCountdown = document.getElementById('adCountdown');

    adModal.style.display = 'block';
    adOverlay.style.display = 'flex';

    function closeAd() {
        adModal.style.display = 'none';
        adOverlay.style.display = 'none';
        clearInterval(countdownTimer);
    }

    let countdownTimer;
    let seconds = 5;
    updateCountdown(seconds);
    
    countdownTimer = setInterval(() => {
        seconds--;
        updateCountdown(seconds);
        
        if (seconds <= 0) {
            closeAd();
        }
    }, 1000);

    function updateCountdown(sec) {
        adCountdown.textContent = `倒计时：${sec}秒后自动关闭`;
    }

    adCloseBtn.addEventListener('click', closeAd);
    adOverlay.addEventListener('click', closeAd);
}

// 3. 初始化按钮事件
function initButtonEvents() {
    const startBtn = document.getElementById('startBtn');
    const modelSelect = document.getElementById('modelSelect');
    const languageSelect = document.getElementById('languageSelect');
    const taskSelect = document.getElementById('taskSelect');
    const deviceSelect = document.getElementById('deviceSelect');
    const resultPreview = document.getElementById('resultPreview');

    startBtn.addEventListener('click', async () => {
        if (!selectedFile) {
            alert('请先选择要上传的文件！');
            return;
        }

        // 验证GPU选择（大模型强制提示）
        if (deviceSelect.value === 'cpu' && ['medium', 'large'].includes(modelSelect.value)) {
            if (!confirm(`当前选择${modelSelect.options[modelSelect.selectedIndex].text}，CPU运行会极慢，建议切换为GPU！是否继续？`)) {
                return;
            }
        }

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('model', modelSelect.value);
        formData.append('language', languageSelect.value);
        formData.append('task', taskSelect.value);
        formData.append('device', deviceSelect.value);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.task_id) {
                resultPreview.textContent = '正在转录中，请稍候...';
                document.getElementById('progressText').style.display = 'block';
                startProgressPolling(data.task_id);
            } else {
                alert('上传失败：' + (data.error || '未知错误'));
            }
        } catch (error) {
            console.error('上传失败：', error);
            alert('上传失败，请检查网络或文件！');
        }
    });
}

// 4. 初始化进度条显示
function initProgressDisplay() {
    document.getElementById('progressText').style.display = 'none';
}

// 5. 初始化下载按钮
function initDownloadButtons() {
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(btn => {
        btn.classList.remove('enabled');
        btn.addEventListener('click', (e) => {
            if (!btn.classList.contains('enabled')) {
                e.preventDefault();
                alert('暂无可用的转录结果，请先完成转录！');
                return;
            }
            if (!currentTaskId) {
                alert('暂无可下载的转录结果！');
                return;
            }
            const format = btn.getAttribute('data-format');
            window.open(`/api/download/${currentTaskId}/${format}`, '_blank');
        });
    });
}

// 6. 启用下载按钮
function enableDownloadButtons() {
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(btn => {
        btn.classList.add('enabled');
    });
}

// 7. 进度条轮询（核心修复：检测完成状态）
function startProgressPolling(taskId) {
    currentTaskId = taskId;
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');

    if (progressPolling) {
        clearInterval(progressPolling);
    }

    progressPolling = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${taskId}`);
            const data = await response.json();

            // 更新进度
            progressBar.style.width = `${data.progress}%`;
            progressText.textContent = `${data.progress}% ${
                data.status === 'processing' ? '正在识别...' : 
                data.status === 'completed' ? '识别完成！' : '识别失败！'
            }`;

            // 任务完成
            if (data.status === 'completed') {
                clearInterval(progressPolling);
                progressPolling = null;
                enableDownloadButtons();
                fetchTranscriptionResult(taskId, resultPreview);
                loadHistoryGrid(); // 刷新历史网格
            }
            // 任务失败
            else if (data.status === 'failed') {
                clearInterval(progressPolling);
                progressPolling = null;
                resultPreview.textContent = '转录失败，请检查文件/模型/设备配置！';
            }
        } catch (error) {
            console.error('获取进度失败：', error);
            clearInterval(progressPolling);
            progressPolling = null;
            progressText.textContent = '获取进度失败，请重试！';
        }
    }, 500);
}

// 8. 获取转录结果
async function fetchTranscriptionResult(taskId, previewElement) {
    try {
        const response = await fetch(`/api/download/${taskId}/txt`);
        if (response.ok) {
            const text = await response.text();
            previewElement.textContent = text || '转录完成，但未生成文本内容！';
        } else {
            previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
        }
    } catch (error) {
        previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
    }
}

// 9. 加载转录历史（2行5列网格，最多10条）
async function loadHistoryGrid() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        const historyGrid = document.getElementById('historyGrid');
        historyGrid.innerHTML = '';

        // 最多取10条（2行5列）
        const historyItems = (data.history || []).slice(0, 10);
        
        if (historyItems.length === 0) {
            historyGrid.innerHTML = '<div class="history-grid-item" style="grid-column: span 5; text-align: center; color: #999;">暂无转录历史</div>';
            return;
        }

        // 渲染网格按钮
        historyItems.forEach((item, index) => {
            const gridItem = document.createElement('div');
            gridItem.className = 'history-grid-item';
            
            const btn = document.createElement('button');
            btn.className = 'history-grid-btn';
            // 简化文件名显示（最多8个字符）
            const shortName = item.filename.length > 8 
                ? item.filename.substring(0, 8) + '...' 
                : item.filename;
            btn.textContent = shortName;
            btn.title = `下载${item.filename}的SRT字幕`;
            btn.onclick = () => downloadHistoryFile(item.task_id, 'srt');
            
            gridItem.appendChild(btn);
            historyGrid.appendChild(gridItem);
        });
    } catch (error) {
        console.error('加载历史失败：', error);
        document.getElementById('historyGrid').innerHTML = '<div class="history-grid-item" style="grid-column: span 5; text-align: center; color: #e53e3e;">加载历史失败</div>';
    }
}

// 10. 下载历史文件
function downloadHistoryFile(taskId, format) {
    window.open(`/api/download/${taskId}/${format}`, '_blank');
}

// 11. 停止进度轮询
function stopProgressPolling() {
    if (progressPolling) {
        clearInterval(progressPolling);
        progressPolling = null;
    }
}