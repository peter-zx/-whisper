// static/js/progress.js
let currentTaskId = "";

function initProgressDisplay() {
    const progressText = document.getElementById('progressText');
    if (progressText) {
        progressText.style.display = 'none';
    }
}

function startProgressPolling(taskId) {
    currentTaskId = taskId;
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');

    if (progressBar) progressBar.style.width = '0%';
    if (progressText) {
        progressText.style.display = 'block';
        progressText.textContent = '0% 准备中...';
    }
    if (resultPreview) resultPreview.innerHTML = '<div class="loading">正在转录，请稍候...</div>';

    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${taskId}`);
            if (!response.ok) throw new Error(`HTTP错误：${response.status}`);
            
            const data = await response.json();

            if (progressBar) progressBar.style.width = `${data.progress}%`;
            if (progressText) {
                let statusText = "";
                switch(data.status) {
                    case "processing":
                        statusText = `${data.progress}% 正在识别...`;
                        break;
                    case "completed":
                        statusText = `${data.progress}% 识别完成！`;
                        break;
                    case "failed":
                        statusText = `${data.progress}% 识别失败！`;
                        break;
                    default:
                        statusText = `${data.progress}% 处理中...`;
                }
                progressText.textContent = statusText;
            }

            if (data.status === 'completed') {
                clearInterval(pollInterval);
                await fetchSRTResult(taskId, resultPreview);
                enableDownloadButtons();
                if (typeof loadHistoryGrid === 'function') {
                    loadHistoryGrid();
                }
            }

            if (data.status === 'failed') {
                clearInterval(pollInterval);
                if (resultPreview) {
                    resultPreview.innerHTML = `<div class="error">转录失败：${data.error || '未知错误'}</div>`;
                }
            }

        } catch (error) {
            console.error("轮询错误：", error);
            let pollCount = (pollCount || 0) + 1;
            if (pollCount > 60) {
                clearInterval(pollInterval);
                if (progressText) progressText.textContent = '转录超时，请重试！';
                if (resultPreview) {
                    resultPreview.innerHTML = '<div class="error">转录超时，请刷新页面重试</div>';
                }
            }
        }
    }, 500);
}

async function fetchSRTResult(taskId, previewElement) {
    if (!previewElement) return;

    try {
        const response = await fetch(`/api/download/${taskId}/srt`);
        
        if (response.ok) {
            const srtContent = await response.text();
            const formattedContent = formatSRTForDisplay(srtContent);
            previewElement.innerHTML = formattedContent;
        } else {
            await fetchTranscriptionResult(taskId, previewElement);
        }
    } catch (error) {
        await fetchTranscriptionResult(taskId, previewElement);
    }
}

function formatSRTForDisplay(srtContent) {
    if (!srtContent || srtContent.trim() === "") {
        return '<div class="empty-result">暂无转录结果</div>';
    }
    
    const lines = srtContent.split('\n');
    let formatted = '<div class="srt-container">';
    
    let currentBlock = "";
    let isTimeLine = false;
    
    lines.forEach(line => {
        line = line.trim();
        if (line === "") {
            if (currentBlock) {
                formatted += `<div class="srt-block">${currentBlock}</div>`;
                currentBlock = "";
            }
        } else if (/^\d+$/.test(line)) {
            currentBlock += `<span class="srt-index">${line}</span>`;
        } else if (line.includes("-->")) {
            isTimeLine = true;
            const timeline = line.replace(",", ".").replace(" --> ", " → ");
            currentBlock += `<div class="srt-timeline">${timeline}</div>`;
        } else if (isTimeLine) {
            if (line) {
                currentBlock += `<div class="srt-text">${line}</div>`;
            }
            isTimeLine = false;
        }
    });
    
    if (currentBlock) {
        formatted += `<div class="srt-block">${currentBlock}</div>`;
    }
    
    formatted += '</div>';
    return formatted;
}

async function fetchTranscriptionResult(taskId, previewElement) {
    if (!previewElement) return;

    try {
        const response = await fetch(`/api/download/${taskId}/txt`);
        if (response.ok) {
            const text = await response.text();
            if (text) {
                previewElement.innerHTML = `<div class="txt-result">${text.replace(/\n/g, '<br>')}</div>`;
            } else {
                previewElement.textContent = '转录完成，但未生成文本内容！';
            }
        } else {
            previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
        }
    } catch (error) {
        previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
    }
}

function enableDownloadButtons() {
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = "1";
        btn.style.cursor = "pointer";
        btn.addEventListener('click', function() {
            const format = this.dataset.format;
            if (currentTaskId && format) {
                window.open(`/api/download/${currentTaskId}/${format}`, '_blank');
            }
        });
    });
}

function stopProgressPolling() {}

document.addEventListener('DOMContentLoaded', function() {
    initProgressDisplay();
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
    });
});