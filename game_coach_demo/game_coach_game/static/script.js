// ==================== 卡牌系统配置 ====================
const CARD_CONFIG = {
    'double_score': { name: '双重预言', icon: '✨', rarity: 'rare', effect: '本局得分×2', type: 'function' },
    'skip_turn': { name: '时间禁锢', icon: '⏳', rarity: 'super-rare', effect: '跳过对方一次回合', type: 'function' },
    'change_number': { name: '命运改写', icon: '🔄', rarity: 'super-rare', effect: '修改之前的一次输入', type: 'function' },
    'next_time': { name: '下次一定', icon: '🤷', rarity: 'common', effect: '没用', type: 'function' },
    'color_purple': { name: '紫晶幻彩', icon: '💜', rarity: 'rare', effect: '解锁紫色', type: 'color', colorId: 'purple' },
    'color_gold': { name: '黄金圣辉', icon: '🏆', rarity: 'rare', effect: '解锁金色', type: 'color', colorId: 'gold' },
    'color_silver': { name: '银月流光', icon: '🌙', rarity: 'rare', effect: '解锁银色', type: 'color', colorId: 'silver' },
    'color_pink': { name: '粉樱绚烂', icon: '🌸', rarity: 'rare', effect: '解锁粉色', type: 'color', colorId: 'pink' },
    'color_aurora': { name: '极光之境', icon: '🌈', rarity: 'legendary', effect: '解锁极光色', type: 'color', colorId: 'aurora' },
    'color_neon': { name: '霓虹幻梦', icon: '💫', rarity: 'legendary', effect: '解锁荧光色', type: 'color', colorId: 'neon' }
};

const GACHA_COST = 50;
const GACHA_RARITY = {
    'common': { chance: 0.5, cards: ['next_time'] },
    'rare': { chance: 0.3, cards: ['double_score', 'color_purple', 'color_gold', 'color_silver', 'color_pink'] },
    'super-rare': { chance: 0.15, cards: ['skip_turn', 'change_number'] },
    'legendary': { chance: 0.05, cards: ['color_aurora', 'color_neon'] }
};

// ==================== 全局变量 ====================
let currentRoomCode = null;
let currentPlayerColor = null;
let selectedCell = null;
let windowCurrentGameData = null;
let inputBuffer = '';
let showMessageTimeout = null;
let player1Color = null;
let player2Color = null;
let currentPlayerName = null;
let selectedTempColor = null;
let isColorSelected = false;
let hasStartedGame = false;
let isMobile = false;
let userPoints = 0;
let myCards = {};
let unlockedColors = [];
let gameScoreMultiplier = 1;
let skipNextTurn = false;
let canChangeNumber = false;
let moveHistory = [];
let usedCardsThisGame = {};
let changeMode = false;
let skipTurnActive = false;
let anyCardUsed = false;  // 修复①：标记是否已使用过任何卡牌

// ==================== 音效系统 ====================
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playSound(type) {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    const now = audioContext.currentTime;
    
    switch(type) {
        case 'click':
            oscillator.type = 'square';
            oscillator.frequency.setValueAtTime(800, now);
            oscillator.frequency.exponentialRampToValueAtTime(400, now + 0.1);
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
            oscillator.start(now);
            oscillator.stop(now + 0.1);
            break;
        case 'place':
            oscillator.type = 'square';
            oscillator.frequency.setValueAtTime(400, now);
            oscillator.frequency.setValueAtTime(600, now + 0.05);
            oscillator.frequency.setValueAtTime(800, now + 0.1);
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            oscillator.start(now);
            oscillator.stop(now + 0.15);
            break;
        case 'score':
            oscillator.type = 'square';
            oscillator.frequency.setValueAtTime(523, now);
            oscillator.frequency.setValueAtTime(659, now + 0.1);
            oscillator.frequency.setValueAtTime(784, now + 0.2);
            oscillator.frequency.setValueAtTime(1047, now + 0.3);
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
            oscillator.start(now);
            oscillator.stop(now + 0.4);
            break;
        case 'win':
            playWinMelody();
            break;
        case 'draw':
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(600, now);
            oscillator.frequency.setValueAtTime(600, now + 0.2);
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
            oscillator.start(now);
            oscillator.stop(now + 0.4);
            break;
        case 'error':
            oscillator.type = 'sawtooth';
            oscillator.frequency.setValueAtTime(150, now);
            oscillator.frequency.linearRampToValueAtTime(100, now + 0.2);
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
            oscillator.start(now);
            oscillator.stop(now + 0.3);
            break;
        case 'select':
            oscillator.type = 'square';
            oscillator.frequency.setValueAtTime(1000, now);
            gainNode.gain.setValueAtTime(0.05, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
            oscillator.start(now);
            oscillator.stop(now + 0.08);
            break;
        case 'gacha':
            playGachaSound();
            break;
        case 'legendary':
            playLegendarySound();
            break;
        case 'card':
            playCardSound();
            break;
    }
}

function playWinMelody() {
    const notes = [523, 659, 784, 1047, 784, 1047];
    const now = audioContext.currentTime;
    notes.forEach((freq, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.type = 'square';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.1, now + index * 0.15);
        gain.gain.exponentialRampToValueAtTime(0.01, now + index * 0.15 + 0.1);
        osc.start(now + index * 0.15);
        osc.stop(now + index * 0.15 + 0.1);
    });
}

function playGachaSound() {
    const now = audioContext.currentTime;
    const notes = [523, 659, 784, 1047, 1318];
    notes.forEach((freq, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.type = 'square';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.1, now + index * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.01, now + index * 0.1 + 0.15);
        osc.start(now + index * 0.1);
        osc.stop(now + index * 0.1 + 0.15);
    });
}

