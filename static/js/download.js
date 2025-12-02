// 初始化下载按钮（禁用状态）
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

// 启用下载按钮
function enableDownloadButtons() {
    const downloadButtons = document.querySelectorAll('.btn-download');
    downloadButtons.forEach(btn => {
        btn.classList.add('enabled');
    });
}