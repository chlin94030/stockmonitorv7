import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 網頁基本設定與手機 UI 樣式
# ==========================================
st.set_page_config(
    page_title="台股行動智慧盯盤大師 Pro", 
    page_icon="📈", 
    layout="centered"
)

st.markdown('''
<style>
    .main-title {
        font-size: 1.5rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(45deg, #3b82f6, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        text-align: center;
        color: #64748b;
        font-size: 0.75rem;
        margin-bottom: 10px;
    }
    .stock-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .badge {
        background-color: #f1f5f9;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        color: #334155;
        font-weight: 600;
    }
    .personality-box {
        background-color: #eff6ff;
        border-left: 4px solid #3b82f6;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 0.78rem;
        color: #1e3a8a;
        margin-top: 8px;
    }
</style>
''', unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 台股行動智慧盯盤大師 Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">專業K線布林通道 x KD/MACD動能 x 股性深度總評</p>', unsafe_allow_html=True)

# ==========================================
# 2. 股票資料與股性定義
# ==========================================
STOCK_DATA = {
    "6187.TWO": {
        "name": "萬潤",
        "strategy": "🚀 短線動能",
        "personality": "【中小型飆股/半導體設備】股性活潑、受投信認養與先進封裝題材高度聯動，短線爆發力強但波動劇烈，適合抓突破與回測支撐。"
    },
    "2449.TW": {
        "name": "京元電子",
        "strategy": "🚀 短線動能",
        "personality": "【AI晶片測試大廠】具備法人籌碼優勢，常隨營收月增率與AI題材起伏，股性偏向穩健中帶有強勢攻擊力。"
    },
    "2360.TW": {
        "name": "致茂",
        "strategy": "🚀 短線動能",
        "personality": "【量測設備/權值高價股】股本適中，法人籌碼穩定，常走波段趨勢，不容易暴漲暴跌，適合中低接。"
    },
    "2382.TW": {
        "name": "廣達",
        "strategy": "📈 中線波段",
        "personality": "【AI伺服器代工龍頭】權值股特性，成交量極大，易受外資動向影響，屬於大浪型走勢，適合月線附近逢低承接。"
    },
    "2327.TW": {
        "name": "國巨",
        "strategy": "📈 中線波段",
        "personality": "【被動元件龍頭】具景氣循環股特性，股性牛皮但常在谷底翻揚時出現急漲，適合長線佈局。"
    },
    "3034.TW": {
        "name": "聯詠",
        "strategy": "📈 中線波段",
        "personality": "【IC設計大廠】高殖利率與配息防禦特性，股價波動受面板及消費性電子需求主導，屬於穩健收益兼具價差型。"
    },
    "2330.TW": {
        "name": "台積電",
        "strategy": "🏰 長線價值",
        "personality": "【護國神山/全球晶圓代工】台股定海神針，外資提款機與資金避風港，長線多頭排列時回測月季線皆為有效買點。"
    },
    "2412.TW": {
        "name": "中華電",
        "strategy": "🏰 長線價值",
        "personality": "【防禦型高股息】股性極度溫和、波動低、抗跌性強，適合存股與資產配置，較少出現短線飆漲。"
    }
}

STRATEGIES = {
    "🚀 短線動能 (動能與突破)": ["6187.TWO", "2449.TW", "2360.TW"],
    "📈 中線波段 (布林與法人趨勢)": ["2382.TW", "2327.TW", "3034.TW", "2330.TW"],
    "🏰 長線價值 (權值與防禦股)": ["2330.TW", "2412.TW"]
}

selected_strategy = st.selectbox("🎯 選擇操作策略週期：", list(STRATEGIES.keys()))

# 時間區間選擇
time_range = st.selectbox("⏳ 選擇K線圖表觀察區間：", ["近 1 個月 (1mo)", "近 3 個月 (3mo)", "近 1 年 (1y)"], index=1)
period_map = {"近 1 個月 (1mo)": "1mo", "近 3 個月 (3mo)": "3mo", "近 1 年 (1y)": "1y"}
selected_period = period_map[time_range]

# ==========================================
# 3. 技術指標計算核心
# ==========================================
def calculate_indicators(df):
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean() if len(df) >= 60 else df['Close'].rolling(window=len(df)).mean()
    
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['STD'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['STD'] * 2)
    
    low_9 = df['Low'].rolling(window=9).min()
    high_9 = df['High'].rolling(window=9).max()
    rsv = (df['Close'] - low_9) / (high_9 - low_9 + 1e-9) * 100
    df['K'] = rsv.ewm(com=2).mean()
    df['D'] = df['K'].ewm(com=2).mean()
    
    ema12 = df['Close'].ewm(span=12, adjust=False).mean()
    ema26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = ema12 - ema26
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']
    return df

@st.cache_data(ttl=60)
def get_stock_analysis(tickers, period):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)
            if df.empty or len(df) < 10:
                continue
            
            df = calculate_indicators(df)
            
            curr = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            chg = (curr - prev) / prev * 100
            
            vol_curr = df['Volume'].iloc[-1]
            vol_avg = df['Volume'].rolling(window=5).mean().iloc[-1]
            vol_status = "🔥 放量大增" if vol_curr > vol_avg * 1.3 else ("❄️ 量縮整理" if vol_curr < vol_avg * 0.7 else "📊 成交量平穩")
            
            k_val = df['K'].iloc[-1]
            d_val = df['D'].iloc[-1]
            prev_k = df['K'].iloc[-2]
            prev_d = df['D'].iloc[-2]
            kd_trend = "🔥 黃金交叉" if (prev_k < prev_d and k_val >= d_val) else ("❄️ 死亡交叉" if (prev_k > prev_d and k_val <= d_val) else ("📈 K>D 多頭" if k_val > d_val else "📉 K<D 空頭"))
            
            hist_curr = df['MACD_Hist'].iloc[-1]
            hist_prev = df['MACD_Hist'].iloc[-2]
            macd_trend = "🚀 柱狀翻紅/擴增" if (hist_curr > hist_prev) else "⚠️ 柱狀縮減/翻綠"
            
            # 建立 Plotly 專業圖表 (仿照專業看盤軟體排版)
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.7, 0.3])
            
            # 1. 蠟燭圖 (紅綠K線) 與 均線、布林通道
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name='K線', increasing_line_color='#ef4444', decreasing_line_color='#22c55e'
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5MA', line=dict(color='#eab308', width=1)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20MA', line=dict(color='#3b82f6', width=1.2)), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='布林上軌', line=dict(color='#cbd5e1', width=1, dash='dash')), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='布林下軌', line=dict(color='#cbd5e1', width=1, dash='dash')), row=1, col=1)
            
            # 2. 成交量圖
            colors = ['#ef4444' if row['Close'] >= row['Open'] else '#22c55e' for index, row in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=colors), row=2, col=1)
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f1f5f9')
            
            meta = STOCK_DATA.get(ticker, {"name": "個股", "personality": "穩健"})
            
            results.append({
                "code": ticker.replace(".TW", "").replace(".TWO", ""),
                "name": meta["name"],
                "price": round(curr, 2),
                "change": f"{chg:+.2f}%",
                "is_up": chg >= 0,
                "k": round(k_val, 1),
                "d": round(d_val, 1),
                "kd_trend": kd_trend,
                "macd_trend": macd_trend,
                "vol_status": vol_status,
                "personality": meta["personality"],
                "chart": fig
            })
        except Exception:
            continue
    return results