function playLegendarySound() {
    const now = audioContext.currentTime;
    const notes = [523, 659, 784, 1047, 1318, 1568, 2093];
    notes.forEach((freq, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.type = 'square';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.15, now + index * 0.12);
        gain.gain.exponentialRampToValueAtTime(0.01, now + index * 0.12 + 0.2);
        osc.start(now + index * 0.12);
        osc.stop(now + index * 0.12 + 0.2);
    });
}

function playCardSound() {
    const now = audioContext.currentTime;
    const notes = [523, 784, 1047];
    notes.forEach((freq, index) => {
        const osc = audioContext.createOscillator();
        const gain = audioContext.createGain();
        osc.connect(gain);
        gain.connect(audioContext.destination);
        osc.type = 'square';
        osc.frequency.value = freq;
        gain.gain.setValueAtTime(0.1, now + index * 0.1);
        gain.gain.exponentialRampToValueAtTime(0.01, now + index * 0.1 + 0.15);
        osc.start(now + index * 0.1);
        osc.stop(now + index * 0.1 + 0.15);
    });
}

// ==================== 设备检测 ====================
function checkMobileDevice() {
    isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
    return isMobile;
}

// ==================== 移动端键盘 ====================
function openMobileKeyboard() {
    if (!isMobile) return;
    const keyboard = document.getElementById('mobileKeyboard');
    if (keyboard) {
        keyboard.classList.add('show');
        document.body.classList.add('keyboard-open');
    }
}

function closeMobileKeyboard() {
    const keyboard = document.getElementById('mobileKeyboard');
    if (keyboard) {
        keyboard.classList.remove('show');
        document.body.classList.remove('keyboard-open');
    }
}

function inputMobileNumber(value) {
    if (!selectedCell || !currentRoomCode) {
        showMessage('请先选择一个格子！');
        playSound('error');
        closeMobileKeyboard();
        return;
    }
    closeMobileKeyboard();
    if (changeMode) {
        submitChangeInput(value);
    } else {
        submitInput(value);
    }
}

// ==================== API 调用 ====================
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = { method, headers: { 'Content-Type': 'application/json' } };
    if (data) options.body = JSON.stringify(data);
    try {
        const response = await fetch(endpoint, options);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, message: '网络错误' };
    }
}

// ==================== 用户系统 ====================
async function login() {
    playSound('click');
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const errorEl = document.getElementById('loginError');
    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        errorEl.style.display = 'block';
        playSound('error');
        return;
    }
    const result = await apiCall('/api/login', 'POST', { username, password });
    if (result.success) {
        document.getElementById('currentUser').textContent = result.username;
        currentPlayerName = result.username;
        await loadUserData();
        playSound('select');
        showMenu();
    } else {
        errorEl.textContent = result.message;
        errorEl.style.display = 'block';
        playSound('error');
    }
}

async function register() {
    playSound('click');
    const username = document.getElementById('newUsername').value.trim();
    const password = document.getElementById('newPassword').value.trim();
    const confirmPassword = document.getElementById('confirmPassword').value.trim();
    const errorEl = document.getElementById('registerError');
    const successEl = document.getElementById('registerSuccess');
    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        errorEl.style.display = 'block';
        playSound('error');
        return;
    }
    if (password !== confirmPassword) {
        errorEl.textContent = '两次输入的密码不一致';
        errorEl.style.display = 'block';
        playSound('error');
        return;
    }
    const result = await apiCall('/api/register', 'POST', { username, password, confirmPassword });
    if (result.success) {
        successEl.textContent = result.message;
        successEl.style.display = 'block';
        errorEl.style.display = 'none';
        playSound('select');
        setTimeout(() => showLogin(), 1500);
    } else {
        errorEl.textContent = result.message;
        errorEl.style.display = 'block';
        playSound('error');
    }
}

async function logout() {
    playSound('click');
    await apiCall('/api/logout', 'POST');
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    userPoints = 0;
    myCards = {};
    unlockedColors = [];
    showLogin();
}

async function checkCurrentUser() {
    const result = await apiCall('/api/current_user');
    if (result.success) {
        document.getElementById('currentUser').textContent = result.username;
        currentPlayerName = result.username;
        await loadUserData();
        showMenu();
    } else {
        showLogin();
    }
}

// ==================== 用户数据系统 ====================
async function loadUserData() {
    if (currentPlayerName) {
        const result = await apiCall('/api/user_points');
        if (result.success) {
            userPoints = result.points;
        } else {
            const savedPoints = localStorage.getItem('user_points_' + currentPlayerName);
            userPoints = savedPoints ? parseInt(savedPoints) : 1000;
        }
        const savedCards = localStorage.getItem('user_cards_' + currentPlayerName);
        myCards = savedCards ? JSON.parse(savedCards) : {};
        const savedColors = localStorage.getItem('user_colors_' + currentPlayerName);
        unlockedColors = savedColors ? JSON.parse(savedColors) : ['red', 'blue', 'gray', 'yellow', 'green'];
        updatePointsDisplay();
        await saveUserData();
    }
}

async function saveUserData() {
    if (currentPlayerName) {
        localStorage.setItem('user_points_' + currentPlayerName, userPoints.toString());
        localStorage.setItem('user_cards_' + currentPlayerName, JSON.stringify(myCards));
        localStorage.setItem('user_colors_' + currentPlayerName, JSON.stringify(unlockedColors));
        await apiCall('/api/update_points', 'POST', { points: userPoints });
    }
}

function updatePointsDisplay() {
    const pointsEl = document.getElementById('currentPoints');
    const menuPointsEl = document.getElementById('menuPoints');
    if (pointsEl) pointsEl.textContent = userPoints;
    if (menuPointsEl) menuPointsEl.textContent = userPoints;
}

