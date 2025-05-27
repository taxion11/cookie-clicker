// ゲーム状態管理
class CookieClickerGame {
    constructor() {
        this.gameData = {
            user_id: 'player1', // 後で認証機能実装時に変更
            cookies: 0,
            cookiesPerSecond: 0,
            clickPower: 1,
            upgrades: {},
            totalClicks: 0,
            startTime: Date.now()
        };

        this.upgrades = [];
        this.autoSaveInterval = null;
        this.cpsInterval = null;
        this.isLoading = false;

        this.init();
    }

    async init() {
        this.showLoading(true);

        try {
            // DOMエレメントの取得
            this.cookieButton = document.getElementById('cookie-button');
            this.cookieCount = document.getElementById('cookie-count');
            this.cpsCount = document.getElementById('cps-count');
            this.clickPower = document.getElementById('click-power');
            this.totalClicksElement = document.getElementById('total-clicks');
            this.upgradesList = document.getElementById('upgrades-list');
            this.gameLog = document.getElementById('game-log');
            this.clickAnimation = document.getElementById('click-animation');

            // イベントリスナーの設定
            this.setupEventListeners();

            // ゲームデータの読み込み
            await this.loadGameData();

            // UI更新
            this.updateUI();

            // 自動保存開始（30秒間隔）
            this.startAutoSave();

            // CPS計算開始（1秒間隔）
            this.startCPSCalculation();

            this.addToLog('🎮 Game initialized successfully! (Direct Python API connection)');

        } catch (error) {
            console.error('Game initialization failed:', error);
            this.addToLog('❌ Failed to initialize game');
        }

        this.showLoading(false);
    }

