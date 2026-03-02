import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import io

# ==========================================================
# 💡 [설정] 구글 시트 URL
# ==========================================================
URL_HEESANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=368982410&single=true&output=csv"
URL_DASOL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=573600297&single=true&output=csv"

# 1. 모바일 화면에 맞춘 페이지 설정
st.set_page_config(page_title="투자 대시보드", layout="centered", initial_sidebar_state="collapsed")

# 2. 현재 사용자 저장소 (희상 <-> 다솔 스위칭용)
if 'current_user' not in st.session_state:
    st.session_state.current_user = "희상"

def toggle_user():
    if st.session_state.current_user == "희상":
        st.session_state.current_user = "다솔"
    else:
        st.session_state.current_user = "희상"

# 3. 데이터 로딩 함수 (5분마다 알아서 새로고침 되도록 캐싱 적용)
@st.cache_data(ttl=300)
def fetch_market_data():
    vix_price = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
    ndx_hist = yf.Ticker("^IXIC").history(period="max")
    ndx_mdd = ((ndx_hist['Close'].iloc[-1] - ndx_hist['High'].max()) / ndx_hist['High'].max()) * 100
    return vix_price, ndx_mdd

@st.cache_data(ttl=300)
def load_google_sheet_data(user):
    target_url = URL_HEESANG if user == "희상" else URL_DASOL
    response = requests.get(target_url)
    response.raise_for_status()
    response.encoding = 'utf-8'
    csv_data = io.StringIO(response.text)
    return pd.read_csv(csv_data, header=None, names=range(30))

def clean_value(val):
    v_str = str(val).strip()
    if v_str.lower() in ["nan", "none", "nat", "<na>"] or v_str.startswith("#"):
        return ""
    return v_str

# --- UI 화면 그리기 ---
st.title(f"👤 {st.session_state.current_user} 대시보드")

# 전환 및 새로고침 버튼
col1, col2 = st.columns(2)
with col1:
    st.button("🔄 최신 데이터 불러오기", on_click=st.cache_data.clear, use_container_width=True)
with col2:
    other_user = "다솔" if st.session_state.current_user == "희상" else "희상"
    st.button(f"{other_user} 대시보드로 전환", on_click=toggle_user, use_container_width=True)

# 시장 지표 (VIX, 나스닥) 표시
try:
    vix, ndx = fetch_market_data()
    
    # 색상 결정 로직
    vix_c = "#1e8e3e" if vix < 20 else "#b8860b" if vix < 30 else "#d95f02" if vix < 40 else "#8b0000"
    ndx_c = "#1e8e3e" if ndx > -20 else "#d4ac0d" if ndx > -30 else "#b8860b" if ndx > -40 else "#ff8c00" if ndx > -50 else "#d95f02" if ndx > -60 else "#ea4335" if ndx > -70 else "#8b0000"

    st.markdown(f"**VIX:** <span style='color:{vix_c}'>{vix:.2f}</span> &nbsp; | &nbsp; **나스닥 고점대비:** <span style='color:{ndx_c}'>{ndx:.2f}%</span>", unsafe_allow_html=True)
except:
    st.warning("시장 데이터를 불러오지 못했습니다.")

st.divider() # 구분선

# 구글 시트 데이터 표 그리기
try:
    df_raw = load_google_sheet_data(st.session_state.current_user)
    
    data = []
    row_indices = [23] + list(range(4, 23))
    
    for row_idx in row_indices:
        if row_idx >= len(df_raw): continue
        
        c_val = clean_value(df_raw.iloc[row_idx, 2])
        if row_idx == 23 and not c_val:
            b_val = clean_value(df_raw.iloc[row_idx, 1])
            c_val = b_val if b_val else "전체 요약"
            
        d_val = clean_value(df_raw.iloc[row_idx, 3])
        e_val = clean_value(df_raw.iloc[row_idx, 4])
        j_val = clean_value(df_raw.iloc[row_idx, 9])
        k_val = clean_value(df_raw.iloc[row_idx, 10])
        lower_val = clean_value(df_raw.iloc[row_idx, 19])
        upper_val = clean_value(df_raw.iloc[row_idx, 20])
        
        data.append({
            "종목명": c_val,
            "목표": d_val,
            "현재": e_val,
            "수익율": j_val,
            "수익금": k_val,
            "하한선": lower_val,
            "상한선": upper_val,
            "excel_row": row_idx + 1,
            "is_total": row_idx == 23
        })
        
    df_disp = pd.DataFrame(data)

    # 엑셀의 조건부 서식을 웹사이트용으로 번역하는 함수
    def apply_styles(row):
        styles = [''] * len(row)
        is_total = row['is_total']
        excel_row = row['excel_row']
        
        # 합계 줄 디자인
        if is_total:
            return ['background-color: #fff2cc; font-weight: bold; color: black;'] * len(row)
            
        # 비중 상/하한선 알람 디자인
        bg_color, fg_color = "", ""
        if (6 <= excel_row <= 12) or (14 <= excel_row <= 22):
            try:
                curr = float(row['현재'].replace('%', '').strip())
                low_v = row['하한선']
                up_v = row['상한선']
                if low_v and up_v:
                    low_b = float(low_v.replace('%', '').strip())
                    up_b = float(up_v.replace('%', '').strip())
                    if curr > up_b:
                        bg_color, fg_color = "#ffe6e6", "#d93025"
                    elif curr < low_b:
                        bg_color, fg_color = "#e8f0fe", "#1a73e8"
            except:
                pass
        
        if bg_color:
            styles[2] = f'background-color: {bg_color}; color: {fg_color};' # 현재 비중 열
            
        # 수익률(3) 및 수익금(4) 색상 (음수 파랑, 양수 빨강)
        for i in [3, 4]:
            val = row.iloc[i]
            if val:
                if "-" in val:
                    styles[i] = 'color: #1a73e8;'
                elif val not in ["0", "0.00%", "0.0%"]:
                    styles[i] = 'color: #d93025;'
                    
        return styles

    # 디자인 적용
    styled_df = df_disp.style.apply(apply_styles, axis=1)

    # 불필요한 계산용 열(하한, 상한 등)은 모바일 화면에서 숨기고 출력합니다.
    st.dataframe(
        styled_df,
        column_config={
            "하한선": None,
            "상한선": None,
            "excel_row": None,
            "is_total": None
        },
        hide_index=True,
        use_container_width=True
    )

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")