// ==================== 抽卡系统 ====================
function showGacha() {
    playSound('click');
    showPage('gachaPage');
    loadUserData().then(() => {
        updatePointsDisplay();
    });
    renderCardPool();
    renderMyCards();
    renderUnlockedColors();
    document.getElementById('gachaResult').textContent = '';
    document.getElementById('cardSlot').innerHTML = '<span class="card-placeholder">?</span>';
    document.getElementById('cardSlot').classList.remove('revealed');
}

function renderCardPool() {
    const poolList = document.getElementById('cardPoolList');
    if (!poolList) return;
    let html = '';
    for (const [cardId, card] of Object.entries(CARD_CONFIG)) {
        html += `<div class="pool-card" onclick="showCardEffect('${cardId}')">
            <div class="card-icon">${card.icon}</div>
            <div class="card-name">${card.name}</div>
            <div class="card-rarity rarity-${card.rarity}">${getRarityText(card.rarity)}</div>
        </div>`;
    }
    poolList.innerHTML = html;
}

function getRarityText(rarity) {
    const texts = { 'common': '普通', 'rare': '稀有', 'super-rare': '史诗', 'legendary': '传说' };
    return texts[rarity] || rarity;
}

function showCardEffect(cardId) {
    const card = CARD_CONFIG[cardId];
    showMessage(`${card.name}: ${card.effect}`);
}

function renderMyCards() {
    const myCardsEl = document.getElementById('myCards');
    if (!myCardsEl) return;
    if (Object.keys(myCards).length === 0) {
        myCardsEl.innerHTML = '<p style="text-align: center; color: #888; grid-column: 1/-1;">暂无卡牌</p>';
        return;
    }
    let html = '';
    for (const [cardId, count] of Object.entries(myCards)) {
        const card = CARD_CONFIG[cardId];
        if (card) {
            html += `<div class="my-card" onclick="useCard('${cardId}')">
                <div class="card-icon">${card.icon}</div>
                <div class="card-name">${card.name}</div>
                ${count > 1 ? `<div class="card-count">×${count}</div>` : ''}
            </div>`;
        }
    }
    myCardsEl.innerHTML = html;
}

function renderUnlockedColors() {
    const colorListEl = document.getElementById('unlockedColors');
    if (!colorListEl) return;
    const colorConfig = {
        'red': { icon: '🔴', class: 'player-color-red' },
        'blue': { icon: '🔵', class: 'player-color-blue' },
        'gray': { icon: '⚪', class: 'player-color-gray' },
        'yellow': { icon: '🟡', class: 'player-color-yellow' },
        'green': { icon: '🟢', class: 'player-color-green' },
        'purple': { icon: '💜', class: 'color-purple' },
        'gold': { icon: '🏆', class: 'color-gold' },
        'silver': { icon: '🌙', class: 'color-silver' },
        'pink': { icon: '🌸', class: 'color-pink' },
        'aurora': { icon: '🌈', class: 'color-aurora' },
        'neon': { icon: '💫', class: 'color-neon' }
    };
    let html = '';
    for (const colorId of unlockedColors) {
        const config = colorConfig[colorId];
        if (config) html += `<div class="unlocked-color-item ${config.class}">${config.icon}</div>`;
    }
    colorListEl.innerHTML = html;
}

async function doGacha() {
    if (userPoints < GACHA_COST) {
        showMessage('积分不足！需要 50 积分');
        playSound('error');
        return;
    }
    const deductResult = await apiCall('/api/deduct_points', 'POST', { amount: GACHA_COST });
    if (deductResult.success) {
        userPoints = deductResult.points;
        updatePointsDisplay();
        performGacha(1);
    } else {
        showMessage('积分不足！');
        playSound('error');
    }
}

async function doGachaMulti() {
    const multiCost = GACHA_COST * 10;
    if (userPoints < multiCost) {
        showMessage('积分不足！需要 500 积分');
        playSound('error');
        return;
    }
    const deductResult = await apiCall('/api/deduct_points', 'POST', { amount: multiCost });
    if (deductResult.success) {
        userPoints = deductResult.points;
        updatePointsDisplay();
        performGacha(10);
    } else {
        showMessage('积分不足！');
        playSound('error');
    }
}

function performGacha(count) {
    playSound('gacha');
    const results = [];
    for (let i = 0; i < count; i++) {
        const cardId = drawCard();
        results.push(cardId);
    }
    setTimeout(() => {
        const lastCardId = results[results.length - 1];
        const card = CARD_CONFIG[lastCardId];
        const cardSlot = document.getElementById('cardSlot');
        cardSlot.innerHTML = card.icon;
        cardSlot.classList.add('revealed');
        const resultEl = document.getElementById('gachaResult');
        if (count > 1) {
            resultEl.textContent = `十连抽完成！获得 ${count} 张卡牌`;
            resultEl.className = 'gacha-result';
        } else {
            const rarityText = getRarityText(card.rarity);
            resultEl.textContent = `获得：${card.name} (${rarityText})`;
            resultEl.className = `gacha-result ${card.rarity === 'legendary' ? 'super-rare' : card.rarity}`;
        }
        if (card.rarity === 'legendary') playSound('legendary');
        renderMyCards();
        renderUnlockedColors();
        saveUserData();
    }, 500);
}