# ==========================================
# 4. 執行與畫面呈現
# ==========================================
if st.button("🔄 立即載入專業K線與技術分析", type="primary", use_container_width=True):
    with st.spinner("正在繪製K線圖、計算布林通道、KD與MACD變化..."):
        analysis_results = get_stock_analysis(STRATEGIES[selected_strategy], selected_period)
    
    st.success(f"載入成功！時間：{datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    
    for item in analysis_results:
        color_style = "color: #ef4444;" if item["is_up"] else "color: #22c55e;"
        
        st.markdown(f"""
        <div class="stock-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">{item['code']} {item['name']}</span>
                </div>
                <div style="text-align: right; {color_style} font-weight: bold; font-size: 1.05rem;">
                    {item['price']} ({item['change']})
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # 顯示專業互動式K線與成交量圖表
        st.plotly_chart(item['chart'], use_container_width=True, config={'displayModeBar': False})
        
        st.markdown(f"""
            <hr style="margin: 4px 0; border: none; border-top: 1px solid #f1f5f9;">
            <div style="font-size: 0.8rem; color: #334155; line-height: 1.5;">
                📊 <b>KD指標變化：</b> K({item['k']}) / D({item['d']}) ➔ <b>{item['kd_trend']}</b><br>
                📈 <b>MACD動能：</b> <b>{item['macd_trend']}</b><br>
                📦 <b>成交量變化：</b> <b>{item['vol_status']}</b>
            </div>
            <div class="personality-box">
                💡 <b>個股股性總評：</b> {item['personality']}
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("<br><p style='text-align: center; color: #888;'>👆 點擊上方按鈕開始載入專屬個股專業圖表與分析</p>", unsafe_allow_html=True)

st.markdown("---")
st.caption("⚠️ 聲明：本工具提供之技術分析與股性總評僅供量化研究與追蹤參考，不代表投資買賣建議。")