// 初始化广告弹窗
function initAdModal() {
    const adModal = document.getElementById('adModal');
    const adOverlay = document.getElementById('adOverlay');
    const adCloseBtn = document.getElementById('adCloseBtn');
    const adCountdown = document.getElementById('adCountdown');

    // 显示弹窗
    adModal.style.display = 'block';
    adOverlay.style.display = 'flex';

    // 关闭弹窗
    function closeAd() {
        adModal.style.display = 'none';
        adOverlay.style.display = 'none';
        clearInterval(countdownTimer);
    }

    // 倒计时关闭
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

    // 更新倒计时文本
    function updateCountdown(sec) {
        adCountdown.textContent = `倒计时：${sec}秒后自动关闭`;
    }

    // 点击关闭按钮/遮罩关闭
    adCloseBtn.addEventListener('click', closeAd);
    adOverlay.addEventListener('click', closeAd);
}