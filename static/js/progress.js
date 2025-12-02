function startProgressPolling(taskId) {
    currentTaskId = taskId;
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const resultPreview = document.getElementById('resultPreview');

    // 强制初始化进度
    progressBar.style.width = '0%';
    progressText.style.display = 'block';
    progressText.textContent = '0% 准备中...';

    // 轮询（增加调试日志）
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/progress/${taskId}`);
            const data = await response.json();
            
            // 调试日志：打印后端返回的状态
            console.log("进度数据：", data);

            // 更新进度条
            progressBar.style.width = `${data.progress}%`;
            progressText.textContent = `${data.progress}% ${
                data.status === 'processing' ? '正在识别...' : 
                data.status === 'completed' ? '识别完成！' : '识别失败！'
            }`;

            // ========== 核心修复5：强制触发结果展示 ==========
            if (data.status === 'completed' || data.progress >= 100) {
                clearInterval(pollInterval);
                // 强制获取结果
                fetchTranscriptionResult(taskId, resultPreview);
                // 启用下载按钮
                enableDownloadButtons();
                // 刷新历史
                loadHistoryGrid();
            }

            // 超时保护
        } catch (error) {
            console.error("轮询错误：", error);
        }
    }, 500); // 缩短轮询间隔
}

// 修复fetchTranscriptionResult：增加调试日志
async function fetchTranscriptionResult(taskId, previewElement) {
    try {
        console.log("获取结果：", taskId);
        // 直接调用下载接口获取文本
        const response = await fetch(`/api/download/${taskId}/txt`);
        if (response.ok) {
            const text = await response.text();
            console.log("转录结果：", text);
            previewElement.textContent = text || '转录完成，但未生成文本内容！';
        } else {
            previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
        }
    } catch (error) {
        console.error("获取结果错误：", error);
        previewElement.textContent = '转录完成，点击下载按钮获取字幕文件！';
    }
}