    setupEventListeners() {
        // クッキークリック
        this.cookieButton.addEventListener('click', (e) => this.clickCookie(e));

        // コントロールボタン
        document.getElementById('save-game').addEventListener('click', () => this.saveGame());
        document.getElementById('load-game').addEventListener('click', () => this.loadGame());
        document.getElementById('reset-game').addEventListener('click', () => this.resetGame());

        // キーボードショートカット
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space') {
                e.preventDefault();
                this.clickCookie();
            }
        });
    }

    async loadGameData() {
        try {
            console.log('Loading game data from Python API...');
            // 修正: Python APIに直接接続
            const response = await fetch(`http://localhost:8001/api/v1/game/${this.gameData.user_id}`);

            if (response.ok) {
                const data = await response.json();
                console.log('Python API response:', data);

                if (data.game_data) {
                    // サーバーデータで更新
                    this.gameData.cookies = data.game_data.cookies || 0;
                    this.gameData.cookiesPerSecond = data.game_data.cookies_per_second || 0;
                    this.gameData.clickPower = data.game_data.click_power || 1;
                    this.gameData.upgrades = data.game_data.upgrades || {};
                    this.gameData.totalClicks = data.game_data.total_clicks || 0;
                }

                if (data.upgrades && data.upgrades.length > 0) {
                    this.upgrades = data.upgrades;
                    console.log('Loaded upgrades from API:', this.upgrades);
                } else {
                    // フォールバック: デフォルトアップグレードを使用
                    console.log('No upgrades from API, using default upgrades');
                    this.upgrades = [
                        {
                            id: "cursor",
                            name: "Cursor",
                            description: "Clicks cookies for you automatically",
                            base_cost: 15,
                            current_cost: 15,
                            cps_boost: 1,
                            click_boost: 0,
                            owned: 0
                        },
                        {
                            id: "grandma",
                            name: "Grandma",
                            description: "A nice grandma to bake more cookies",
                            base_cost: 100,
                            current_cost: 100,
                            cps_boost: 5,
                            click_boost: 0,
                            owned: 0
                        },
                        {
                            id: "farm",
                            name: "Cookie Farm",
                            description: "Grows cookie plants!",
                            base_cost: 1100,
                            current_cost: 1100,
                            cps_boost: 47,
                            click_boost: 0,
                            owned: 0
                        },
                        {
                            id: "click_power",
                            name: "Better Clicks",
                            description: "Each click gives more cookies",
                            base_cost: 50,
                            current_cost: 50,
                            cps_boost: 0,
                            click_boost: 1,
                            owned: 0
                        }
                    ];
                }

                this.renderUpgrades();
                this.addToLog('📁 Game data loaded from Python API');

            } else {
                console.error('Failed to load game data:', response.status);
                this.addToLog('⚠️ Using default game data');
                this.setDefaultUpgrades();
            }
        } catch (error) {
            console.error('Failed to load game data:', error);
            this.addToLog('⚠️ Failed to connect to Python API, using local data');
            this.setDefaultUpgrades();
        }
    }

    setDefaultUpgrades() {
        this.upgrades = [
            {
                id: "cursor",
                name: "Cursor",
                description: "Clicks cookies for you automatically",
                base_cost: 15,
                current_cost: 15,
                cps_boost: 1,
                click_boost: 0,
                owned: 0
            },
            {
                id: "grandma",
                name: "Grandma",
                description: "A nice grandma to bake more cookies",
                base_cost: 100,
                current_cost: 100,
                cps_boost: 5,
                click_boost: 0,
                owned: 0
            }
        ];
        this.renderUpgrades();
    }

    async clickCookie(event) {
        // 連続クリック防止
        if (this.isLoading) return;

        try {
            this.isLoading = true;

            // クリックアニメーション（即座に表示）
            this.showClickAnimation(event);

            // 修正: Python APIに直接クリック送信
            console.log('Sending click to Python API...');
            const response = await fetch(`http://localhost:8001/api/v1/game/${this.gameData.user_id}/click`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    click_power: this.gameData.clickPower
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Python API click response:', data);

                // サーバーレスポンスでゲームデータを更新
                if (data.total_cookies !== undefined) {
                    this.gameData.cookies = data.total_cookies;
                }
                if (data.total_clicks !== undefined) {
                    this.gameData.totalClicks = data.total_clicks;
                }
                if (data.click_power !== undefined) {
                    this.gameData.clickPower = data.click_power;
                }

                // UI更新
                this.updateUI();

                // 成功ログ
                this.addToLog(`🍪 +${data.cookies_earned || this.gameData.clickPower} cookies! (Total: ${data.total_cookies})`);

                // 成果チェック
                this.checkAchievements();

            } else {
                console.error('Click request failed:', response.status);
                // フォールバック: ローカル更新
                this.gameData.cookies += this.gameData.clickPower;
                this.gameData.totalClicks++;
                this.updateUI();
                this.addToLog('🍪 Cookie clicked (local fallback)');
            }

        } catch (error) {
            console.error('Click processing failed:', error);
            // エラー時のフォールバック
            this.gameData.cookies += this.gameData.clickPower;
            this.gameData.totalClicks++;
            this.updateUI();
            this.addToLog('🍪 Cookie clicked (error fallback)');
        } finally {
            this.isLoading = false;
        }
    }

    showClickAnimation(event) {
        const animation = this.clickAnimation;
        animation.textContent = `+${this.gameData.clickPower}`;
        animation.style.display = 'block';
        animation.style.opacity = '1';

        // イベントがある場合は、マウス位置に表示
        if (event) {
            const rect = this.cookieButton.getBoundingClientRect();
            animation.style.left = (event.clientX - rect.left) + 'px';
            animation.style.top = (event.clientY - rect.top) + 'px';
        }

        // アニメーション実行
        animation.style.transform = 'translateY(-50px)';
        animation.style.opacity = '0';

        setTimeout(() => {
            animation.style.display = 'none';
            animation.style.transform = 'translateY(0)';
            animation.style.opacity = '1';
        }, 1000);
    }

    async purchaseUpgrade(upgradeId) {
        if (this.isLoading) return;

        try {
            this.isLoading = true;

            const upgrade = this.upgrades.find(u => u.id === upgradeId);
            if (!upgrade) return;

            console.log('Purchasing upgrade via Python API:', upgradeId);

            // 修正: Python APIに直接アップグレード購入送信
            const response = await fetch(`http://localhost:8001/api/v1/game/${this.gameData.user_id}/upgrade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    upgrade_id: upgradeId
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Python API upgrade response:', data);

                // サーバーレスポンスでゲームデータを更新
                if (data.remaining_cookies !== undefined) {
                    this.gameData.cookies = data.remaining_cookies;
                }
                if (data.new_cps !== undefined) {
                    this.gameData.cookiesPerSecond = data.new_cps;
                }
                if (data.new_click_power !== undefined) {
                    this.gameData.clickPower = data.new_click_power;
                }

                // アップグレード所有数更新
                if (data.owned_count !== undefined) {
                    this.gameData.upgrades[upgradeId] = data.owned_count;
                    // アップグレードリストも更新
                    upgrade.owned = data.owned_count;
                    upgrade.current_cost = data.cost || Math.floor(upgrade.current_cost * 1.15);
                }

                // UI更新（アップグレードリストを再読み込み）
                await this.loadGameData();
                this.updateUI();

                this.addToLog(`🛍️ Purchased ${upgrade.name}! Cost: ${data.cost} cookies`);
                this.showAchievement(`Purchased ${upgrade.name}!`);

            } else {
                const errorData = await response.json().catch(() => ({}));
                console.error('Upgrade purchase failed:', response.status, errorData);
                this.addToLog(`💰 ${errorData.detail || 'Purchase failed'}`);
            }

        } catch (error) {
            console.error('Upgrade purchase failed:', error);
            this.addToLog(`❌ Purchase failed: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    renderUpgrades() {
        this.upgradesList.innerHTML = '';

        this.upgrades.forEach(upgrade => {
            const upgradeElement = document.createElement('div');
            upgradeElement.className = 'upgrade-item';

            const canAfford = this.gameData.cookies >= upgrade.current_cost;
            if (!canAfford) {
                upgradeElement.classList.add('unaffordable');
            }

            upgradeElement.innerHTML = `
                <div class="upgrade-info">
                    <h4>${upgrade.name}</h4>
                    <p>${upgrade.description}</p>
                    <div class="upgrade-stats">
                        ${upgrade.cps_boost > 0 ? `+${upgrade.cps_boost} CPS` : ''}
                        ${upgrade.click_boost > 0 ? `+${upgrade.click_boost} Click Power` : ''}
                    </div>
                </div>
                <div class="upgrade-purchase">
                    <div class="upgrade-cost">${this.formatNumber(upgrade.current_cost)} 🍪</div>
                    <div class="upgrade-owned">Owned: ${upgrade.owned || 0}</div>
                    <button class="upgrade-button" ${!canAfford ? 'disabled' : ''}>
                        Buy
                    </button>
                </div>
            `;

            const buyButton = upgradeElement.querySelector('.upgrade-button');
            buyButton.addEventListener('click', () => this.purchaseUpgrade(upgrade.id));

            this.upgradesList.appendChild(upgradeElement);
        });
    }

    updateUI() {
        this.cookieCount.textContent = this.formatNumber(this.gameData.cookies);
        this.cpsCount.textContent = this.formatNumber(this.gameData.cookiesPerSecond);
        this.clickPower.textContent = this.formatNumber(this.gameData.clickPower);
        this.totalClicksElement.textContent = this.formatNumber(this.gameData.totalClicks);

        // アップグレードボタンの状態更新
        this.renderUpgrades();
    }

    startCPSCalculation() {
        this.cpsInterval = setInterval(() => {
            if (this.gameData.cookiesPerSecond > 0) {
                this.gameData.cookies += this.gameData.cookiesPerSecond;
                this.updateUI();
            }
        }, 1000);
    }

    startAutoSave() {
        this.autoSaveInterval = setInterval(() => {
            this.saveGame(true); // サイレント保存
        }, 30000); // 30秒間隔
    }

    async saveGame(silent = false) {
        try {
            // 修正: Python APIに直接保存
            const response = await fetch(`http://localhost:8001/api/v1/game/${this.gameData.user_id}/save`, {
                method: 'GET'
            });

            if (response.ok) {
                if (!silent) {
                    this.addToLog('💾 Game saved to DynamoDB!');
                    this.showAchievement('Game Saved!');
                }
            }
        } catch (error) {
            console.error('Save failed:', error);
            if (!silent) {
                this.addToLog('❌ Save failed');
            }
        }
    }

    async loadGame() {
        try {
            this.showLoading(true);
            await this.loadGameData();
            this.updateUI();
            this.addToLog('📁 Game loaded from DynamoDB!');
            this.showAchievement('Game Loaded!');
        } catch (error) {
            console.error('Load failed:', error);
            this.addToLog('❌ Load failed');
        } finally {
            this.showLoading(false);
        }
    }

    resetGame() {
        if (confirm('Are you sure you want to reset your game? This cannot be undone!')) {
            this.gameData = {
                user_id: this.gameData.user_id,
                cookies: 0,
                cookiesPerSecond: 0,
                clickPower: 1,
                upgrades: {},
                totalClicks: 0,
                startTime: Date.now()
            };

            // アップグレードのリセット
            this.upgrades.forEach(upgrade => {
                upgrade.owned = 0;
                upgrade.current_cost = upgrade.base_cost || Math.floor(upgrade.current_cost / Math.pow(1.15, upgrade.owned || 0));
            });

            this.updateUI();
            this.addToLog('🔄 Game reset successfully!');
        }
    }

    checkAchievements() {
        const achievements = [
            { id: 'first_click', threshold: 1, message: 'First Click!', property: 'totalClicks' },
            { id: 'hundred_cookies', threshold: 100, message: '100 Cookies!', property: 'cookies' },
            { id: 'thousand_cookies', threshold: 1000, message: '1,000 Cookies!', property: 'cookies' },
            { id: 'click_master', threshold: 100, message: 'Click Master! (100 clicks)', property: 'totalClicks' },
        ];

        achievements.forEach(achievement => {
            if (this.gameData[achievement.property] >= achievement.threshold) {
                const storageKey = `achievement_${achievement.id}`;
                if (!localStorage.getItem(storageKey)) {
                    localStorage.setItem(storageKey, 'true');
                    this.showAchievement(achievement.message);
                }
            }
        });
    }

    showAchievement(message) {
        const notification = document.getElementById('achievement-notification');
        const text = notification.querySelector('.achievement-text');

        text.textContent = message;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    addToLog(message) {
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('p');
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;

        this.gameLog.appendChild(logEntry);

        // ログの最大数を制限（最新50件）
        while (this.gameLog.children.length > 50) {
            this.gameLog.removeChild(this.gameLog.firstChild);
        }

        // 最新ログまでスクロール
        this.gameLog.scrollTop = this.gameLog.scrollHeight;
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        loading.style.display = show ? 'flex' : 'none';
    }

    formatNumber(num) {
        if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
        if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
        return Math.floor(num).toString();
    }

    // クリーンアップ（ページを離れるときに呼ぶ）
    cleanup() {
        if (this.autoSaveInterval) clearInterval(this.autoSaveInterval);
        if (this.cpsInterval) clearInterval(this.cpsInterval);
    }
}

// ゲーム初期化
let game;

document.addEventListener('DOMContentLoaded', () => {
    game = new CookieClickerGame();
});

// ページを離れるときの処理
window.addEventListener('beforeunload', () => {
    if (game) {
        game.saveGame(true); // サイレント保存
        game.cleanup();
    }
});