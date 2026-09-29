import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ==========================================
# 1. 網頁基本設定 (手機版面優化)
# ==========================================
st.set_page_config(
    page_title="台股行動智慧盯盤", 
    page_icon="📈", 
    layout="centered"
)

# 自訂 CSS 樣式
st.markdown('''
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        text-align: center;
        background: -webkit-linear-gradient(45deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 20px;
    }
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 台股行動智慧盯盤系統</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">籌碼面 x 技術面 x 基本面 x 智慧化量化評分</p>', unsafe_allow_html=True)

# ==========================================
# 2. 策略清單與個股對照
# ==========================================
STRATEGIES = {
    "🚀 短線動能強勢股": {
        "stocks": ["6187.TWO", "2449.TW", "2360.TW", "3034.TW"],
        "desc": "外資投信連買、創短天期新高、成交量放大之動能標的",
        "personality": "高貝塔值、短線爆發力強、波動度較大，適合守好停損快速進出。"
    },
    "📈 中線波段多頭股": {
        "stocks": ["2382.TW", "2327.TW", "2330.TW", "3711.TW"],
        "desc": "站穩月季線、大戶持股增加、營收連月成長之波段好股",
        "personality": "中大型權值或產業龍頭，走勢較具趨勢性，適合沿月線（20MA）操作。"
    },
    "🏰 長線價值收息股": {
        "stocks": ["2412.TW", "1301.TW", "1101.TW", "2881.TW"],
        "desc": "股本雄厚、現金殖利率穩健、長線站穩年線之防禦標的",
        "personality": "低波動、防禦型收益股，股性牛皮但抗跌，適合分批低接領息。"
    }
}

STOCK_NAMES = {
    "6187.TWO": "萬潤 (半導體設備)",
    "2449.TW": "京元電子 (封測)",
    "2360.TW": "致茂 (量測設備)",
    "3034.TW": "聯詠 (IC設計)",
    "2382.TW": "廣達 (AI伺服器)",
    "2327.TW": "國巨 (被動元件)",
    "2330.TW": "台積電 (晶圓代工)",
    "3711.TW": "日月光投控 (先進封測)",
    "2412.TW": "中華電 (電信防禦)",
    "1301.TW": "台塑 (塑化權值)",
    "1101.TW": "台泥 (水泥傳產)",
    "2881.TW": "富邦金 (金融龍頭)"
}

selected_strategy = st.selectbox("🎯 選擇操作策略週期：", list(STRATEGIES.keys()))
st.info(f"💡 **篩選邏輯：** {STRATEGIES[selected_strategy]['desc']}\n\n🛡️ **個股股性解析：** {STRATEGIES[selected_strategy]['personality']}")

# ==========================================
# 3. 技術指標計算
# ==========================================
def calculate_indicators(df):
    df['5MA'] = df['Close'].rolling(window=5).mean()
    df['20MA'] = df['Close'].rolling(window=20).mean()
    df['60MA'] = df['Close'].rolling(window=60).mean()
    
    std20 = df['Close'].rolling(window=20).std()
    df['BB_UP'] = df['20MA'] + (std20 * 2)
    df['BB_DOWN'] = df['20MA'] - (std20 * 2)
    
    low_min = df['Low'].rolling(window=9).min()
    high_max = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_min) / (high_max - low_min + 1e-9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    ema12 = df['Close'].ewm(span=12).mean()
    ema26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    return df

@st.cache_data(ttl=60)
def analyze_stocks(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1y")
            if hist.empty or len(hist) < 60:
                continue
            hist = calculate_indicators(hist)
            curr = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            chg_pct = (curr - prev) / prev * 100
            
            ma5 = hist['5MA'].iloc[-1]
            ma20 = hist['20MA'].iloc[-1]
            ma60 = hist['60MA'].iloc[-1]
            bb_up = hist['BB_UP'].iloc[-1]
            bb_down = hist['BB_DOWN'].iloc[-1]
            
            k_val = hist['K'].iloc[-1]
            d_val = hist['D'].iloc[-1]
            prev_k = hist['K'].iloc[-2]
            prev_d = hist['D'].iloc[-2]
            
            kd_cross = "金交叉 🟢" if (prev_k < prev_d and k_val >= d_val) else ("死交叉 🔴" if (prev_k > prev_d and k_val <= d_val) else ("多頭整理" if k_val > d_val else "空頭整理"))
            macd_hist = hist['Hist'].iloc[-1]
            prev_hist = hist['Hist'].iloc[-2]
            macd_status = "柱狀翻紅 🟢" if (prev_hist < 0 and macd_hist >= 0) else ("多方擴增" if macd_hist > 0 else "空方整理")
            
            vol_curr = hist['Volume'].iloc[-1]
            vol_avg5 = hist['Volume'].rolling(window=5).mean().iloc[-1]
            vol_status = "🔥 爆量放大" if vol_curr > (vol_avg5 * 1.5) else ("量縮整理" if vol_curr < (vol_avg5 * 0.7) else "成交量平穩")
            
            score = 50
            if curr > ma20: score += 15
            if curr > ma60: score += 15
            if "金交叉" in kd_cross: score += 10
            if macd_hist > 0: score += 10
            score = min(max(score, 10), 95)
            recommendation = "🔥 強力買進 / 順勢加碼" if score >= 80 else ("⚖️ 逢低佈局 / 區間操作" if score >= 60 else "⚠️ 觀望保守 / 注意風險")

            results.append({
                "ticker": ticker,
                "name": STOCK_NAMES.get(ticker, ticker),
                "price": round(curr, 2),
                "change": f"{chg_pct:+.2f}%",
                "is_up": chg_pct >= 0,
                "ma5": round(ma5, 2),
                "ma20": round(ma20, 2),
                "ma60": round(ma60, 2),
                "bb_up": round(bb_up, 2),
                "bb_down": round(bb_down, 2),
                "k": round(k_val, 1),
                "d": round(d_val, 1),
                "kd_cross": kd_cross,
                "macd_status": macd_status,
                "vol_status": vol_status,
                "score": score,
                "recommendation": recommendation,
                "hist_data": hist
            })
        except:
            continue
    return results

if st.button("🔄 立即更新盤中數據與技術指標", type="primary", use_container_width=True):
    with st.spinner("正在計算布林通道、KD、MACD與智慧評分..."):
        stock_list = analyze_stocks(STRATEGIES[selected_strategy]["stocks"])
    
    st.success(f"更新成功！時間：{datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    for item in stock_list:
        color_style = "color: #ff4d4d;" if item["is_up"] else "color: #00b300;"
        with st.container():
            st.markdown(f"""
            <div class="stock-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 1.2rem; font-weight: bold;">{item['name']}</span>
                    <span style="font-size: 1.1rem; font-weight: bold; {color_style}">{item['price']} ({item['change']})</span>
                </div>
                <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
                <div style="font-size: 0.85rem; color: #444; line-height: 1.6;">
                    <b>智慧綜合評分：</b> <span style="color: #0066cc; font-size: 1rem; font-weight: bold;">{item['score']} 分</span> ({item['recommendation']})<br>
                    <b>技術指標：</b> 5MA: {item['ma5']} | 月線: {item['ma20']} | 季線: {item['ma60']}<br>
                    <b>布林通道：</b> 頂軌: {item['bb_up']} | 底軌: {item['bb_down']}<br>
                    <b>動能狀態：</b> KD ({item['k']}/{item['d']}) [{item['kd_cross']}] | MACD [{item['macd_status']}] | {item['vol_status']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            df_plot = item["hist_data"]
            time_period = st.selectbox(f"📊 選擇【{item['name']}】走勢週期", ["近 1 個月", "近 3 個月", "近 1 年"], key=f"sel_{item['ticker']}")
            
            df_sub = df_plot.tail(22) if time_period == "近 1 個月" else (df_plot.tail(66) if time_period == "近 3 個月" else df_plot)
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(
                x=df_sub.index, open=df_sub['Open'], high=df_sub['High'], low=df_sub['Low'], close=df_sub['Close'],
                increasing_line_color='#ff4d4d', decreasing_line_color='#00b300', name='K線'
            ), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_sub.index, y=df_sub['5MA'], name='5MA', line=dict(color='#ff9900', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_sub.index, y=df_sub['20MA'], name='20MA', line=dict(color='#0066ff', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_sub.index, y=df_sub['BB_UP'], name='布林上', line=dict(color='gray', width=0.8, dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_sub.index, y=df_sub['BB_DOWN'], name='布林下', line=dict(color='gray', width=0.8, dash='dash')), row=1, col=1)
            
            colors = ['#ff4d4d' if c >= o else '#00b300' for c, o in zip(df_sub['Close'], df_sub['Open'])]
            fig.add_trace(go.Bar(x=df_sub.index, y=df_sub['Volume'], name='成交量', marker_color=colors), row=2, col=1)
            
            fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{item['ticker']}")
            st.markdown("---")
else:
    st.markdown("<br><p style='text-align: center; color: #888;'>👆 點擊上方按鈕開始載入盤中智慧分析數據</p>", unsafe_allow_html=True)
