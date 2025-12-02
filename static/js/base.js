// 全局变量（所有模块共享）
let selectedFile = null;
let progressPolling = null;
let currentTaskId = null;

// 页面加载完成后初始化所有模块
document.addEventListener('DOMContentLoaded', function() {
    // 初始化各模块
    initUpload();                // 上传模块
    initAdModal();               // 广告弹窗模块
    initButtonEvents();          // 按钮事件模块
    loadHistoryGrid();           // 历史记录模块
    initProgressDisplay();       // 进度条模块
    initDownloadButtons();       // 下载按钮模块
    
    // 默认选中简体中文
    document.getElementById('languageSelect').value = 'zh';
});