function drawCard() {
    const rand = Math.random();
    let rarity;
    if (rand < GACHA_RARITY['legendary'].chance) rarity = 'legendary';
    else if (rand < GACHA_RARITY['legendary'].chance + GACHA_RARITY['super-rare'].chance) rarity = 'super-rare';
    else if (rand < GACHA_RARITY['legendary'].chance + GACHA_RARITY['super-rare'].chance + GACHA_RARITY['rare'].chance) rarity = 'rare';
    else rarity = 'common';
    
    const cards = GACHA_RARITY[rarity].cards;
    const cardId = cards[Math.floor(Math.random() * cards.length)];
    const card = CARD_CONFIG[cardId];
    
    if (card.type === 'color') {
        if (unlockedColors.includes(card.colorId)) return drawCard();
        else unlockedColors.push(card.colorId);
    }
    
    if (myCards[cardId]) myCards[cardId]++;
    else myCards[cardId] = 1;
    
    return cardId;
}

function useCard(cardId) {
    const card = CARD_CONFIG[cardId];
    if (!card) return;
    if (card.type === 'function') {
        if (document.getElementById('gamePage').classList.contains('active')) {
            activateCard(cardId);
        } else {
            showMessage('功能卡只能在对战中使用！');
            playSound('error');
        }
    } else if (card.type === 'color') {
        showMessage(`${card.name}: ${card.effect}`);
    }
}

// ==================== 页面导航 ====================
function showPage(pageId) {
    playSound('click');
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
}

function showLogin() { showPage('loginPage'); }
function showRegister() { showPage('registerPage'); }
function showMenu() { showPage('menuPage'); }
function showCreateRoom() { showPage('createRoomPage'); }
function showJoinRoom() { showPage('joinRoomPage'); }

async function showLeaderboard() {
    await updateLeaderboard();
    showPage('leaderboardPage');
}

function viewLeaderboard() { showLeaderboard(); }

document.getElementById('gridSize').addEventListener('change', function() {
    playSound('click');
    document.getElementById('customGrid').style.display = this.value === 'custom' ? 'block' : 'none';
});

// ==================== 房间系统 ====================
let roomCheckInterval = null;

async function createRoom() {
    playSound('click');
    const roomCode = document.getElementById('roomCode').value.trim();
    const gridSize = document.getElementById('gridSize').value;
    let rows, cols;
    if (gridSize === 'custom') {
        rows = parseInt(document.getElementById('customRows').value) || 5;
        cols = parseInt(document.getElementById('customCols').value) || 8;
    } else {
        [rows, cols] = gridSize.split(',').map(Number);
    }
    const result = await apiCall('/api/create_room', 'POST', { roomCode, rows, cols });
    if (result.success) {
        currentRoomCode = result.roomCode;
        const roomCodeEl = document.getElementById('waitingRoomCode');
        const player1El = document.getElementById('waitingPlayer1Name');
        if (roomCodeEl) roomCodeEl.textContent = result.roomCode;
        if (player1El) player1El.textContent = currentPlayerName;
        playSound('select');
        showPage('waitingPage');
        startRoomCheck();
    } else {
        alert(result.message);
        playSound('error');
    }
}

async function joinRoom() {
    playSound('click');
    const roomCode = document.getElementById('joinRoomCode').value.trim();
    const errorEl = document.getElementById('joinError');
    if (roomCode.length !== 6) {
        errorEl.textContent = '房间号必须是 6 位';
        errorEl.style.display = 'block';
        playSound('error');
        return;
    }
    const result = await apiCall('/api/join_room', 'POST', { roomCode });
    if (result.success) {
        currentRoomCode = roomCode;
        stopRoomCheck();
        playSound('select');
        showColorSelect(roomCode);
    } else {
        errorEl.textContent = result.message;
        errorEl.style.display = 'block';
        playSound('error');
    }
}

function startRoomCheck() {
    if (roomCheckInterval) clearInterval(roomCheckInterval);
    roomCheckInterval = setInterval(async () => {
        if (!currentRoomCode) return;
        try {
            const result = await apiCall(`/api/room_status/${currentRoomCode}`);
            if (result.success && result.room) {
                const player2El = document.getElementById('waitingPlayer2Name');
                if (player2El) player2El.textContent = result.room.player2 || '等待中...';
                if (result.room.status === 'playing' && result.room.player2) {
                    stopRoomCheck();
                    playSound('select');
                    setTimeout(() => showColorSelect(currentRoomCode), 500);
                }
            }
        } catch (error) {
            console.error('房间状态检查错误:', error);
        }
    }, 1000);
}

function stopRoomCheck() {
    if (roomCheckInterval) { clearInterval(roomCheckInterval); roomCheckInterval = null; }
}

async function cancelRoom() {
    playSound('click');
    if (!currentRoomCode) return;
    await apiCall(`/api/cancel_room/${currentRoomCode}`, 'POST');
    currentRoomCode = null;
    stopRoomCheck();
    showMenu();
}

// ==================== 颜色选择系统 ====================
async function showColorSelect(roomCode) {
    currentRoomCode = roomCode;
    isColorSelected = false;
    hasStartedGame = false;
    document.getElementById('colorSelectRoomCode').textContent = roomCode;
    document.getElementById('selectedColorName').textContent = '未选择';
    document.getElementById('confirmColorBtn').disabled = true;
    document.getElementById('confirmColorBtn').style.display = 'block';
    document.getElementById('colorWaitingMessage').style.display = 'none';
    selectedTempColor = null;
    renderColorOptions();
    showPage('colorSelectPage');
    await checkColorStatus();
    startColorCheck();
}

