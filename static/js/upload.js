// 初始化文件上传
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('fileName');

    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // 选择文件后显示文件名
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            selectedFile = e.target.files[0];
            fileName.textContent = `已选择：${selectedFile.name}`;
        }
    });

    // 拖拽上传
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

// 按钮点击事件（上传+启动转录）
function initButtonEvents() {
    const startBtn = document.getElementById('startBtn');
    const modelSelect = document.getElementById('modelSelect');
    const languageSelect = document.getElementById('languageSelect');
    const taskSelect = document.getElementById('taskSelect');
    const deviceSelect = document.getElementById('deviceSelect');
    const resultPreview = document.getElementById('resultPreview');

    startBtn.addEventListener('click', async () => {
        // 校验：未选择文件
        if (!selectedFile) {
            alert('请先选择要上传的文件！');
            return;
        }

        // 校验：大模型+CPU提示
        if (deviceSelect.value === 'cpu' && ['medium', 'large'].includes(modelSelect.value)) {
            if (!confirm(`当前选择${modelSelect.options[modelSelect.selectedIndex].text}，CPU运行会极慢，建议切换为GPU！是否继续？`)) {
                return;
            }
        }

        // 构建表单数据
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('model', modelSelect.value);
        formData.append('language', languageSelect.value);
        formData.append('task', taskSelect.value);
        formData.append('device', deviceSelect.value);

        try {
            // 上传文件
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.task_id) {
                // 重置预览区
                resultPreview.textContent = '正在转录中，请稍候...';
                document.getElementById('progressText').style.display = 'block';
                // 启动进度轮询
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