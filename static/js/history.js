// 加载转录历史（2行5列网格）
async function loadHistoryGrid() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        const historyGrid = document.getElementById('historyGrid');
        historyGrid.innerHTML = '';

        // 最多取10条记录
        const historyItems = (data.history || []).slice(0, 10);
        
        // 无历史记录
        if (historyItems.length === 0) {
            historyGrid.innerHTML = '<div class="history-grid-item" style="grid-column: span 5; text-align: center; color: #999;">暂无转录历史</div>';
            return;
        }

        // 渲染历史按钮
        historyItems.forEach((item, index) => {
            const gridItem = document.createElement('div');
            gridItem.className = 'history-grid-item';
            
            const btn = document.createElement('button');
            btn.className = 'history-grid-btn';
            // 简化文件名显示
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

// 下载历史文件
function downloadHistoryFile(taskId, format) {
    window.open(`/api/download/${taskId}/${format}`, '_blank');
}