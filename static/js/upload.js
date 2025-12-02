// static/js/upload.js
// 【最终终极版】解决所有上传按钮问题
window.onload = function() {
    // 等待页面完全加载（比DOMContentLoaded更可靠）
    initUpload();
};

// 全局变量
let currentTaskId = "";

/**
 * 初始化上传功能（核心）
 */
function initUpload() {
    // 强制获取所有元素（兼容所有场景）
    const uploadBtn = document.getElementById('uploadBtn');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const progressContainer = document.getElementById('progressContainer');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');

    // 初始化状态
    if (uploadStatus) uploadStatus.textContent = '';
    if (progressContainer) progressContainer.style.display = 'none';

    // 按钮点击事件（核心：直接绑定，不用表单提交）
    if (uploadBtn) {
        uploadBtn.addEventListener('click', async function() {
            // 1. 获取选中的文件
            const file = fileInput ? fileInput.files[0] : null;
            
            // 2. 校验文件
            if (!file) {
                if (uploadStatus) {
                    uploadStatus.textContent = '❌ 请先选择要上传的音频/视频文件！';
                    uploadStatus.style.color = '#e53e3e';
                }
                return;
            }

            // 3. 按钮置为加载状态
            uploadBtn.disabled = true;
            uploadBtn.textContent = '上传中...';
            fileInput.disabled = true;
            uploadStatus.textContent = '🔄 正在上传文件，请稍候...';
            uploadStatus.style.color = '#4299e1';
            resultPreview.innerHTML = '<div style="text-align:center; padding: 50px 0;">正在上传文件...</div>';

            try {
                // 4. 构建上传数据
                const formData = new FormData();
                formData.append('file', file);
                formData.append('model', 'tiny');
                formData.append('language', 'zh');
                formData.append('task', 'transcribe');
                formData.append('device', 'cpu');

                // 5. 发送上传请求（核心）
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    timeout: 60000 // 超时时间60秒
                });

                // 6. 解析响应
                if (!response.ok) throw new Error(`HTTP错误：${response.status}`);
                const responseData = await response.json();

                // 7. 上传成功处理
                if (responseData.task_id) {
                    currentTaskId = responseData.task_id;
                    uploadStatus.textContent = '✅ 文件上传成功，开始识别音频/视频...';
                    uploadStatus.style.color = '#48bb78';
                    
                    // 显示进度条
                    if (progressContainer) progressContainer.style.display = 'block';
                    if (progressBar) progressBar.style.width = '10%';
                    if (progressText) progressText.textContent = '10% 正在识别...';
                    
                    // 启动进度轮询
                    startProgressPolling(responseData.task_id);
                } else {
                    throw new Error(responseData.error || '上传失败，未获取到任务ID');
                }

            } catch (error) {
                // 8. 错误处理
                console.error('上传错误：', error);
                uploadStatus.textContent = `❌ 上传失败：${error.message || '网络异常，请重试！'}`;
                uploadStatus.style.color = '#e53e3e';
                resultPreview.innerHTML = `<div style="text-align:center; color: #e53e3e; padding: 50px 0;">上传失败：${error.message || '请检查网络后重试'}</div>`;
                
                // 恢复按钮状态
                uploadBtn.disabled = false;
                uploadBtn.textContent = '开始识别';
                fileInput.disabled = false;

            }
        });
    }

    // 9. 文件选择事件（选文件后显示文件名）
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                uploadStatus.textContent = `📄 已选择文件：${file.name}（大小：${formatFileSize(file.size)}）`;
                uploadStatus.style.color = '#4299e1';
            } else {
                uploadStatus.textContent = '';
            }
        });
    }

    // 辅助函数：格式化文件大小
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
}

/**
 * 进度轮询函数（和progress.js联动）
 */
function startProgressPolling(taskId) {
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');
    const downloadButtons = document.querySelectorAll('.btn-download');

    // 初始化进度
    progressBar.style.width = '10%';
    progressText.textContent = '10% 正在识别音频...';

    // 轮询（每秒一次）
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${taskId}`);
            if (!response.ok) throw new Error('获取进度失败');
            
            const data = await response.json();
            
            // 更新进度条
            progressBar.style.width = `${data.progress}%`;
            progressText.textContent = `${data.progress}% ${data.status === 'processing' ? '正在识别...' : '识别完成！'}`;

            // 识别完成
            if (data.status === 'completed') {
                clearInterval(pollInterval);
                progressBar.style.width = '100%';
                
                // 获取SRT结果（带时间轴）
                const srtResponse = await fetch(`/api/download/${taskId}/srt`);
                if (srtResponse.ok) {
                    const srtContent = await srtResponse.text();
                    resultPreview.innerHTML = formatSRT(srtContent);
                } else {
                    // 降级获取TXT
                    const txtResponse = await fetch(`/api/download/${taskId}/txt`);
                    const txtContent = await txtResponse.text();
                    resultPreview.innerHTML = txtContent.replace(/\n/g, '<br>');
                }

                // 启用下载按钮
                downloadButtons.forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.addEventListener('click', function() {
                        const format = this.dataset.format;
                        window.open(`/api/download/${taskId}/${format}`, '_blank');
                    });
                });
            }

            // 识别失败
            if (data.status === 'failed') {
                clearInterval(pollInterval);
                resultPreview.innerHTML = `<div style="text-align:center; color: #e53e3e; padding: 50px 0;">识别失败：${data.error || '未知错误'}</div>`;
                const uploadBtn = document.getElementById('uploadBtn');
                uploadBtn.disabled = false;
                uploadBtn.textContent = '重新识别';
                document.getElementById('fileInput').disabled = false;
            }

        } catch (error) {
            console.error('进度轮询错误：', error);
            // 轮询10次后停止
            let pollCount = (pollCount || 0) + 1;
            if (pollCount > 60) {
                clearInterval(pollInterval);
                progressText.textContent = '识别超时，请重试！';
            }
        }
    }, 1000);
}

/**
 * 格式化SRT为美观的HTML
 */
function formatSRT(srtContent) {
    if (!srtContent) return '暂无识别结果';
    const lines = srtContent.split('\n');
    let html = '<div class="srt-container">';
    let currentBlock = '';
    let isTimeLine = false;

    lines.forEach(line => {
        line = line.trim();
        if (line === '') {
            if (currentBlock) {
                html += `<div class="srt-block">${currentBlock}</div>`;
                currentBlock = '';
            }
        } else if (/^\d+$/.test(line)) {
            // 跳过序号
        } else if (line.includes('-->')) {
            isTimeLine = true;
            currentBlock += `<div class="srt-time" style="color: #2196F3; font-family: monospace; margin: 8px 0;">${line.replace(' --> ', ' → ')}</div>`;
        } else if (isTimeLine) {
            currentBlock += `<div class="srt-text" style="color: #333; line-height: 1.6; padding-left: 8px; border-left: 3px solid #48bb78;">${line}</div>`;
            isTimeLine = false;
        }
    });

    html += '</div>';
    return html;
}

// 全局暴露方法
window.initUpload = initUpload;
window.startProgressPolling = startProgressPolling;