function renderColorOptions() {
    const container = document.getElementById('colorOptions');
    if (!container) return;
    const colorConfig = {
        'red': { name: '红色', icon: '🔴' },
        'blue': { name: '蓝色', icon: '🔵' },
        'gray': { name: '灰色', icon: '⚪' },
        'yellow': { name: '黄色', icon: '🟡' },
        'green': { name: '绿色', icon: '🟢' },
        'purple': { name: '紫色', icon: '💜' },
        'gold': { name: '金色', icon: '🏆' },
        'silver': { name: '银色', icon: '🌙' },
        'pink': { name: '粉色', icon: '🌸' },
        'aurora': { name: '极光', icon: '🌈' },
        'neon': { name: '荧光', icon: '💫' }
    };
    let html = '';
    for (const [colorId, config] of Object.entries(colorConfig)) {
        const isUnlocked = unlockedColors.includes(colorId);
        html += `<div class="color-option ${isUnlocked ? '' : 'locked'}" data-color="${colorId}" onclick="${isUnlocked ? `selectColor('${colorId}')` : ''}">
            <div class="color-preview ${getPlayerColorClass(colorId)}"></div>
            <span>${config.name}</span>
            ${!isUnlocked ? '<span style="font-size: 10px;">🔒</span>' : ''}
        </div>`;
    }
    container.innerHTML = html;
}

function getPlayerColorClass(colorId) {
    const map = {
        'red': 'player-color-red', 'blue': 'player-color-blue', 'gray': 'player-color-gray',
        'yellow': 'player-color-yellow', 'green': 'player-color-green', 'purple': 'player-color-purple',
        'gold': 'player-color-gold', 'silver': 'player-color-silver', 'pink': 'player-color-pink',
        'aurora': 'player-color-aurora', 'neon': 'player-color-neon'
    };
    return map[colorId] || '';
}

function selectColor(color) {
    playSound('click');
    selectedTempColor = color;
    document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
    document.querySelector(`.color-option[data-color="${color}"]`).classList.add('selected');
    const colorNames = {
        'red': '红色', 'blue': '蓝色', 'gray': '灰色', 'yellow': '黄色', 'green': '绿色',
        'purple': '紫色', 'gold': '金色', 'silver': '银色', 'pink': '粉色',
        'aurora': '极光色', 'neon': '荧光色'
    };
    document.getElementById('selectedColorName').textContent = colorNames[color];
    document.getElementById('confirmColorBtn').disabled = false;
    playSound('select');
}

async function confirmColor() {
    if (!selectedTempColor) return;
    playSound('click');
    const result = await apiCall('/api/select_color', 'POST', { roomCode: currentRoomCode, color: selectedTempColor });
    if (result.success) {
        isColorSelected = true;
        currentPlayerColor = selectedTempColor;
        document.getElementById('confirmColorBtn').style.display = 'none';
        document.getElementById('colorWaitingMessage').style.display = 'block';
        playSound('select');
        await checkColorStatus();
    } else {
        showMessage(result.message);
        playSound('error');
    }
}

let colorCheckInterval = null;

async function checkColorStatus() {
    if (!currentRoomCode) return;
    const result = await apiCall(`/api/color_status/${currentRoomCode}`);
    if (result.success && result.colors) {
        player1Color = result.colors.player1;
        player2Color = result.colors.player2;
        if (player1Color && player2Color && !hasStartedGame) {
            hasStartedGame = true;
            stopColorCheck();
            playSound('select');
            setTimeout(() => startGame(currentRoomCode), 300);
        }
    }
}

function startColorCheck() {
    if (colorCheckInterval) clearInterval(colorCheckInterval);
    colorCheckInterval = setInterval(async () => {
        if (!currentRoomCode || hasStartedGame) return;
        await checkColorStatus();
    }, 500);
}

function stopColorCheck() {
    if (colorCheckInterval) { clearInterval(colorCheckInterval); colorCheckInterval = null; }
}

// ==================== 游戏系统 ====================
let gameSyncInterval = null;
let hasShownEndMessage = false;

async function startGame(roomCode) {
    currentRoomCode = roomCode;
    hasShownEndMessage = false;
    gameScoreMultiplier = 1;
    skipNextTurn = false;
    canChangeNumber = false;
    moveHistory = [];
    usedCardsThisGame = {};
    changeMode = false;
    skipTurnActive = false;
    anyCardUsed = false;  // 修复①：重置卡牌使用标记
    
    const result = await apiCall(`/api/game/${roomCode}`);
    if (!result.success) {
        alert('游戏数据不存在');
        playSound('error');
        showMenu();
        return;
    }
    const game = result.game;
    if (currentPlayerName === game.player1) {
        currentPlayerColor = player1Color;
    } else {
        currentPlayerColor = player2Color;
    }
    document.getElementById('gameRoomCode').textContent = roomCode;
    setupPlayerInfo('player1', game.player1, player1Color, game.player1Score);
    setupPlayerInfo('player2', game.player2, player2Color, game.player2Score);
    windowCurrentGameData = game;
    updateGameDisplay(game);
    showPage('gamePage');
    playSound('select');
    renderAvailableCards();
    document.addEventListener('keydown', handleKeyPress);
    document.addEventListener('click', handleOutsideClick);
    if (gameSyncInterval) clearInterval(gameSyncInterval);
    gameSyncInterval = setInterval(() => syncGame(roomCode), 500);
}

function renderAvailableCards() {
    const container = document.getElementById('availableCards');
    if (!container) return;
    const functionCards = ['double_score', 'skip_turn', 'change_number'];
    let html = '';
    for (const cardId of functionCards) {
        const card = CARD_CONFIG[cardId];
        const hasCard = myCards[cardId] && myCards[cardId] > 0;
        // 修复①：检查是否已使用过任何卡牌
        const used = anyCardUsed;
        if (hasCard) {
            html += `<div class="available-card ${used ? 'used' : ''}" onclick="${used ? '' : `activateCard('${cardId}')`}">
                <span class="card-icon">${card.icon}</span>
                <span class="card-name">${card.name}</span>
            </div>`;
        }
    }
    if (html === '') {
        html = '<p style="color: #FFF; font-size: 12px;">暂无可用功能卡</p>';
    }
    container.innerHTML = html;
}

