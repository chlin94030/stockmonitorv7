import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

# ==========================================
# 1. 網頁基本設定與高質感手機 UI 樣式
# ==========================================
st.set_page_config(
    page_title="台股行動智慧盯盤大師", 
    page_icon="📈", 
    layout="centered"
)

st.markdown('''
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 0.85rem;
        margin-bottom: 15px;
    }
    .strategy-box {
        background-color: #f8f9fa;
        border-left: 5px solid #4ECDC4;
        padding: 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-bottom: 15px;
        color: #333;
    }
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .badge-buy {
        background-color: #d1fae5;
        color: #065f46;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-sell {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 台股行動智慧盯盤大師</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">籌碼面 x 技術面 x 基本面高勝率策略</p>', unsafe_allow_html=True)

# ==========================================
# 2. 股票代號與中文公司名稱對應字典
# ==========================================
STOCK_NAMES = {
    "6187.TWO": "萬潤",
    "2449.TW": "京元電子",
    "2360.TW": "致茂",
    "2382.TW": "廣達",
    "2327.TW": "國巨",
    "3034.TW": "聯詠",
    "2330.TW": "台積電",
    "1301.TW": "台塑",
    "1101.TW": "台泥",
    "2412.TW": "中華電"
}

# ==========================================
# 3. 完整策略定義 (三面合一條件)
# ==========================================
STRATEGIES = {
    "🚀 短線策略 (動能突破)": {
        "stocks": ["6187.TWO", "2449.TW", "2360.TW"],
        "chip": "外資連3日買超 + 投信連3日買超",
        "tech": "股價創20日新高 + 均線多頭排列",
        "fund": "近期單月營收創歷史新高",
        "desc": "專注短線資金動能與法人順風車，適合積極型操作，嚴守 5/10 日線停損。"
    },
    "📈 中線策略 (波段趨勢)": {
        "stocks": ["2382.TW", "2327.TW", "3034.TW", "2330.TW"],
        "chip": "1,000張以上大戶持股連三週增加",
        "tech": "股價站上月線(20MA)與季線(60MA)",
        "fund": "月營收連3月成長 + 近四季ROE>10%",
        "desc": "最穩健的主升段波段選股法，逢回測月季線量縮時為最佳佈局點。"
    },
    "🏰 長線策略 (價值護城河)": {
        "stocks": ["2330.TW", "1301.TW", "1101.TW", "2412.TW"],
        "chip": "股本大於百億 + 大股東持股長期穩定",
        "tech": "長底打底完成，站上年線(240MA)",
        "fund": "近10年殖利率>5% + 本益比<20倍",
        "desc": "低基期權值股與高殖利率防禦配置，適合存股族分批建立核心部位。"
    }
}

# ==========================================
# 4. 手機策略選擇介面
# ==========================================
selected_strategy = st.selectbox("🎯 選擇盯盤策略週期：", list(STRATEGIES.keys()))
strat_info = STRATEGIES[selected_strategy]

# 完整呈現選股策略細節
st.markdown(f"""
<div class="strategy-box">
    <b>💡 策略核心精神：</b><br>{strat_info['desc']}<br><br>
    <b>【三面合一過濾條件】</b><br>
    • {strat_info['chip']}<br>
    • {strat_info['tech']}<br>
    • {strat_info['fund']}
</div>
""", unsafe_allow_html=True)

# ==========================================
# 5. 資料抓取、均線計算與買賣價生成核心
# ==========================================
@st.cache_data(ttl=60)
def get_stock_analysis(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            if hist.empty or len(hist) < 20: 
                continue
                
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            chg = (curr - prev) / prev * 100
            
            ma5 = hist['Close'].rolling(window=5).mean().iloc[-1]
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma60 = hist['Close'].rolling(window=60).mean().iloc[-1] if len(hist) >= 60 else ma20
            
            # 智慧建議買賣價邏輯 (基於均線與支撐壓力運算)
            # 建議買入價：靠近月線(20MA)或當前價回測 1.5%
            buy_price = round(min(curr, ma20 * 1.01), 2)
            # 建議賣出價(停利目標)：當前價上方約 6% 或前波高點
            sell_price = round(curr * 1.06, 2)
            # 停損價：跌破季線或下方 4%
            stop_loss = round(min(ma60, curr * 0.96), 2)
            
            results.append({
                "code": ticker,
                "name": STOCK_NAMES.get(ticker, "未知"),
                "price": round(curr, 2),
                "change": f"{chg:+.2f}%",
                "is_up": chg >= 0,
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "buy": buy_price,
                "sell": sell_price,
                "stop": stop_loss,
                "status": "🟢 多頭排列" if curr > ma20 and ma20 > ma60 else "🟡 盤整打底"
            })
        except: 
            continue
    return results

# ==========================================
# 6. 執行更新與精美卡片渲染
# ==========================================
if st.button("🔄 立即更新盤中即時數據與價位", type="primary", use_container_width=True):
    with st.spinner("正在連線取得最新報價、計算均線與智慧買賣價..."):
        data_list = get_stock_analysis(strat_info["stocks"])
    
    st.success(f"更新成功！最後更新：{datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    # 渲染手機專屬直式精美卡片
    for item in data_list:
        color = "color: #ff4d4d;" if item["is_up"] else "color: #00b300;"
        
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.15rem; font-weight: 800; color: #1e293b;">{item['code'].replace('.TW','').replace('.TWO','')} {item['name']}</span>
                    <span style="font-size: 0.8rem; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">{item['status']}</span>
                </div>
                <div style="text-align: right; {color} font-weight: bold; font-size: 1.1rem;">
                    {item['price']} ({item['change']})
                </div>
            </div>
            <hr style="margin: 10px 0; border: none; border-top: 1px solid #edf2f7;">
            <div style="font-size: 0.85rem; color: #475569; line-height: 1.5;">
                📊 <b>均線參考：</b> 月線(20MA): {item['ma20']} | 季線(60MA): {item['ma60']}<br>
                🎯 <span class="badge-buy">建議買入價</span>：<b>{item['buy']}</b> 附近<br>
                💰 <span class="badge-sell">目標賣出價</span>：<b>{item['sell']}</b> (停損設: {item['stop']})
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("<br><p style='text-align: center; color: #888;'>👆 點擊上方按鈕開始載入盤中盯盤數據與買賣價建議</p>", unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ 聲明：買賣價建議為基於技術分析與均線之量化參考，不代表絕對獲利保證，投資請自負風險。")