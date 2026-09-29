import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 1. 網頁基本設定與頂級手機美化 CSS
# ==========================================
st.set_page_config(
    page_title="台股行動盯盤大師",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* 全局行動端優化背景與字體 */
    .stApp {
        background-color: #f4f6f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 頂部炫彩標題 */
    .hero-banner {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .hero-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .hero-subtitle {
        font-size: 0.85rem;
        opacity: 0.85;
    }

    /* 手機美化卡片設計 */
    .stock-card {
        background: #ffffff;
        padding: 16px;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        margin-bottom: 14px;
        border-left: 6px solid #4ECDC4;
        transition: transform 0.2s;
    }
    .card-red { border-left-color: #FF6B6B; }
    .card-green { border-left-color: #2ECC71; }

    /* 徽章樣式 */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 6px;
        background-color: #eef2f7;
        color: #555;
        margin-right: 4px;
    }
    .badge-success { background-color: #e1fdf4; color: #0d9488; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 策略資料庫設定
# ==========================================
STRATEGIES = {
    "🔥 短線策略 (動能突破)": {
        "desc": "專注短線資金動能，嚴守 5/10 日線停損。",
        "stocks": ["6187.TWO", "2449.TW", "3324.TW"],
        "names": ["萬潤", "京元電", "雙鴻"]
    },
    "📈 中線策略 (波段趨勢)": {
        "desc": "主升段大戶籌碼追蹤，逢回月季線佈局。",
        "stocks": ["2382.TW", "2327.TW", "3034.TW", "2330.TW"],
        "names": ["廣達", "國巨", "聯詠", "台積電"]
    },
    "🏰 長線策略 (價值護城河)": {
        "desc": "低基期權值股與高殖利率防禦配置。",
        "stocks": ["2330.TW", "1301.TW", "1101.TW", "2412.TW"],
        "names": ["台積電", "台塑", "台泥", "中華電"]
    }
}

# ==========================================
# 3. 穩定抓取與 100% 防呆容錯函數
# ==========================================
@st.cache_data(ttl=60)
def fetch_stock_data(tickers):
    data_list = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")
            
            if hist.empty or len(hist) < 5:
                data_list.append({"ticker": ticker, "status": "資料不足"})
                continue
                
            price = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2])
            change = price - prev
            change_pct = (change / prev) * 100
            
            ma5 = float(hist['Close'].rolling(5).mean().iloc[-1])
            ma20 = float(hist['Close'].rolling(20).mean().iloc[-1])
            ma60 = float(hist['Close'].rolling(60).mean().iloc[-1]) if len(hist) >= 60 else ma20
            
            data_list.append({
                "ticker": ticker.replace(".TW", "").replace(".TWO", ""),
                "price": price,
                "change": change,
                "change_pct": change_pct,
                "ma5": ma5,
                "ma20": ma20,
                "ma60": ma60,
                "is_bull": price > ma5 > ma20,
                "above_season": price > ma60,
                "status": "OK"
            })
        except Exception:
            data_list.append({"ticker": ticker.replace(".TW", "").replace(".TWO", ""), "status": "連線異常"})
    return data_list

# ==========================================
# 4. 行動版介面排版
# ==========================================
tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%m/%d %H:%M')

st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-title">📈 台股行動智慧盯盤</div>
        <div class="hero-subtitle">更新時間：{tw_time} | 專為手機瀏覽優化</div>
    </div>
""", unsafe_allow_html=True)

# 策略選單
selected_key = st.selectbox("🎯 切換盯盤策略：", list(STRATEGIES.keys()))
strat = STRATEGIES[selected_key]

st.info(f"💡 **核心邏輯：** {strat['desc']}")

if st.button("🔄 立即重新整理盤勢", type="primary", use_container_width=True):
    st.toast("正在從雲端抓取即時報價...", icon="⚡")

# 獲取資料
with st.spinner("正在計算均線與多空訊號..."):
    results = fetch_stock_data(strat["stocks"])

st.markdown("### 📊 監控清單即時卡片")

# 渲染美化卡片
for item in results:
    if item["status"] != "OK":
        st.warning(f"⚠️ 股票 {item['ticker']} 暫時無法取得完整資料")
        continue
        
    is_up = item["change"] >= 0
    card_class = "card-green" if is_up else "card-red"
    color_code = "#2ECC71" if is_up else "#FF6B6B"
    sign = "+" if is_up else ""
    
    st.markdown(f"""
        <div class="stock-card {card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.15rem; font-weight: 700; color: #1e293b;">{item['ticker']}</span>
                    <div style="margin-top: 4px;">
                        <span class="badge badge-success">{'多頭排列' if item['is_bull'] else '盤整修正'}</span>
                        <span class="badge">{'站上季線' if item['above_season'] else '季線之下'}</span>
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.25rem; font-weight: 800; color: #0f172a;">{item['price']:.2f}</div>
                    <div style="font-size: 0.85rem; font-weight: 600; color: {color_code};">
                        {sign}{item['change']:.2f} ({sign}{item['change_pct']:.2f}%)
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("📱 提示：點擊瀏覽器選單的「加入主畫面」，即可當成 App 隨時隨地輕鬆盯盤！")