async function activateCard(cardId) {
    // 修复①：检查是否已使用过任何卡牌
    if (anyCardUsed) {
        showMessage('本局已使用过卡牌，无法再次使用！');
        playSound('error');
        return;
    }
    
    const result = await apiCall(`/api/game/${currentRoomCode}/apply_card`, 'POST', { card_type: cardId });
    if (result.success) {
        anyCardUsed = true;  // 修复①：标记已使用卡牌
        playSound('card');
        if (cardId === 'double_score') {
            updateMultiplierDisplay();
            showMessage('✨ 双重预言已激活！本局得分×2');
        } else if (cardId === 'skip_turn') {
            skipTurnActive = true;
            showMessage('⏳ 时间禁锢已激活！');
        } else if (cardId === 'change_number') {
            changeMode = true;
            showMessage('🔄 命运改写已激活！请选择要修改的格子');
        }
        renderAvailableCards();
    } else {
        showMessage(result.message);
        playSound('error');
    }
}

function updateMultiplierDisplay() {
    const game = windowCurrentGameData;
    if (!game) return;
    const p1Mult = game.player1Multiplier || 1;
    const p2Mult = game.player2Multiplier || 1;
    document.getElementById('player1Multiplier').textContent = p1Mult > 1 ? `×${p1Mult}` : '';
    document.getElementById('player2Multiplier').textContent = p2Mult > 1 ? `×${p2Mult}` : '';
}

function setupPlayerInfo(playerNum, playerName, color, score) {
    const prefix = playerNum.startsWith('final') ? 'finalPlayer' : 'player';
    const num = playerNum.replace('final', '');
    const infoEl = document.getElementById(`${prefix}${num}Info`);
    const labelEl = document.getElementById(`${prefix}${num}Label`);
    const nameEl = document.getElementById(`${prefix}${num}Name`);
    const scoreEl = document.getElementById(`${prefix}${num}Score`);
    if (infoEl) {
        infoEl.className = `player-info player-color-${color}`;
    }
    if (labelEl) labelEl.textContent = playerName === currentPlayerName ? '你' : '对手';
    if (nameEl) nameEl.textContent = playerName;
    if (scoreEl) scoreEl.textContent = score || 0;
}

function updateGameDisplay(game) {
    document.getElementById('player1Score').textContent = game.player1Score || 0;
    document.getElementById('player2Score').textContent = game.player2Score || 0;
    document.getElementById('player1Info').classList.remove('current-turn');
    document.getElementById('player2Info').classList.remove('current-turn');
    if (game.status === 'playing') {
        if (game.currentTurn === 'player1') {
            document.getElementById('player1Info').classList.add('current-turn');
        } else {
            document.getElementById('player2Info').classList.add('current-turn');
        }
    }
    updateMultiplierDisplay();
    renderGrid(game);
}

function renderGrid(game) {
    const container = document.getElementById('gridContainer');
    container.style.gridTemplateColumns = `repeat(${game.grid[0].length}, 60px)`;
    container.innerHTML = '';
    game.grid.forEach((row, rowIndex) => {
        row.forEach((cell, colIndex) => {
            const cellEl = document.createElement('div');
            cellEl.className = 'grid-cell';
            cellEl.dataset.row = rowIndex;
            cellEl.dataset.col = colIndex;
            if (cell) {
                cellEl.classList.add('filled', cell.color);
                if (cell.value === 'X' || cell.value === 'x') {
                    cellEl.textContent = '✕';
                } else {
                    cellEl.textContent = cell.value;
                }
                // 修复③④：命运改写模式下的格子样式
                if (changeMode && cell.turn === (currentPlayerName === game.player1 ? 'player1' : 'player2')) {
                    cellEl.classList.add('change-mode');
                    cellEl.style.cursor = 'pointer';
                    cellEl.onclick = () => selectChangeCell(rowIndex, colIndex, cell.value);
                }
            } else {
                cellEl.onclick = () => {
                    playSound('click');
                    selectCell(rowIndex, colIndex);
                };
            }
            container.appendChild(cellEl);
        });
    });
    if (selectedCell && !changeMode) {
        highlightSelectedCell();
        showInputPreview();
    }
}

function selectCell(rowIndex, colIndex) {
    if (!currentRoomCode) return;
    const game = windowCurrentGameData;
    if (!game || game.status !== 'playing') return;
    const isPlayer1 = currentPlayerName === game.player1;
    const currentTurnPlayer = isPlayer1 ? 'player1' : 'player2';
    if (skipTurnActive && game.currentTurn !== currentTurnPlayer) {
        skipTurnActive = false;
        return;
    }
    if (game.currentTurn !== currentTurnPlayer) {
        showMessage('不是你的回合！');
        playSound('error');
        return;
    }
    if (game.grid[rowIndex][colIndex]) {
        showMessage('该格子已被填充！');
        playSound('error');
        return;
    }
    selectedCell = { row: rowIndex, col: colIndex };
    inputBuffer = '';
    highlightSelectedCell();
    playSound('select');
    if (isMobile) setTimeout(() => openMobileKeyboard(), 200);
}

// 修复③④：选择要修改的格子，传入原值
function selectChangeCell(rowIndex, colIndex, oldValue) {
    if (!changeMode) return;
    selectedCell = { row: rowIndex, col: colIndex };
    inputBuffer = '';
    highlightSelectedCell();
    // 修复④：显示原值，让用户知道要修改什么
    showMessage(`修改格子：${oldValue} → 请输入新内容`);
    if (isMobile) setTimeout(() => openMobileKeyboard(), 200);
}

