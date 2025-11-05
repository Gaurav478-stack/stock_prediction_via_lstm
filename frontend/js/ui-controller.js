class UIController {
    constructor() {
        this.currentView = 'dashboard';
        this.currentStock = null;
        this.requestCache = new Map();
        this.requestQueue = [];
        this.maxConcurrentRequests = 5;
        this.dashboardPortfolioChart = null;
    }

    init() {
        try {
            console.log('Step 1: Checking if landing page should be shown...');
            
            // Check if user has visited before
            const hasVisited = localStorage.getItem('hasVisited');
            
            if (!hasVisited) {
                // First time visitor - show landing page
                this.showLandingPage();
            } else {
                // Returning user - go straight to app
                this.startApp();
            }
            
            console.log('Initialization complete');
        } catch (error) {
            console.error('Initialization error:', error);
            throw error;
        }
    }
    
    showLandingPage() {
        const landingPage = document.getElementById('landingPage');
        const mainApp = document.getElementById('mainApp');
        
        if (landingPage) landingPage.style.display = 'flex';
        if (mainApp) mainApp.style.display = 'none';
        
        // Bind get started button
        const getStartedBtn = document.getElementById('getStartedBtn');
        if (getStartedBtn) {
            getStartedBtn.addEventListener('click', () => {
                localStorage.setItem('hasVisited', 'true');
                this.startApp();
                
                // Animate transition
                landingPage.style.opacity = '0';
                landingPage.style.transition = 'opacity 0.5s ease';
                setTimeout(() => {
                    landingPage.style.display = 'none';
                    mainApp.style.display = 'block';
                    mainApp.style.opacity = '0';
                    setTimeout(() => {
                        mainApp.style.opacity = '1';
                        mainApp.style.transition = 'opacity 0.5s ease';
                    }, 50);
                }, 500);
            });
        }
    }
    
    startApp() {
        const landingPage = document.getElementById('landingPage');
        const mainApp = document.getElementById('mainApp');
        
        if (landingPage) landingPage.style.display = 'none';
        if (mainApp) mainApp.style.display = 'block';
        
        console.log('Step 1: Hiding API key setup...');
        this.hideApiKeySetup();
        
        console.log('Step 2: Binding events...');
        this.bindEvents();
        
        console.log('Step 3: Initializing charts...');
        this.initializeCharts();
        
        console.log('Step 4: Loading dashboard...');
        this.loadDashboard();
    }
    
    // XSS Protection - Sanitize HTML
    sanitizeHTML(str) {
        const temp = document.createElement('div');
        temp.textContent = str;
        return temp.innerHTML;
    }
    
    // Validate symbol format
    validateSymbol(symbol) {
        if (!symbol || typeof symbol !== 'string') return false;
        // Allow uppercase letters, numbers, dots (for Indian stocks), hyphens, and carets
        // Extended length for Indian stocks with .NS/.BO suffix
        return /^[A-Z0-9.\-^]{1,15}$/.test(symbol.toUpperCase());
    }
    
    // Prevent rapid-fire requests (debounce)
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    hideApiKeySetup() {
        const apiKeySetup = document.getElementById('apiKeySetup');
        if (apiKeySetup) apiKeySetup.style.display = 'none';
    }

    bindEvents() {
        // Nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchView(link.dataset.page);
            });
        });
        
        // Search
        const searchInput = document.getElementById('stockSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        }
        
        // Buttons - add null checks
        const editWatchlist = document.getElementById('editWatchlist');
        if (editWatchlist) editWatchlist.addEventListener('click', this.editWatchlist.bind(this));
        
        const addToWatchlist = document.getElementById('addToWatchlist');
        if (addToWatchlist) addToWatchlist.addEventListener('click', this.addToWatchlist.bind(this));
        
        const viewAnalysis = document.getElementById('viewAnalysis');
        if (viewAnalysis) viewAnalysis.addEventListener('click', this.viewAdvancedAnalysis.bind(this));
        
        const runAnalysis = document.getElementById('runAnalysis');
        if (runAnalysis) runAnalysis.addEventListener('click', this.runAdvancedAnalysis.bind(this));
        
        const timeframeSelect = document.getElementById('timeframeSelect');
        if (timeframeSelect) timeframeSelect.addEventListener('change', this.changeTimeframe.bind(this));
        
        // Portfolio view buttons
        const addHoldingBtn = document.getElementById('addHoldingBtn');
        if (addHoldingBtn) addHoldingBtn.addEventListener('click', () => this.addHolding());
        
        const saveHoldingBtn = document.getElementById('saveHoldingBtn');
        if (saveHoldingBtn) saveHoldingBtn.addEventListener('click', () => this.saveHolding());
        
        const cancelHoldingBtn = document.getElementById('cancelHoldingBtn');
        if (cancelHoldingBtn) cancelHoldingBtn.addEventListener('click', () => this.closeModal());
        
        const closeModal = document.getElementById('closeModal');
        if (closeModal) closeModal.addEventListener('click', () => this.closeModal());
        
        const viewPortfolio = document.getElementById('viewPortfolio');
        if (viewPortfolio) viewPortfolio.addEventListener('click', () => this.switchView('portfolio'));
        
        // Market tabs
        const marketTabs = document.querySelectorAll('.market-tab');
        marketTabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchMarketView(tab.dataset.market));
        });
        
        // News view filter
        // News filter handlers
        const newsFilterTabs = document.querySelectorAll('.news-filter-tab');
        newsFilterTabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                newsFilterTabs.forEach(t => t.classList.remove('active'));
                e.target.closest('.news-filter-tab').classList.add('active');
                this.loadNewsView();
            });
        });
        
        const loadMoreBtn = document.getElementById('loadMoreNews');
        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => this.loadMoreNews());
        }
        
        const moreNews = document.getElementById('moreNews');
        if (moreNews) moreNews.addEventListener('click', () => this.switchView('news'));
        
        // AI Prediction buttons
        const runLSTMBtn = document.getElementById('runLSTMPrediction');
        if (runLSTMBtn) runLSTMBtn.addEventListener('click', () => this.runLSTMPrediction());
        
        const runTradingBtn = document.getElementById('runTradingAgent');
        if (runTradingBtn) runTradingBtn.addEventListener('click', () => this.runTradingAgent());
        
        // Visualization buttons
        const loadComprehensiveBtn = document.getElementById('loadComprehensiveAnalysis');
        if (loadComprehensiveBtn) loadComprehensiveBtn.addEventListener('click', () => this.loadComprehensiveVisualization());
        
        const loadEnhancedBtn = document.getElementById('loadEnhancedDashboard');
        if (loadEnhancedBtn) loadEnhancedBtn.addEventListener('click', () => this.loadEnhancedDashboard());
    }

    initializeCharts() {
        try {
            chartService.initMarketChart();
            chartService.initPortfolioChart();
            chartService.initStockDetailChart();
        } catch (error) {
            console.error('Chart initialization error:', error);
        }
    }

    async switchView(view) {
        this.currentView = view;
        
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === view);
        });
        
        // Hide all views
        const views = ['dashboardView', 'stockDetailView', 'portfolioView', 'newsView', 'analysisView'];
        views.forEach(viewId => {
            const element = document.getElementById(viewId);
            if (element) element.style.display = 'none';
        });
        
        // Show selected view
        switch(view) {
            case 'dashboard':
                document.getElementById('dashboardView').style.display = 'block';
                await this.loadDashboard();
                break;
            case 'markets':
                document.getElementById('stockDetailView').style.display = 'block';
                break;
            case 'portfolio':
                document.getElementById('portfolioView').style.display = 'block';
                await this.loadPortfolioView();
                break;
            case 'news':
                document.getElementById('newsView').style.display = 'block';
                await this.loadNewsView();
                break;
            case 'analysis':
                document.getElementById('analysisView').style.display = 'block';
                await this.loadAnalysisView();
                break;
        }
    }

    async loadDashboard() {
        try {
            this.showLoading();
            
            const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
            const [watchlistData, marketData] = await Promise.all([
                dataService.getWatchlistData(watchlist).catch(err => {
                    console.warn('Watchlist data failed:', err);
                    return [];
                }),
                dataService.getMarketData().catch(err => {
                    console.warn('Market data failed:', err);
                    return dataService.getDefaultMarketData();
                })
            ]);
            
            if (watchlistData && watchlistData.length > 0) {
                this.updateWatchlist(watchlistData);
            } else {
                // Show empty state for watchlist
                const container = document.getElementById('watchlistContainer');
                if (container) {
                    container.innerHTML = `
                        <div style="padding: var(--space-lg); text-align: center; color: var(--text-muted);">
                            <i class="fas fa-chart-line" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                            <p style="font-weight: 500;">Your watchlist is empty</p>
                            <p style="font-size: 0.85rem; margin-top: 0.5rem;">
                                Click "Edit" to add stocks to your watchlist
                            </p>
                        </div>
                    `;
                }
            }
            this.updateMarketOverview(marketData);
            this.updatePortfolio();
            this.updateNews();
            
        } catch (error) {
            console.error('Dashboard load error:', error);
            // Show error but don't throw - let the app continue
        } finally {
            this.hideLoading();
        }
    }

    async updateNews() {
        const newsContainer = document.getElementById('newsContainer');
        if (!newsContainer) return;
        
        // Show loading state while fetching real news
        newsContainer.innerHTML = `
            <div style="padding: var(--space-md); text-align: center; color: var(--text-muted);">
                <i class="fas fa-spinner fa-spin"></i> Loading news...
            </div>
        `;
        
        try {
            const response = await fetch(`${CONFIG.BACKEND.ANALYTICS_URL}/news/general?limit=5`);
            if (!response.ok) throw new Error('Failed to fetch news');
            
            const data = await response.json();
            const news = data.news || [];
            
            if (news.length === 0) {
                newsContainer.innerHTML = `
                    <div style="padding: var(--space-md); text-align: center; color: var(--text-muted);">
                        <p>No news available</p>
                    </div>
                `;
                return;
            }
            
            newsContainer.innerHTML = news.map(item => `
                <a href="${item.link}" target="_blank" style="display: block; padding: var(--space-md); border-bottom: 1px solid var(--border); text-decoration: none; color: inherit; transition: background 0.2s;" onmouseover="this.style.background='var(--bg-secondary)'" onmouseout="this.style.background='transparent'">
                    <div style="font-weight: 500; margin-bottom: 0.25rem; color: var(--text);">${item.title}</div>
                    <div style="font-size: 0.85rem; color: var(--text-muted);">
                        ${item.publisher} • ${this.formatTime(item.publishedAt)}
                    </div>
                </a>
            `).join('');
            
        } catch (error) {
            console.error('Error loading news:', error);
            newsContainer.innerHTML = `
                <div style="padding: var(--space-md); text-align: center; color: var(--text-muted);">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load news</p>
                </div>
            `;
        }
    }
    
    formatTime(isoString) {
        try {
            const date = new Date(isoString);
            const now = new Date();
            const diffMs = now - date;
            const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
            
            if (diffHours < 1) return 'Just now';
            if (diffHours < 24) return `${diffHours}h ago`;
            const diffDays = Math.floor(diffHours / 24);
            if (diffDays < 7) return `${diffDays}d ago`;
            return date.toLocaleDateString();
        } catch (e) {
            return '';
        }
    }

    switchMarketView(market) {
        // Update active tab
        document.querySelectorAll('.market-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-market="${market}"]`).classList.add('active');
        
        // Hide all market views
        document.querySelectorAll('.market-view').forEach(view => {
            view.style.display = 'none';
        });
        
        // Show selected market view
        const selectedView = document.getElementById(`${market}MarketView`);
        if (selectedView) {
            selectedView.style.display = 'block';
            
            // Load data for the selected market
            if (market === 'us') {
                this.loadUSMarketData();
            } else if (market === 'india') {
                this.loadIndiaMarketData();
            }
        }
    }

    async loadUSMarketData() {
        const usStocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM'];
        const indices = [
            { symbol: 'SPY', elementPrefix: 'spy' },
            { symbol: 'QQQ', elementPrefix: 'qqq' },
            { symbol: 'DIA', elementPrefix: 'dia' },
            { symbol: 'IWM', elementPrefix: 'iwm' }
        ];
        
        try {
            // Update market status
            this.updateMarketStatus('us');
            
            // Load indices
            for (const index of indices) {
                const data = await dataService.getStockDetail(index.symbol);
                const valueEl = document.getElementById(`${index.elementPrefix}Value`);
                const changeEl = document.getElementById(`${index.elementPrefix}Change`);
                
                if (valueEl) valueEl.textContent = `$${data.price.toFixed(2)}`;
                if (changeEl) {
                    const changeClass = data.change >= 0 ? 'positive' : 'negative';
                    const changeSign = data.change >= 0 ? '+' : '';
                    changeEl.textContent = `${changeSign}${data.changePercent.toFixed(2)}%`;
                    changeEl.className = `index-change ${changeClass}`;
                }
            }
            
            // Setup quick action buttons
            this.setupMarketActions('us');
            
            // Load market movers
            await this.loadMarketMovers(usStocks, 'usMoversGrid', 'gainers');
            
            // Load popular stocks
            await this.loadPopularStocks(usStocks, 'usStocksGrid');
        } catch (error) {
            console.error('Error loading US market data:', error);
        }
    }

    async loadIndiaMarketData() {
        const indiaStocks = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS'];
        const indices = [
            { symbol: '^NSEI', elementPrefix: 'nifty50' },
            { symbol: '^NSEBANK', elementPrefix: 'bankNifty' },
            { symbol: '^CNXIT', elementPrefix: 'niftyIt' },
            { symbol: '^CNXAUTO', elementPrefix: 'niftyauto' }
        ];
        
        try {
            // Update market status
            this.updateMarketStatus('india');
            
            // Load indices
            for (const index of indices) {
                try {
                    const data = await dataService.getStockDetail(index.symbol);
                    const valueEl = document.getElementById(`${index.elementPrefix}Value`);
                    const changeEl = document.getElementById(`${index.elementPrefix}Change`);
                    
                    if (valueEl) valueEl.textContent = data.price.toFixed(2);
                    if (changeEl) {
                        const changeClass = data.change >= 0 ? 'positive' : 'negative';
                        const changeSign = data.change >= 0 ? '+' : '';
                        changeEl.textContent = `${changeSign}${data.changePercent.toFixed(2)}%`;
                        changeEl.className = `index-change ${changeClass}`;
                    }
                } catch (err) {
                    console.warn(`Failed to load ${index.symbol}:`, err);
                }
            }
            
            // Setup quick action buttons
            this.setupMarketActions('india');
            
            // Load market movers
            await this.loadMarketMovers(indiaStocks, 'indiaMoversGrid', 'gainers');
            
            // Load popular stocks
            await this.loadPopularStocks(indiaStocks, 'indiaStocksGrid');
        } catch (error) {
            console.error('Error loading India market data:', error);
        }
    }

    async loadPopularStocks(symbols, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);"><i class="fas fa-spinner fa-spin"></i> Loading stocks...</div>';
        
        try {
            const stocksData = await Promise.all(
                symbols.map(symbol => 
                    dataService.getStockDetail(symbol).catch(err => {
                        console.warn(`Failed to load ${symbol}:`, err);
                        return null;
                    })
                )
            );
            
            const validStocks = stocksData.filter(stock => stock !== null);
            
            if (validStocks.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">No data available</div>';
                return;
            }
            
            container.innerHTML = validStocks.map(stock => `
                <div class="stock-card" onclick="uiController.showStockDetail('${stock.symbol}')">
                    <div class="stock-card-header">
                        <div>
                            <div class="stock-symbol">${stock.symbol}</div>
                            <div class="stock-name">${stock.name}</div>
                        </div>
                    </div>
                    <div class="stock-price">$${stock.price.toFixed(2)}</div>
                    <div class="stock-change ${stock.change >= 0 ? 'positive' : 'negative'}">
                        ${stock.change >= 0 ? '+' : ''}${stock.changePercent.toFixed(2)}%
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading popular stocks:', error);
            container.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-secondary);">Failed to load stocks</div>';
        }
    }

    updateWatchlist(stocks) {
        const container = document.getElementById('watchlistContainer');
        
        if (!stocks || stocks.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding: var(--space-lg); text-align: center; color: var(--text-muted);">
                    <i class="fas fa-chart-line" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
                    <p>Loading live stock data via yfinance...</p>
                    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
                        <i class="fas fa-rocket" style="color: #10b981;"></i> 
                        Unlimited data - No rate limits!
                    </p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = stocks.map(stock => `
            <div class="stock-card" data-symbol="${stock.symbol}">
                <div class="stock-info">
                    <span class="stock-symbol">${stock.symbol}</span>
                    <span class="stock-name">${this.formatStockName(stock.symbol)}</span>
                </div>
                <div class="stock-data">
                    <div class="stock-price">${dataService.formatPrice(stock.price, stock.currency || 'USD', stock.symbol)}</div>
                    <div class="stock-change ${stock.change >= 0 ? 'change-positive' : 'change-negative'}">
                        ${dataService.formatPercent(stock.changePercent)}
                    </div>
                </div>
            </div>
        `).join('');
        
        container.querySelectorAll('.stock-card').forEach(card => {
            card.addEventListener('click', () => {
                this.showStockDetail(card.dataset.symbol);
            });
        });
    }

    updateMarketOverview(marketData) {
        const sentimentElement = document.getElementById('marketSentiment');
        if (sentimentElement) {
            if (marketData && marketData.chartData && marketData.chartData.values && marketData.chartData.values.length > 0) {
                // Calculate sentiment from actual SPY data
                const values = marketData.chartData.values;
                const recentChange = ((values[values.length - 1] - values[0]) / values[0]) * 100;
                const sentiment = Math.min(100, Math.max(0, 50 + recentChange * 5));
                
                sentimentElement.innerHTML = `
                    <div class="sentiment-indicator" style="padding: var(--space-md); text-align: center;">
                        <span style="font-size: 0.9rem; color: var(--text-muted);">Market Sentiment: ${sentiment.toFixed(0)}% Bullish</span>
                        <div style="font-size: 0.85rem; margin-top: 0.25rem;">Based on S&P 500 (SPY) trend</div>
                    </div>
                `;
            } else {
                sentimentElement.innerHTML = `
                    <div class="sentiment-indicator" style="padding: var(--space-md); text-align: center; color: var(--text-muted);">
                        <i class="fas fa-chart-area" style="font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.5;"></i>
                        <p style="font-size: 0.9rem;">Loading market data...</p>
                    </div>
                `;
            }
        }
        
        if (marketData && marketData.chartData) {
            chartService.updateMarketChart(marketData.chartData);
        }
    }

    async updatePortfolio() {
        const container = document.getElementById('portfolioSummary');
        if (!container) return;
        
        // For demo purposes, analyze the watchlist as a portfolio
        const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
        if (!watchlist || watchlist.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: var(--space-lg); color: var(--text-muted);">No stocks in watchlist</div>';
            return;
        }
        
        const holdings = watchlist.map(symbol => ({
            symbol: symbol,
            shares: 10,
            purchasePrice: 100 // Default price for demo
        }));
        
        container.innerHTML = `
            <div style="text-align: center; padding: var(--space-md) 0;">
                <i class="fas fa-spinner fa-spin"></i> Loading portfolio...
            </div>
        `;
        
        try {
            const response = await fetch(`${CONFIG.BACKEND.ANALYTICS_URL}/portfolio/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ holdings })
            });
            
            if (!response.ok) throw new Error('Failed to analyze portfolio');
            
            const portfolio = await response.json();
            const totalValue = portfolio.totalValue || 0;
            const totalGain = portfolio.totalGain || 0;
            const totalGainPct = portfolio.totalGainPercent || 0;
            
            container.innerHTML = `
                <div style="padding: var(--space-md) 0;">
                    <div style="margin-bottom: var(--space-md);">
                        <div style="font-size: 1.5rem; font-weight: 600; color: var(--text);">$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                        <div style="font-size: 0.9rem; color: ${totalGain >= 0 ? 'var(--success)' : 'var(--danger)'};">
                            ${totalGain >= 0 ? '+' : ''}$${totalGain.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} 
                            (${totalGain >= 0 ? '+' : ''}${totalGainPct.toFixed(2)}%)
                        </div>
                    </div>
                    
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem;">${portfolio.positions?.length || 0} Holdings</div>
                </div>
            `;
            
            // Update dashboard portfolio chart
            this.updateDashboardPortfolioChart(portfolio.positions || []);
            
        } catch (error) {
            console.error('Error loading portfolio:', error);
            container.innerHTML = `
                <div style="text-align: center; padding: var(--space-md) 0; color: var(--text-muted);">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Failed to load portfolio</p>
                </div>
            `;
        }
    }

    async showStockDetail(symbol) {
        try {
            this.showLoading();
            this.currentStock = symbol;
            
            const stockDetail = await dataService.getStockDetail(symbol);
            this.updateStockDetailView(stockDetail);
            this.switchView('markets');
            
            if (CONFIG.FEATURES.ENABLE_AI_INSIGHTS) {
                await this.loadAIAnalysis(symbol);
            }
            
        } catch (error) {
            this.showError('Failed to load stock details: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    updateStockDetailView(stockDetail) {
        const { quote } = stockDetail;
        const currency = quote.currency || 'USD';
        const symbol = quote.symbol;
        
        document.getElementById('detailStockSymbol').textContent = symbol;
        document.getElementById('detailStockName').textContent = this.formatStockName(symbol);
        document.getElementById('detailStockPrice').textContent = dataService.formatPrice(quote.price, currency, symbol);
        
        const changeElement = document.getElementById('detailStockChange');
        changeElement.textContent = 
            `${quote.change >= 0 ? '+' : ''}${dataService.formatPrice(quote.change, currency, symbol)} ` +
            `(${dataService.formatPercent(quote.changePercent)})`;
        changeElement.className = `stock-detail-change ${quote.change >= 0 ? 'change-positive' : 'change-negative'}`;
        
        document.getElementById('statOpen').textContent = dataService.formatPrice(quote.open, currency, symbol);
        document.getElementById('statHigh').textContent = dataService.formatPrice(quote.high, currency, symbol);
        document.getElementById('statLow').textContent = dataService.formatPrice(quote.low, currency, symbol);
        document.getElementById('statVolume').textContent = quote.volume.toLocaleString();
        
        chartService.updateStockDetailChart(stockDetail.timeSeries);
    }

    async loadAIAnalysis(symbol) {
        try {
            const analysis = await dataService.getAIAnalysis(symbol, 'technical');
            this.displayAIAnalysis(analysis);
        } catch (error) {
            console.error('AI analysis failed:', error);
        }
    }

    displayAIAnalysis(analysis) {
        const content = document.getElementById('aiAnalysisContent');
        
        content.innerHTML = `
            <div class="analysis-result">
                <h3>Technical Analysis</h3>
                <div class="analysis-metrics">
                    <div class="analysis-metric">
                        <span class="metric-label">RSI</span>
                        <span class="metric-value ${analysis.rsi > 70 ? 'sentiment-negative' : analysis.rsi < 30 ? 'sentiment-positive' : ''}">
                            ${analysis.rsi}
                        </span>
                    </div>
                    <div class="analysis-metric">
                        <span class="metric-label">Trend</span>
                        <span class="metric-value sentiment-${analysis.trend}">
                            ${analysis.trend.toUpperCase()}
                        </span>
                    </div>
                    <div class="analysis-metric">
                        <span class="metric-label">Recommendation</span>
                        <span class="metric-value ${analysis.recommendation === 'BUY' ? 'sentiment-positive' : analysis.recommendation === 'SELL' ? 'sentiment-negative' : ''}">
                            ${analysis.recommendation}
                        </span>
                    </div>
                </div>
                <div class="analysis-summary">
                    <p><strong>Confidence:</strong> ${analysis.confidence}%</p>
                    <p><strong>Support:</strong> ${dataService.formatPrice(analysis.support, this.currentStock?.currency || 'USD', this.currentStock?.symbol || '')}</p>
                    <p><strong>Resistance:</strong> ${dataService.formatPrice(analysis.resistance, this.currentStock?.currency || 'USD', this.currentStock?.symbol || '')}</p>
                </div>
            </div>
        `;
    }

    async handleSearch(event) {
        const query = event.target.value.trim();
        const resultsContainer = document.getElementById('searchResults');
        const marketSelector = document.getElementById('marketSelector');
        const selectedMarket = marketSelector ? marketSelector.value : 'all';
        
        // Input validation
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        // Limit query length
        if (query.length > 50) {
            resultsContainer.innerHTML = '<div class="search-result-item">Query too long</div>';
            resultsContainer.style.display = 'block';
            return;
        }
        
        // Sanitize input - allow .NS/.BO for Indian stocks
        const sanitizedQuery = query.replace(/[^a-zA-Z0-9\s.-]/g, '');
        
        try {
            let results = await yfinanceService.searchStocks(sanitizedQuery);
            
            // Filter by selected market
            if (selectedMarket !== 'all') {
                results = results.filter(stock => {
                    if (selectedMarket === 'india') {
                        return stock.symbol.includes('.NS') || stock.symbol.includes('.BO');
                    } else if (selectedMarket === 'us') {
                        return !stock.symbol.includes('.NS') && !stock.symbol.includes('.BO');
                    }
                    return true;
                });
            }
            
            this.displaySearchResults(results);
        } catch (error) {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="search-result-item">Search failed</div>';
            resultsContainer.style.display = 'block';
        }
    }

    displaySearchResults(results) {
        const container = document.getElementById('searchResults');
        
        if (!results || results.length === 0) {
            container.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            // Sanitize results to prevent XSS
            container.innerHTML = results.map(stock => {
                // For Indian stocks, use nse_symbol with .NS suffix, otherwise use regular symbol
                const actualSymbol = stock.nse_symbol || stock.symbol || '';
                const displaySymbol = stock.symbol || '';
                const safeActualSymbol = this.sanitizeHTML(actualSymbol);
                const safeDisplaySymbol = this.sanitizeHTML(displaySymbol);
                const safeName = this.sanitizeHTML(stock.name || stock.company_name || '');
                const safeMarket = stock.market ? this.sanitizeHTML(stock.market) : '';
                return `
                    <div class="search-result-item" data-symbol="${safeActualSymbol}">
                        <div>
                            <strong>${safeDisplaySymbol}</strong> - ${safeName}
                        </div>
                        ${safeMarket ? `<span class="market-badge">${safeMarket}</span>` : ''}
                    </div>
                `;
            }).join('');
            
            container.querySelectorAll('.search-result-item').forEach(item => {
                item.addEventListener('click', () => {
                    const symbol = item.dataset.symbol;
                    
                    // Validate symbol (allow dots for Indian stocks, increased length for .NS/.BO suffix)
                    if (!symbol || !/^[A-Z0-9.\-^]{1,20}$/.test(symbol)) {
                        console.error('Invalid symbol:', symbol);
                        return;
                    }
                    
                    document.getElementById('stockSearch').value = '';
                    container.style.display = 'none';
                    this.showStockDetail(symbol);
                });
            });
        }
        
        container.style.display = 'block';
    }

    async runAdvancedAnalysis() {
        const analysisType = document.getElementById('analysisType').value;
        const resultsContainer = document.getElementById('analysisResults');
        
        // Use current stock or default to AAPL
        const symbol = this.currentStock || 'AAPL';
        
        try {
            resultsContainer.innerHTML = `
                <div class="loading-analysis">
                    <div class="spinner"></div>
                    <p>Running ${analysisType} analysis for ${symbol}...</p>
                </div>
            `;

            const analysis = await dataService.getAIAnalysis(symbol, analysisType);
            this.displayAdvancedAnalysis(analysisType, analysis);
            
        } catch (error) {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    Analysis failed: ${error.message}
                </div>
            `;
        }
    }

    displayAdvancedAnalysis(analysisType, analysis) {
        const resultsContainer = document.getElementById('analysisResults');
        
        let html = `<div class="analysis-result">
            <h3>${analysisType.charAt(0).toUpperCase() + analysisType.slice(1)} Analysis for ${analysis.symbol}</h3>`;
        
        if (analysisType === 'technical') {
            html += this.renderTechnicalAnalysis(analysis);
        } else if (analysisType === 'risk') {
            html += this.renderRiskAnalysis(analysis);
        }
        
        html += `</div>`;
        resultsContainer.innerHTML = html;
    }

    renderTechnicalAnalysis(analysis) {
        return `
            <div class="analysis-metrics">
                <div class="analysis-metric">
                    <span class="metric-label">RSI</span>
                    <span class="metric-value">${analysis.rsi}</span>
                </div>
                <div class="analysis-metric">
                    <span class="metric-label">MACD</span>
                    <span class="metric-value">${analysis.macd}</span>
                </div>
                <div class="analysis-metric">
                    <span class="metric-label">Recommendation</span>
                    <span class="metric-value ${analysis.recommendation === 'BUY' ? 'sentiment-positive' : 'sentiment-negative'}">
                        ${analysis.recommendation}
                    </span>
                </div>
            </div>
            <div class="analysis-summary">
                <p><strong>Confidence:</strong> ${analysis.confidence}%</p>
                <p><strong>Trend:</strong> ${analysis.trend}</p>
            </div>
        `;
    }

    renderRiskAnalysis(analysis) {
        return `
            <div class="analysis-metrics">
                <div class="analysis-metric">
                    <span class="metric-label">Volatility</span>
                    <span class="metric-value">${analysis.volatility}%</span>
                </div>
                <div class="analysis-metric">
                    <span class="metric-label">Beta</span>
                    <span class="metric-value">${analysis.beta}</span>
                </div>
                <div class="analysis-metric">
                    <span class="metric-label">Sharpe Ratio</span>
                    <span class="metric-value">${analysis.sharpe}</span>
                </div>
            </div>
        `;
    }

    formatStockName(symbol) {
        const nameMap = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'SPY': 'SPDR S&P 500 ETF'
        };
        return nameMap[symbol] || symbol;
    }

    showLoading() {
        document.body.classList.add('loading');
    }

    hideLoading() {
        document.body.classList.remove('loading');
    }

    showError(message) {
        alert(message); // In real app, use a proper notification system
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Watchlist Editor Methods
    editWatchlist() {
        console.log('Edit watchlist clicked');
        const modal = document.getElementById('watchlistModal');
        if (!modal) {
            console.error('Watchlist modal not found!');
            this.showMessage('Error: Modal not found', 'error');
            return;
        }
        console.log('Modal found, opening...');
        modal.style.display = 'flex';
        console.log('Modal display set to flex');
        this.populateWatchlistEditor();
        console.log('Watchlist editor populated');
        
        // Setup event listeners for the modal
        const closeBtn = document.getElementById('closeWatchlistModal');
        const doneBtn = document.getElementById('closeWatchlistEditor');
        const addBtn = document.getElementById('addWatchlistSymbol');
        const resetBtn = document.getElementById('resetWatchlist');
        const input = document.getElementById('newWatchlistSymbol');
        
        if (closeBtn) closeBtn.onclick = () => this.closeWatchlistEditor();
        if (doneBtn) doneBtn.onclick = () => this.closeWatchlistEditor();
        if (addBtn) addBtn.onclick = () => this.addToWatchlistEditor();
        if (resetBtn) resetBtn.onclick = () => this.resetWatchlistToDefault();
        
        // Add on Enter key press
        if (input) {
            input.onkeypress = (e) => {
                if (e.key === 'Enter') {
                    this.addToWatchlistEditor();
                }
            };
        }
        
        // Close on outside click
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.closeWatchlistEditor();
            }
        };
    }
    
    populateWatchlistEditor() {
        const container = document.getElementById('watchlistEditorItems');
        const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
        
        if (watchlist.length === 0) {
            container.innerHTML = '<div class="watchlist-empty">Your watchlist is empty. Add some stocks!</div>';
            return;
        }
        
        container.innerHTML = watchlist.map(symbol => `
            <div class="watchlist-item" data-symbol="${symbol}">
                <div class="watchlist-item-info">
                    <div class="watchlist-item-symbol">${symbol}</div>
                    <div class="watchlist-item-name">Loading...</div>
                </div>
                <div class="watchlist-item-actions">
                    <button class="watchlist-item-remove" onclick="uiController.removeFromWatchlistEditor('${symbol}')">
                        Remove
                    </button>
                </div>
            </div>
        `).join('');
        
        // Fetch stock names asynchronously
        watchlist.forEach(symbol => this.fetchStockNameForEditor(symbol));
    }
    
    async fetchStockNameForEditor(symbol) {
        try {
            const quote = await yfinanceService.getQuote(symbol);
            const nameElement = document.querySelector(`.watchlist-item[data-symbol="${symbol}"] .watchlist-item-name`);
            if (nameElement) {
                nameElement.textContent = quote.name || symbol;
            }
        } catch (error) {
            const nameElement = document.querySelector(`.watchlist-item[data-symbol="${symbol}"] .watchlist-item-name`);
            if (nameElement) {
                nameElement.textContent = symbol;
            }
        }
    }
    
    addToWatchlistEditor() {
        const input = document.getElementById('newWatchlistSymbol');
        const symbol = input.value.trim().toUpperCase();
        
        if (!symbol) {
            this.showMessage('Please enter a stock symbol', 'error');
            return;
        }
        
        // Basic validation
        if (!/^[A-Z0-9.\-^]{1,20}$/.test(symbol)) {
            this.showMessage('Invalid symbol format', 'error');
            return;
        }
        
        const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
        
        if (watchlist.includes(symbol)) {
            this.showMessage(`${symbol} is already in your watchlist`, 'error');
            return;
        }
        
        watchlist.push(symbol);
        localStorage.setItem('watchlist', JSON.stringify(watchlist));
        
        input.value = '';
        this.populateWatchlistEditor();
        this.showMessage(`${symbol} added to watchlist`, 'success');
        
        // Refresh the main watchlist display
        this.loadWatchlist();
    }
    
    removeFromWatchlistEditor(symbol) {
        const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
        const index = watchlist.indexOf(symbol);
        
        if (index > -1) {
            watchlist.splice(index, 1);
            localStorage.setItem('watchlist', JSON.stringify(watchlist));
            this.populateWatchlistEditor();
            this.showMessage(`${symbol} removed from watchlist`, 'success');
            
            // Refresh the main watchlist display
            this.loadWatchlist();
        }
    }
    
    resetWatchlistToDefault() {
        if (confirm('Are you sure you want to reset your watchlist to default stocks?')) {
            localStorage.setItem('watchlist', JSON.stringify(CONFIG.APP.DEFAULT_WATCHLIST));
            this.populateWatchlistEditor();
            this.showMessage('Watchlist reset to default', 'success');
            
            // Refresh the main watchlist display
            this.loadWatchlist();
        }
    }
    
    closeWatchlistEditor() {
        const modal = document.getElementById('watchlistModal');
        modal.style.display = 'none';
        document.getElementById('newWatchlistSymbol').value = '';
    }

    addToWatchlist() {
        if (!this.currentStock) return;
        
        const watchlist = JSON.parse(localStorage.getItem('watchlist')) || CONFIG.APP.DEFAULT_WATCHLIST;
        if (!watchlist.includes(this.currentStock)) {
            watchlist.push(this.currentStock);
            localStorage.setItem('watchlist', JSON.stringify(watchlist));
            this.showMessage(`${this.currentStock} added to watchlist`);
        }
    }

    viewAdvancedAnalysis() {
        this.switchView('analysis');
    }

    async changeTimeframe() {
        if (!this.currentStock) return;
        
        const timeframe = document.getElementById('timeframeSelect').value;
        try {
            const timeSeries = await yfinanceService.getTimeSeries(this.currentStock, timeframe);
            chartService.updateStockDetailChart(timeSeries);
        } catch (error) {
            this.showError('Failed to update chart: ' + error.message);
        }
    }

    showMessage(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        // Add to body
        document.body.appendChild(toast);
        
        // Show with animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Portfolio View Functions
    async loadPortfolioView() {
        const holdings = this.getPortfolioHoldings();
        
        if (holdings.length === 0) {
            document.getElementById('holdingsTableBody').innerHTML = `
                <tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-muted);">
                    No holdings yet. Click "Add Holding" to get started.
                </td></tr>
            `;
            this.updatePortfolioStats(null);
            return;
        }
        
        try {
            const response = await fetch(`${CONFIG.BACKEND.ANALYTICS_URL}/portfolio/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ holdings })
            });
            
            if (!response.ok) throw new Error('Failed to analyze portfolio');
            
            const portfolio = await response.json();
            this.updatePortfolioStats(portfolio);
            this.updateHoldingsTable(portfolio.positions || []);
            this.updatePortfolioChart(portfolio.positions || []);
        } catch (error) {
            console.error('Error loading portfolio:', error);
            this.showError('Failed to load portfolio data');
        }
    }
    
    updatePortfolioStats(portfolio) {
        if (!portfolio) {
            document.getElementById('portfolioTotalValue').textContent = '$0.00';
            document.getElementById('portfolioTotalGain').textContent = '$0.00';
            document.getElementById('portfolioTotalGainPct').textContent = '0.00%';
            document.getElementById('portfolioHoldingsCount').textContent = '0';
            return;
        }
        
        const totalValue = portfolio.totalValue || 0;
        const totalGain = portfolio.totalGain || 0;
        const totalGainPct = portfolio.totalGainPercent || 0;
        const count = portfolio.positions?.length || 0;
        
        document.getElementById('portfolioTotalValue').textContent = 
            `$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById('portfolioTotalGain').textContent = 
            `${totalGain >= 0 ? '+' : ''}$${totalGain.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById('portfolioTotalGain').style.color = 
            totalGain >= 0 ? 'var(--success)' : 'var(--danger)';
        document.getElementById('portfolioTotalGainPct').textContent = 
            `${totalGain >= 0 ? '+' : ''}${totalGainPct.toFixed(2)}%`;
        document.getElementById('portfolioTotalGainPct').style.color = 
            totalGain >= 0 ? 'var(--success)' : 'var(--danger)';
        document.getElementById('portfolioHoldingsCount').textContent = count;
    }
    
    updateHoldingsTable(positions) {
        const tbody = document.getElementById('holdingsTableBody');
        tbody.innerHTML = positions.map(pos => `
            <tr>
                <td><strong>${this.sanitizeHTML(pos.symbol)}</strong></td>
                <td>${pos.shares}</td>
                <td>$${pos.purchasePrice.toFixed(2)}</td>
                <td>$${pos.currentPrice.toFixed(2)}</td>
                <td>$${pos.currentValue.toFixed(2)}</td>
                <td style="color: ${pos.gain >= 0 ? 'var(--success)' : 'var(--danger)'}">
                    ${pos.gain >= 0 ? '+' : ''}$${pos.gain.toFixed(2)} (${pos.gainPercent.toFixed(2)}%)
                </td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="window.stockSenseApp.editHolding('${pos.symbol}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline" onclick="window.stockSenseApp.deleteHolding('${pos.symbol}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    updatePortfolioChart(positions) {
        const canvas = document.getElementById('portfolioAllocationChart');
        if (!canvas) return;
        
        if (this.portfolioChart) {
            this.portfolioChart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        this.portfolioChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: positions.map(p => p.symbol),
                datasets: [{
                    data: positions.map(p => p.currentValue),
                    backgroundColor: [
                        '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
                        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toFixed(2)} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    getPortfolioHoldings() {
        return JSON.parse(localStorage.getItem('portfolio_holdings') || '[]');
    }
    
    savePortfolioHoldings(holdings) {
        localStorage.setItem('portfolio_holdings', JSON.stringify(holdings));
    }
    
    addHolding() {
        document.getElementById('modalTitle').textContent = 'Add Holding';
        document.getElementById('holdingSymbol').value = '';
        document.getElementById('holdingShares').value = '';
        document.getElementById('holdingCost').value = '';
        document.getElementById('holdingModal').style.display = 'flex';
    }
    
    editHolding(symbol) {
        const holdings = this.getPortfolioHoldings();
        const holding = holdings.find(h => h.symbol === symbol);
        if (!holding) return;
        
        document.getElementById('modalTitle').textContent = 'Edit Holding';
        document.getElementById('holdingSymbol').value = holding.symbol;
        document.getElementById('holdingSymbol').disabled = true;
        document.getElementById('holdingShares').value = holding.shares;
        document.getElementById('holdingCost').value = holding.purchasePrice;
        document.getElementById('holdingModal').style.display = 'flex';
    }
    
    saveHolding() {
        const symbol = document.getElementById('holdingSymbol').value.trim().toUpperCase();
        const shares = parseFloat(document.getElementById('holdingShares').value);
        const cost = parseFloat(document.getElementById('holdingCost').value);
        
        if (!symbol || !this.validateSymbol(symbol)) {
            alert('Please enter a valid stock symbol');
            return;
        }
        
        if (isNaN(shares) || shares <= 0) {
            alert('Please enter a valid number of shares');
            return;
        }
        
        if (isNaN(cost) || cost <= 0) {
            alert('Please enter a valid purchase price');
            return;
        }
        
        const holdings = this.getPortfolioHoldings();
        const existingIndex = holdings.findIndex(h => h.symbol === symbol);
        
        if (existingIndex >= 0) {
            holdings[existingIndex] = { symbol, shares, purchasePrice: cost };
        } else {
            holdings.push({ symbol, shares, purchasePrice: cost });
        }
        
        this.savePortfolioHoldings(holdings);
        this.closeModal();
        this.loadPortfolioView();
    }
    
    deleteHolding(symbol) {
        if (!confirm(`Delete ${symbol} from portfolio?`)) return;
        
        const holdings = this.getPortfolioHoldings();
        const filtered = holdings.filter(h => h.symbol !== symbol);
        this.savePortfolioHoldings(filtered);
        this.loadPortfolioView();
    }
    
    closeModal() {
        document.getElementById('holdingModal').style.display = 'none';
        document.getElementById('holdingSymbol').disabled = false;
    }
    
    // News View Functions
    async loadNewsView(append = false) {
        const activeTab = document.querySelector('.news-filter-tab.active');
        const filter = activeTab?.dataset.filter || 'general';
        const region = activeTab?.dataset.region || 'us';
        const container = document.getElementById('newsViewContainer');
        const loadMoreContainer = document.querySelector('.news-load-more');
        
        if (!container) return;
        
        // Show loading skeletons
        if (!append) {
            container.innerHTML = this.getNewsSkeletons(6);
        }
        
        try {
            // Build endpoint based on filter and region
            const endpoint = `${CONFIG.BACKEND.ANALYTICS_URL}/news/general?limit=20&region=${region}`;
                
            const response = await fetch(endpoint);
            if (!response.ok) throw new Error('Failed to fetch news');
            
            const data = await response.json();
            const news = data.news || [];
            
            // Store current news for search filtering
            this.currentNews = news;
            
            if (news.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-newspaper"></i>
                        <p>No news available at the moment</p>
                    </div>
                `;
                if (loadMoreContainer) loadMoreContainer.style.display = 'none';
                return;
            }
            
            const newsHTML = news.map((item, index) => `
                <div class="news-card" style="animation-delay: ${index * 0.1}s" data-title="${this.sanitizeHTML(item.title).toLowerCase()}">
                    ${item.thumbnail ? `<img src="${item.thumbnail}" alt="${this.sanitizeHTML(item.title)}" class="news-thumbnail" onerror="this.style.display='none'">` : ''}
                    <div class="news-content">
                        <h3 class="news-title">
                            <a href="${item.link}" target="_blank" rel="noopener noreferrer">
                                ${this.sanitizeHTML(item.title)}
                            </a>
                        </h3>
                        <div class="news-meta">
                            <span class="news-publisher">
                                <i class="fas fa-building"></i>
                                ${this.sanitizeHTML(item.publisher)}
                            </span>
                            <span class="news-time">
                                <i class="far fa-clock"></i>
                                ${this.formatTime(item.publishedAt)}
                            </span>
                        </div>
                        ${item.relatedTickers && item.relatedTickers.length > 0 ? `
                            <div class="news-tickers">
                                ${item.relatedTickers.slice(0, 3).map(ticker => `
                                    <span class="news-ticker-tag">${ticker}</span>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');
            
            if (append) {
                container.innerHTML += newsHTML;
            } else {
                container.innerHTML = newsHTML;
            }
            
            // Show/hide load more button (for now, hide it as we're loading all at once)
            if (loadMoreContainer) loadMoreContainer.style.display = 'none';
            
        } catch (error) {
            console.error('Error loading news:', error);
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Failed to load news. Please try again later.</p>
                </div>
            `;
        }
    }
    
    getNewsSkeletons(count = 6) {
        return Array(count).fill('').map(() => `
            <div class="news-card">
                <div class="skeleton" style="height: 200px;"></div>
                <div class="news-content">
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text" style="width: 70%;"></div>
                </div>
            </div>
        `).join('');
    }
    
    async loadMoreNews() {
        // Placeholder for load more functionality
        // In a real implementation, you would fetch the next page of news
        console.log('Load more news clicked');
    }
    
    // Analysis View Functions
    async loadAnalysisView() {
        // Placeholder for analysis view initialization
        console.log('Analysis view loaded');
    }
    
    updateDashboardPortfolioChart(positions) {
        const canvas = document.getElementById('portfolioChart');
        if (!canvas || !positions || positions.length === 0) return;
        
        // Destroy existing chart instance
        if (this.dashboardPortfolioChart) {
            this.dashboardPortfolioChart.destroy();
            this.dashboardPortfolioChart = null;
        }
        
        // Also check if there's any chart attached to the canvas
        const existingChart = Chart.getChart(canvas);
        if (existingChart) {
            existingChart.destroy();
        }
        
        const ctx = canvas.getContext('2d');
        this.dashboardPortfolioChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: positions.map(p => p.symbol),
                datasets: [{
                    data: positions.map(p => p.currentValue),
                    backgroundColor: [
                        '#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
                        '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#84cc16'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 10,
                            font: { size: 11 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((value / total) * 100).toFixed(1);
                                return `${label}: $${value.toFixed(2)} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Market status and actions methods
    updateMarketStatus(market) {
        const now = new Date();
        const day = now.getDay();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const totalMinutes = hours * 60 + minutes;
        
        let isOpen = false;
        let statusText = 'Closed';
        
        if (market === 'us') {
            // US market: Mon-Fri, 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
            if (day >= 1 && day <= 5) {
                // Convert to ET (simplified, not accounting for DST)
                const etHours = hours - 5; // Rough conversion
                const etMinutes = etHours * 60 + minutes;
                if (etMinutes >= 570 && etMinutes < 960) { // 9:30 AM - 4:00 PM
                    isOpen = true;
                    statusText = 'Open';
                }
            }
        } else if (market === 'india') {
            // India market: Mon-Fri, 9:15 AM - 3:30 PM IST
            if (day >= 1 && day <= 5) {
                const istMinutes = totalMinutes + (5.5 * 60); // Convert to IST
                const normalizedMinutes = istMinutes % (24 * 60);
                if (normalizedMinutes >= 555 && normalizedMinutes < 930) { // 9:15 AM - 3:30 PM
                    isOpen = true;
                    statusText = 'Open';
                }
            }
        }
        
        const statusElements = document.querySelectorAll(`.market-status[data-market="${market}"]`);
        statusElements.forEach(el => {
            const indicator = el.querySelector('.status-indicator');
            const text = el.querySelector('.status-text');
            if (indicator) {
                indicator.className = `status-indicator ${isOpen ? 'open' : 'closed'}`;
            }
            if (text) {
                text.textContent = statusText;
            }
        });
    }

    setupMarketActions(market) {
        const container = document.querySelector(`.markets-tab-content[data-market="${market}"]`);
        if (!container) return;
        
        // Top Movers button
        const moversBtn = container.querySelector('[data-action="movers"]');
        if (moversBtn) {
            moversBtn.onclick = () => this.showTopMovers(market);
        }
        
        // Sectors button
        const sectorsBtn = container.querySelector('[data-action="sectors"]');
        if (sectorsBtn) {
            sectorsBtn.onclick = () => this.showSectors(market);
        }
        
        // Heat Map button
        const heatMapBtn = container.querySelector('[data-action="heatmap"]');
        if (heatMapBtn) {
            heatMapBtn.onclick = () => this.showHeatMap(market);
        }
        
        // Compare button
        const compareBtn = container.querySelector('[data-action="compare"]');
        if (compareBtn) {
            compareBtn.onclick = () => this.showCompare(market);
        }
        
        // Setup mover tabs
        const tabs = container.querySelectorAll('.mover-tab');
        tabs.forEach(tab => {
            tab.onclick = () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const type = tab.dataset.type;
                const gridId = market === 'us' ? 'usMoversGrid' : 'indiaMoversGrid';
                const stocks = this.getTopStocksForMarket(market);
                this.loadMarketMovers(stocks, gridId, type);
            };
        });
    }

    getTopStocksForMarket(market) {
        if (market === 'us') {
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM',
                'V', 'WMT', 'JNJ', 'PG', 'MA', 'HD', 'DIS', 'PYPL',
                'NFLX', 'ADBE', 'CRM', 'CSCO', 'PFE', 'KO', 'PEP', 'TMO'
            ];
        } else {
            return [
                'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
                'HINDUNILVR.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'KOTAKBANK.NS',
                'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
                'TITAN.NS', 'ULTRACEMCO.NS', 'BAJFINANCE.NS', 'NESTLEIND.NS', 'WIPRO.NS'
            ];
        }
    }

    async loadMarketMovers(stocks, gridId, type) {
        const grid = document.getElementById(gridId);
        if (!grid) return;
        
        grid.innerHTML = '<div class="loading">Loading market movers...</div>';
        
        try {
            const promises = stocks.map(symbol => dataService.getStockDetail(symbol));
            const results = await Promise.all(promises);
            
            // Filter out errors and sort based on type
            const validStocks = results.filter(r => r && r.price);
            
            let sorted = [];
            if (type === 'gainers') {
                sorted = validStocks
                    .filter(s => s.changePercent > 0)
                    .sort((a, b) => b.changePercent - a.changePercent)
                    .slice(0, 8);
            } else if (type === 'losers') {
                sorted = validStocks
                    .filter(s => s.changePercent < 0)
                    .sort((a, b) => a.changePercent - b.changePercent)
                    .slice(0, 8);
            } else if (type === 'active') {
                // For active, we'll just show highest volume (or use all if volume not available)
                sorted = validStocks
                    .sort((a, b) => (b.volume || 0) - (a.volume || 0))
                    .slice(0, 8);
            }
            
            if (sorted.length === 0) {
                grid.innerHTML = '<div class="no-data">No data available</div>';
                return;
            }
            
            grid.innerHTML = sorted.map(stock => {
                const changeClass = stock.change >= 0 ? 'positive' : 'negative';
                const changeSign = stock.change >= 0 ? '+' : '';
                const currency = stock.symbol.includes('.NS') || stock.symbol.includes('.BO') ? '₹' : '$';
                
                return `
                    <div class="mover-card" onclick="window.uiController.searchStock('${stock.symbol}')">
                        <div class="mover-symbol">${stock.symbol}</div>
                        <div class="mover-name">${stock.name || stock.symbol}</div>
                        <div class="mover-price">${currency}${stock.price.toFixed(2)}</div>
                        <div class="mover-change ${changeClass}">
                            ${changeSign}${stock.changePercent.toFixed(2)}%
                        </div>
                    </div>
                `;
            }).join('');
        } catch (error) {
            console.error('Error loading market movers:', error);
            grid.innerHTML = '<div class="error">Error loading market movers</div>';
        }
    }

    showTopMovers(market) {
        this.showMessage(`Top movers for ${market === 'us' ? 'US' : 'India'} market`, 'info');
        // Scroll to movers section
        const container = document.querySelector(`.markets-tab-content[data-market="${market}"]`);
        const moversSection = container?.querySelector('.market-movers-section');
        if (moversSection) {
            moversSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    showSectors(market) {
        this.showMessage(`Sector analysis coming soon for ${market === 'us' ? 'US' : 'India'} market`, 'info');
        // TODO: Implement sector analysis modal or section
    }

    showHeatMap(market) {
        this.showMessage(`Market heat map coming soon for ${market === 'us' ? 'US' : 'India'} market`, 'info');
        // TODO: Implement heat map visualization
    }

    showCompare(market) {
        this.showMessage(`Stock comparison tool coming soon for ${market === 'us' ? 'US' : 'India'} market`, 'info');
        // TODO: Implement stock comparison tool
    }

    // AI Prediction Methods
    async runLSTMPrediction() {
        console.log('runLSTMPrediction called!');
        const symbol = document.getElementById('lstmSymbol')?.value?.trim();
        const period = document.getElementById('lstmPeriod')?.value || '2y';
        const simulations = parseInt(document.getElementById('lstmSimulations')?.value) || 5;
        const futureDays = parseInt(document.getElementById('lstmFutureDays')?.value) || 30;
        
        console.log('LSTM Parameters:', { symbol, period, simulations, futureDays });
        
        if (!symbol) {
            this.showMessage('Please enter a stock symbol', 'error');
            return;
        }
        
        const resultsDiv = document.getElementById('lstmResults');
        const loadingDiv = document.getElementById('lstmLoading');
        const runButton = document.getElementById('runLSTMPrediction');
        
        if (runButton) runButton.disabled = true;
        if (resultsDiv) resultsDiv.style.display = 'none';
        if (loadingDiv) loadingDiv.style.display = 'block';
        
        const startTime = performance.now();
        
        try {
            // Try pre-trained model first
            let url = `${CONFIG.BACKEND.ANALYTICS_URL}/ai/predict/lstm-pretrained?symbol=${encodeURIComponent(symbol)}&future_days=${futureDays}`;
            console.log('Fetching (pre-trained):', url);
            
            let response = await fetch(url);
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Prediction failed');
            }
            
            const data = await response.json();
            console.log('Prediction data received:', data);
            
            const endTime = performance.now();
            const processingTime = ((endTime - startTime) / 1000).toFixed(2) + 's';
            data.processing_time = processingTime;
            data.future_days = futureDays;
            
            if (data.success) {
                if (loadingDiv) loadingDiv.style.display = 'none';
                this.displayLSTMResults(data);
                this.showMessage('LSTM prediction completed successfully!', 'success');
            } else {
                throw new Error(data.error || 'Prediction failed');
            }
        } catch (error) {
            console.error('LSTM prediction error:', error);
            if (loadingDiv) loadingDiv.style.display = 'none';
            if (resultsDiv) {
                resultsDiv.style.display = 'block';
                resultsDiv.innerHTML = `
                    <div class="error-state" style="text-align: center; padding: 2rem;">
                        <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: var(--accent-red); margin-bottom: 1rem;"></i>
                        <h3 style="color: var(--text-primary); margin-bottom: 0.5rem;">Prediction Failed</h3>
                        <p style="color: var(--text-secondary);">${error.message}</p>
                    </div>
                `;
            }
            this.showMessage(error.message, 'error');
        } finally {
            if (runButton) runButton.disabled = false;
        }
    }
    
    displayLSTMResults(data) {
        const resultsDiv = document.getElementById('lstmResults');
        if (!resultsDiv) {
            console.error('Results div not found!');
            return;
        }
        
        // Show results div with fade-in
        resultsDiv.style.display = 'block';
        resultsDiv.classList.add('fade-in');
        
        // Extract data
        const symbol = data.symbol || 'N/A';
        const currentPrice = data.current_price || 0;
        const predictedPrice = data.predicted_price || data.predictions?.[data.predictions.length - 1] || 0;
        const priceChange = data.price_change_percent || 0;
        const futureDays = data.future_days || (data.predictions?.length || 30);
        const modelMetadata = data.model_metadata || {};
        const usingPretrained = data.using_pretrained || false;
        
        // Calculate processing time
        const processingTime = data.processing_time || '2.5s';
        
        // Wait for DOM to be ready before updating elements
        setTimeout(() => {
            this.updateLSTMResultsDOM(data, {
                symbol,
                currentPrice,
                predictedPrice,
                priceChange,
                futureDays,
                modelMetadata,
                usingPretrained,
                processingTime
            });
        }, 100);
    }
    
    updateLSTMResultsDOM(data, parsed) {
        const { symbol, currentPrice, predictedPrice, priceChange, futureDays, modelMetadata, usingPretrained, processingTime } = parsed;
        // Determine change direction
        const isPositive = priceChange >= 0;
        const changeClass = isPositive ? 'positive' : 'negative';
        const changeIcon = isPositive ? 'fa-arrow-up' : 'fa-arrow-down';
        const changeText = isPositive ? 'Expected to increase' : 'Expected to decrease';
        
        // Animate counter for prices
        const animateValue = (element, start, end, duration) => {
            if (!element) return;
            const startTime = performance.now();
            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                const value = start + (end - start) * progress;
                element.textContent = value.toFixed(2);
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };
            requestAnimationFrame(animate);
        };
        
        // Update current price with animation
        setTimeout(() => {
            const currentPriceEl = document.getElementById('lstmCurrentPrice');
            animateValue(currentPriceEl, 0, currentPrice, 800);
        }, 200);
        
        // Update predicted price with animation
        setTimeout(() => {
            const predictedPriceEl = document.getElementById('lstmPredictedPrice');
            animateValue(predictedPriceEl, 0, predictedPrice, 1000);
        }, 500);
        
        // Update other fields with null checks
        const lstmDaysLabel = document.getElementById('lstmDaysLabel');
        const lstmPriceChange = document.getElementById('lstmPriceChange');
        const lstmChangeText = document.getElementById('lstmChangeText');
        const lstmHorizon = document.getElementById('lstmHorizon');
        const lstmModelType = document.getElementById('lstmModelType');
        const lstmProcessTime = document.getElementById('lstmProcessTime');
        const lstmConfidence = document.getElementById('lstmConfidence');
        
        if (lstmDaysLabel) lstmDaysLabel.textContent = `(${futureDays} days)`;
        if (lstmPriceChange) lstmPriceChange.textContent = `${priceChange >= 0 ? '+' : ''}${priceChange.toFixed(2)}%`;
        if (lstmChangeText) lstmChangeText.textContent = changeText;
        if (lstmHorizon) lstmHorizon.textContent = `${futureDays} days`;
        if (lstmModelType) lstmModelType.textContent = usingPretrained ? 'Pre-trained LSTM' : 'Fresh LSTM';
        if (lstmProcessTime) lstmProcessTime.textContent = processingTime;
        
        // Update confidence/accuracy
        if (lstmConfidence) {
            if (modelMetadata.test_mae !== undefined) {
                const accuracy = Math.max(0, 100 - modelMetadata.test_mae * 100).toFixed(1);
                lstmConfidence.textContent = `${accuracy}%`;
            } else {
                lstmConfidence.textContent = 'High';
            }
        }
        
        // Update change indicator styling
        const changeIndicator = document.getElementById('lstmChangeIndicator');
        if (changeIndicator) {
            const changeBadge = changeIndicator.querySelector('.change-badge');
            if (changeBadge) {
                changeBadge.className = `change-badge ${changeClass}`;
                const badgeIcon = changeBadge.querySelector('i');
                if (badgeIcon) badgeIcon.className = `fas ${changeIcon}`;
            }
        }
        
        // Create prediction chart
        try {
            if (data.predictions && data.future_dates && data.historical_prices && data.historical_dates) {
                this.createLSTMChart({
                    historical: {
                        dates: data.historical_dates,
                        prices: data.historical_prices
                    },
                    predictions: {
                        dates: data.future_dates,
                        prices: data.predictions
                    },
                    symbol: symbol
                });
            }
        } catch (chartError) {
            console.error('Chart creation error:', chartError);
            // Chart error shouldn't break the results display
        }
    }
    
    createLSTMChart(data) {
        const canvas = document.getElementById('lstmPredictionChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        const { historical, predictions, symbol } = data;
        
        // Create datasets with gradient colors
        const datasets = [
            {
                label: 'Historical Prices',
                data: historical.prices.map((price, idx) => ({
                    x: historical.dates[idx],
                    y: price
                })),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            },
            {
                label: 'Predicted Prices',
                data: predictions.prices.map((price, idx) => ({
                    x: predictions.dates[idx],
                    y: price
                })),
                borderColor: '#a855f7',
                backgroundColor: 'rgba(168, 85, 247, 0.1)',
                borderWidth: 3,
                pointRadius: 0,
                borderDash: [5, 5],
                fill: true,
                tension: 0.4
            }
        ];
        
        new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#e5e7eb',
                            font: {
                                size: 12,
                                weight: '500'
                            },
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 46, 0.95)',
                        titleColor: '#e5e7eb',
                        bodyColor: '#e5e7eb',
                        borderColor: 'rgba(168, 85, 247, 0.5)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            label: (context) => {
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: `${symbol || 'Stock'} Price Prediction`,
                        color: '#e5e7eb',
                        font: {
                            size: 16,
                            weight: '600'
                        },
                        padding: 20
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                            displayFormats: {
                                day: 'MMM dd'
                            }
                        },
                        grid: { 
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#9ca3af',
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        grid: { 
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: { 
                            color: '#9ca3af',
                            font: {
                                size: 11
                            },
                            callback: (value) => '$' + value.toFixed(2)
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
    
    async runTradingAgent() {
        console.log('runTradingAgent called!');
        const symbol = document.getElementById('agentSymbol')?.value?.trim();
        const period = document.getElementById('agentPeriod')?.value || '1y';
        const initialFund = parseFloat(document.getElementById('agentInitialFund')?.value) || 10000;
        const skipDays = parseInt(document.getElementById('agentSkipDays')?.value) || 5;
        const strategy = document.getElementById('agentStrategy')?.value || 'ma';
        
        console.log('Trading Agent Parameters:', { symbol, period, initialFund, skipDays, strategy });
        
        if (!symbol) {
            this.showMessage('Please enter a stock symbol', 'error');
            return;
        }
        
        const resultsDiv = document.getElementById('agentResults');
        const runButton = document.getElementById('runTradingAgent');
        
        if (runButton) runButton.disabled = true;
        if (resultsDiv) resultsDiv.innerHTML = '<div class="loading">Running trading simulation...</div>';
        
        try {
            const response = await fetch(
                `${CONFIG.BACKEND.ANALYTICS_URL}/ai/trading-agent?symbol=${encodeURIComponent(symbol)}&period=${period}&initial_fund=${initialFund}&skip_days=${skipDays}&strategy=${strategy}`
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Trading simulation failed');
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.displayTradingResults(data);
                this.showMessage('Trading simulation completed!', 'success');
            } else {
                throw new Error(data.error || 'Trading simulation failed');
            }
        } catch (error) {
            console.error('Trading agent error:', error);
            if (resultsDiv) {
                resultsDiv.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>${error.message}</p>
                    </div>
                `;
            }
            this.showMessage(error.message, 'error');
        } finally {
            if (runButton) runButton.disabled = false;
        }
    }
    
    displayTradingResults(data) {
        const resultsDiv = document.getElementById('agentResults');
        if (!resultsDiv) return;
        
        const { symbol, strategy, metrics, comparison, trades } = data;
        
        const profitClass = metrics.total_profit >= 0 ? 'positive' : 'negative';
        const profitSign = metrics.total_profit >= 0 ? '+' : '';
        const advantageClass = comparison.strategy_advantage >= 0 ? 'positive' : 'negative';
        
        resultsDiv.innerHTML = `
            <div class="ai-results">
                <div class="results-header">
                    <h3>Trading Agent Results for ${symbol}</h3>
                    <span class="badge">${strategy.toUpperCase()} Strategy</span>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Initial Fund</div>
                        <div class="metric-value">$${metrics.initial_fund.toLocaleString()}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Final Value</div>
                        <div class="metric-value ${profitClass}">$${metrics.final_value.toLocaleString()}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Profit/Loss</div>
                        <div class="metric-value ${profitClass}">
                            ${profitSign}$${Math.abs(metrics.total_profit).toLocaleString()}
                            (${profitSign}${metrics.total_return_pct.toFixed(2)}%)
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value">${metrics.num_trades}</div>
                        <div class="metric-sublabel">${metrics.buy_trades} buys, ${metrics.sell_trades} sells</div>
                    </div>
                </div>
                
                <div class="comparison-section">
                    <h4>vs Buy & Hold Strategy</h4>
                    <div class="comparison-grid">
                        <div class="comparison-item">
                            <span class="comparison-label">Buy & Hold Return:</span>
                            <span class="comparison-value">${comparison.buy_hold_return_pct.toFixed(2)}%</span>
                        </div>
                        <div class="comparison-item">
                            <span class="comparison-label">Strategy Advantage:</span>
                            <span class="comparison-value ${advantageClass}">
                                ${comparison.strategy_advantage >= 0 ? '+' : ''}${comparison.strategy_advantage.toFixed(2)}%
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="chart-container" style="height: 400px; margin-top: 20px;">
                    <canvas id="tradingAgentChart"></canvas>
                </div>
            </div>
        `;
        
        // Create trading chart
        this.createTradingChart(data);
    }
    
    createTradingChart(data) {
        const canvas = document.getElementById('tradingAgentChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destroy existing chart
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        const { historical, trades } = data;
        
        // Create price dataset
        const priceData = historical.prices.map((price, idx) => ({
            x: historical.dates[idx],
            y: price
        }));
        
        // Create buy/sell markers
        const buyMarkers = [];
        const sellMarkers = [];
        
        trades.forEach(trade => {
            const marker = {
                x: trade.date,
                y: trade.price
            };
            
            if (trade.action === 'BUY') {
                buyMarkers.push(marker);
            } else {
                sellMarkers.push(marker);
            }
        });
        
        new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Stock Price',
                        data: priceData,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: true
                    },
                    {
                        label: 'Buy',
                        data: buyMarkers,
                        borderColor: '#10b981',
                        backgroundColor: '#10b981',
                        pointRadius: 8,
                        pointStyle: 'triangle',
                        showLine: false
                    },
                    {
                        label: 'Sell',
                        data: sellMarkers,
                        borderColor: '#ef4444',
                        backgroundColor: '#ef4444',
                        pointRadius: 8,
                        pointStyle: 'triangle',
                        rotation: 180,
                        showLine: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: { color: '#e5e7eb' }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                if (context.dataset.label === 'Stock Price') {
                                    return `Price: $${context.parsed.y.toFixed(2)}`;
                                }
                                return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#9ca3af' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { 
                            color: '#9ca3af',
                            callback: (value) => '$' + value.toFixed(2)
                        }
                    }
                }
            }
        });
    }
    
    async loadComprehensiveVisualization() {
        const symbol = document.getElementById('lstmSymbol')?.value?.trim();
        if (!symbol) {
            this.showMessage('Please enter a stock symbol first and run prediction', 'error');
            return;
        }
        
        const container = document.getElementById('visualizationContainer');
        const loading = document.getElementById('visualizationLoading');
        const img = document.getElementById('pythonChart');
        
        if (!container || !loading || !img) {
            console.error('Visualization elements not found');
            return;
        }
        
        try {
            // Hide container, show loading
            container.style.display = 'none';
            loading.style.display = 'block';
            
            const futureDays = parseInt(document.getElementById('lstmFutureDays')?.value) || 30;
            
            const response = await fetch(
                `${CONFIG.API_BASE_URL}/api/ai/visualization/comprehensive-analysis?symbol=${encodeURIComponent(symbol)}&future_days=${futureDays}`
            );
            
            if (!response.ok) {
                throw new Error('Failed to generate comprehensive analysis');
            }
            
            const data = await response.json();
            
            if (!data.success || !data.chart) {
                throw new Error('Analysis generation failed');
            }
            
            // Display the chart
            img.src = `data:image/png;base64,${data.chart}`;
            img.alt = `${symbol} Comprehensive Analysis`;
            
            loading.style.display = 'none';
            container.style.display = 'block';
            
            this.showMessage('Comprehensive analysis generated successfully!', 'success');
            
        } catch (error) {
            console.error('Visualization error:', error);
            loading.style.display = 'none';
            this.showMessage(error.message, 'error');
        }
    }
    
    async loadEnhancedDashboard() {
        const symbol = document.getElementById('lstmSymbol')?.value?.trim();
        if (!symbol) {
            this.showMessage('Please enter a stock symbol first and run prediction', 'error');
            return;
        }
        
        const container = document.getElementById('visualizationContainer');
        const loading = document.getElementById('visualizationLoading');
        const img = document.getElementById('pythonChart');
        
        if (!container || !loading || !img) {
            console.error('Visualization elements not found');
            return;
        }
        
        try {
            // Hide container, show loading
            container.style.display = 'none';
            loading.style.display = 'block';
            loading.innerHTML = `
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: var(--text-secondary);">
                    Generating Enhanced AI Dashboard with 9 advanced charts...<br>
                    <small>This may take 15-20 seconds</small>
                </p>
            `;
            
            const futureDays = parseInt(document.getElementById('lstmFutureDays')?.value) || 30;
            
            // Create AbortController for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
            
            const response = await fetch(
                `${CONFIG.BACKEND.ANALYTICS_URL}/ai/visualization/enhanced-dashboard?symbol=${encodeURIComponent(symbol)}&future_days=${futureDays}`,
                { signal: controller.signal }
            );
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error('Failed to generate enhanced dashboard');
            }
            
            const data = await response.json();
            
            if (!data.success || !data.chart) {
                throw new Error('Dashboard generation failed');
            }
            
            // Display the chart
            img.src = `data:image/png;base64,${data.chart}`;
            img.alt = `${symbol} Enhanced AI Dashboard`;
            
            loading.style.display = 'none';
            container.style.display = 'block';
            
            // Update info text
            const infoText = container.querySelector('small');
            if (infoText) {
                infoText.innerHTML = `
                    <i class="fas fa-check-circle" style="color: var(--accent-green);"></i> 
                    Enhanced dashboard with 9 charts: Main Prediction, Momentum, Volatility Gauge, 
                    Technical Summary, Confidence Meter, Returns Distribution, Accuracy Metrics, Risk Assessment • 
                    <i class="fas fa-info-circle"></i> Click image to open in full size
                `;
            }
            
            this.showMessage('Enhanced AI Dashboard generated successfully! 🎉', 'success');
            
        } catch (error) {
            console.error('Enhanced dashboard error:', error);
            loading.style.display = 'none';
            this.showMessage(error.message, 'error');
        }
    }
}

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.log('Initializing StockSense application...');
        console.log('Config loaded:', typeof CONFIG !== 'undefined');
        console.log('AlphaVantage service loaded:', typeof alphaVantageService !== 'undefined');
        console.log('Data service loaded:', typeof dataService !== 'undefined');
        console.log('Chart service loaded:', typeof chartService !== 'undefined');
        
        window.uiController = new UIController();
        window.uiController.init();
        window.stockSenseApp = window.uiController;
        
        console.log('StockSense application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
        document.body.innerHTML = `
            <div style="padding: 2rem; text-align: center;">
                <h2 style="color: #ef4444;">Application Error</h2>
                <p>Failed to initialize: ${error.message}</p>
                <p style="font-size: 0.9rem; color: #666;">Check the browser console for details</p>
            </div>
        `;
    }
});