function highlightSelectedCell() {
    document.querySelectorAll('.grid-cell').forEach(cell => cell.classList.remove('selected'));
    if (selectedCell) {
        const cells = document.querySelectorAll('.grid-cell');
        const game = windowCurrentGameData;
        if (game) {
            const index = selectedCell.row * game.grid[0].length + selectedCell.col;
            if (cells[index]) cells[index].classList.add('selected');
        }
    }
}

function showInputPreview() {
    document.querySelectorAll('.grid-cell').forEach(cell => cell.classList.remove('input-preview'));
    if (selectedCell && inputBuffer) {
        const cells = document.querySelectorAll('.grid-cell');
        const game = windowCurrentGameData;
        if (game) {
            const index = selectedCell.row * game.grid[0].length + selectedCell.col;
            if (cells[index]) {
                cells[index].classList.add('input-preview');
                cells[index].textContent = inputBuffer.toUpperCase() === 'X' ? '✕' : inputBuffer;
            }
        }
    } else if (selectedCell) {
        const cells = document.querySelectorAll('.grid-cell');
        const game = windowCurrentGameData;
        if (game) {
            const index = selectedCell.row * game.grid[0].length + selectedCell.col;
            if (cells[index] && !game.grid[selectedCell.row][selectedCell.col]) {
                cells[index].textContent = '';
            }
        }
    }
}

function handleKeyPress(event) {
    if (isMobile && document.getElementById('mobileKeyboard').classList.contains('show')) return;
    if (!document.getElementById('gamePage').classList.contains('active')) return;
    if (!selectedCell || !currentRoomCode) return;
    const game = windowCurrentGameData;
    if (!game || game.status !== 'playing') return;
    const isPlayer1 = currentPlayerName === game.player1;
    const currentTurnPlayer = isPlayer1 ? 'player1' : 'player2';
    if (game.currentTurn !== currentTurnPlayer) return;
    const key = event.key;
    if (key === 'Enter') {
        event.preventDefault();
        if (inputBuffer.trim() !== '') {
            if (changeMode) {
                submitChangeInput(inputBuffer.trim());
            } else {
                if (inputBuffer.toUpperCase() === 'X') {
                    submitInput('X');
                } else if (/^\d+$/.test(inputBuffer.trim())) {
                    submitInput(inputBuffer.trim());
                } else {
                    showMessage('请输入有效数字或 X');
                    playSound('error');
                    inputBuffer = '';
                    showInputPreview();
                }
            }
        }
        return;
    }
    if (key === 'Escape') {
        event.preventDefault();
        playSound('click');
        inputBuffer = '';
        if (changeMode) {
            changeMode = false;
            selectedCell = null;
            renderGrid(game);
        } else {
            clearInput();
        }
        return;
    }
    if (key === 'Backspace') {
        event.preventDefault();
        playSound('click');
        inputBuffer = inputBuffer.slice(0, -1);
        showInputPreview();
        return;
    }
    if (/^[0-9Xx]$/.test(key)) {
        event.preventDefault();
        playSound('click');
        inputBuffer += key;
        showInputPreview();
    }
}

function handleOutsideClick(event) {
    if (event.target.id === 'gridContainer' || event.target.classList.contains('container') ||
        event.target.classList.contains('page') || event.target.classList.contains('panel') ||
        event.target.classList.contains('input-section') || event.target.classList.contains('cards-section')) {
        if (changeMode) {
            changeMode = false;
            selectedCell = null;
            renderGrid(windowCurrentGameData);
        } else {
            clearInput();
        }
    }
}

async function submitInput(value) {
    if (!selectedCell || !currentRoomCode) {
        showMessage('请先选择一个格子！');
        playSound('error');
        return;
    }
    const { row, col } = selectedCell;
    const result = await apiCall(`/api/game/${currentRoomCode}/move`, 'POST', {
        row, col, value: value, color: currentPlayerColor
    });
    if (result.success) {
        playSound('place');
        moveHistory.push({ row, col, value, player: currentPlayerName });
        selectedCell = null;
        inputBuffer = '';
        windowCurrentGameData = result.game;
        updateGameDisplay(result.game);
        if (result.game.rowScores || result.game.colScores) {
            const hasNewScore = Object.keys(result.game.rowScores || {}).length > 0 || Object.keys(result.game.colScores || {}).length > 0;
            if (hasNewScore) playSound('score');
        }
        if (result.game.status === 'ended' && !hasShownEndMessage) {
            hasShownEndMessage = true;
            const game = result.game;
            const myScore = currentPlayerName === game.player1 ? game.player1Score : game.player2Score;
            const multiplier = currentPlayerName === game.player1 ? (game.player1Multiplier || 1) : (game.player2Multiplier || 1);
            const finalScore = myScore * multiplier;
            document.getElementById('scoreGained').textContent = finalScore;
            setTimeout(() => endGameLocal(), 1000);
        }
    } else {
        showMessage(result.message);
        playSound('error');
        inputBuffer = '';
        showInputPreview();
    }
}

// 修复③：命运改写后重新计算得分
async function submitChangeInput(value) {
    if (!selectedCell || !currentRoomCode) {
        showMessage('请先选择一个格子！');
        playSound('error');
        return;
    }
    const { row, col } = selectedCell;
    const game = windowCurrentGameData;
    const oldScoreP1 = game.player1Score;
    const oldScoreP2 = game.player2Score;
    
    const result = await apiCall(`/api/game/${currentRoomCode}/change_move`, 'POST', {
        row, col, value: value
    });
    if (result.success) {
        playSound('place');
        changeMode = false;
        selectedCell = null;
        inputBuffer = '';
        windowCurrentGameData = result.game;
        updateGameDisplay(result.game);
        
        // 修复③：计算分数变化并显示
        const newScoreP1 = result.game.player1Score;
        const newScoreP2 = result.game.player2Score;
        const scoreDiffP1 = newScoreP1 - oldScoreP1;
        const scoreDiffP2 = newScoreP2 - oldScoreP2;
        
        if (scoreDiffP1 !== 0 || scoreDiffP2 !== 0) {
            let msg = '✅ 修改成功！';
            if (scoreDiffP1 !== 0) msg += ` 玩家 1 分数${scoreDiffP1 > 0 ? '+' : ''}${scoreDiffP1}`;
            if (scoreDiffP2 !== 0) msg += ` 玩家 2 分数${scoreDiffP2 > 0 ? '+' : ''}${scoreDiffP2}`;
            showMessage(msg);
            playSound('score');
        } else {
            showMessage('✅ 修改成功！消耗一回合');
        }
        
        if (result.game.status === 'ended' && !hasShownEndMessage) {
            hasShownEndMessage = true;
            setTimeout(() => endGameLocal(), 1000);
        }
    } else {
        showMessage(result.message);
        playSound('error');
    }
}

function showMessage(text) {
    if (showMessageTimeout) clearTimeout(showMessageTimeout);
    const existingMsg = document.querySelector('.message-popup');
    if (existingMsg) existingMsg.remove();
    const msg = document.createElement('div');
    msg.className = 'message-popup';
    msg.textContent = text;
    msg.style.cssText = `position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #D9534F; color: #FFF; padding: 15px 30px; border: 3px solid #000; font-family: 'Press Start 2P', cursive; font-size: 14px; z-index: 1000;`;
    document.body.appendChild(msg);
    showMessageTimeout = setTimeout(() => { msg.remove(); showMessageTimeout = null; }, 1500);
}

function clearInput() {
    selectedCell = null;
    inputBuffer = '';
    document.querySelectorAll('.grid-cell').forEach(cell => cell.classList.remove('selected', 'input-preview'));
}

async function syncGame(roomCode) {
    const result = await apiCall(`/api/game/${roomCode}`);
    if (!result.success) {
        stopGameSync();
        showMenu();
        return;
    }
    windowCurrentGameData = result.game;
    updateGameDisplay(result.game);
    if (result.game.status === 'ended' && !hasShownEndMessage) {
        hasShownEndMessage = true;
        stopGameSync();
        setTimeout(() => endGameLocal(), 1000);
    }
}

function stopGameSync() {
    if (gameSyncInterval) { clearInterval(gameSyncInterval); gameSyncInterval = null; }
}

async function endGame() {
    if (!currentRoomCode) return;
    if (!confirm('确定要结束游戏吗？')) return;
    playSound('click');
    await apiCall(`/api/game/${currentRoomCode}/end`, 'POST');
    hasShownEndMessage = true;
    endGameLocal();
}

// 修复②：游戏结束后所有玩家都跳转到结束界面
function endGameLocal() {
    stopGameSync();
    stopColorCheck();
    document.removeEventListener('keydown', handleKeyPress);
    document.removeEventListener('click', handleOutsideClick);
    const game = windowCurrentGameData;
    if (!game) return;
    setupPlayerInfo('finalPlayer1', game.player1, player1Color, game.player1Score);
    setupPlayerInfo('finalPlayer2', game.player2, player2Color, game.player2Score);
    document.getElementById('finalPlayer1Score').textContent = game.player1Score || 0;
    document.getElementById('finalPlayer2Score').textContent = game.player2Score || 0;
    let winnerText = '', resultText = '';
    const p1Final = game.player1Score * (game.player1Multiplier || 1);
    const p2Final = game.player2Score * (game.player2Multiplier || 1);
    if (p1Final > p2Final) {
        winnerText = '🏆 玩家 1 获胜！';
        resultText = `玩家 1 ${p1Final} - ${p2Final} 玩家 2`;
        playSound('win');
    } else if (p2Final > p1Final) {
        winnerText = '🏆 玩家 2 获胜！';
        resultText = `玩家 2 ${p2Final} - ${p1Final} 玩家 1`;
        playSound('win');
    } else {
        winnerText = '🤝 平局！';
        resultText = `双方得分：${p1Final}`;
        playSound('draw');
    }
    document.getElementById('winnerText').textContent = winnerText;
    document.getElementById('gameResult').textContent = resultText;
    showPage('gameOverPage');
}

// ==================== 排行榜系统 ====================
async function updateLeaderboard() {
    playSound('click');
    const result = await apiCall('/api/leaderboard');
    const container = document.getElementById('leaderboardContent');
    if (!result.success || !result.leaderboard || result.leaderboard.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #888; font-size: 13px;">暂无数据</p>';
        return;
    }
    const leaderboard = result.leaderboard;
    let html = '<table><tr><th>排名</th><th>玩家</th><th>总积分</th><th>胜</th><th>负</th><th>平</th></tr>';
    leaderboard.forEach((player, index) => {
        html += `<tr><td>${index + 1}</td><td>${player.name}</td><td style="color: #FFD700;">${player.totalScore}</td><td style="color: #5CB85C;">${player.wins}</td><td style="color: #D9534F;">${player.losses}</td><td style="color: #888;">${player.draws}</td></tr>`;
    });
    html += '</table>';
    container.innerHTML = html;
}

// ==================== 初始化 ====================
window.addEventListener('load', () => {
    checkMobileDevice();
    document.addEventListener('click', () => {
        if (audioContext.state === 'suspended') audioContext.resume();
    }, { once: true });
    checkCurrentUser();
});

window.addEventListener('beforeunload', () => {
    stopRoomCheck();
    stopGameSync();
    stopColorCheck();
    document.removeEventListener('keydown', handleKeyPress);
    document.removeEventListener('click', handleOutsideClick);
    if (showMessageTimeout) clearTimeout(showMessageTimeout);
});