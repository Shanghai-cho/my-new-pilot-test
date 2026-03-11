import streamlit as st
import pandas as pd
import requests
import io

# ==========================================================
# 💡 [설정] 구글 시트 URL
# ==========================================================
URL_HEESANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=368982410&single=true&output=csv"
URL_DASOL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=573600297&single=true&output=csv"

# 1. 페이지 설정 (넓게 쓰기 모드)
st.set_page_config(page_title="투자 대시보드", layout="centered", initial_sidebar_state="collapsed")

# ==========================================================
# 💡 [모바일 최적화 디자인] 여백 축소 및 '한눈에 들어오는 표' 강제 적용
# ==========================================================
st.markdown("""
<style>
    /* 상하좌우 여백 극단적 축소 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stButton"] button {
        padding: 0.2rem 0.5rem !important;
        font-size: 13px !important;
    }
    .stMarkdown p {
        font-size: 13px !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 💡 가로 스크롤을 없애는 마법의 모바일 전용 표 디자인 */
    .mobile-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 11px !important; /* 모바일에 딱 맞는 글씨 크기 */
        margin-top: 10px;
    }
    .mobile-table th {
        background-color: #f0f2f6;
        color: #333;
        text-align: center !important;
        padding: 6px 2px;
        border-bottom: 2px solid #ccc;
        white-space: nowrap;
    }
    .mobile-table td {
        padding: 6px 2px;
        text-align: right;
        border-bottom: 1px solid #eee;
        white-space: nowrap; /* 숫자는 줄바꿈 안 됨 */
    }
    /* 1번째 열(종목명)은 왼쪽 정렬하고, 글자가 길면 알아서 줄바꿈 되도록 허용! */
    .mobile-table td:nth-child(1) {
        text-align: left !important;
        white-space: normal !important; 
        word-break: keep-all;
    }
</style>
""", unsafe_allow_html=True)

# 2. 현재 사용자 스위칭
if 'current_user' not in st.session_state:
    st.session_state.current_user = "희상"

def toggle_user():
    if st.session_state.current_user == "희상":
        st.session_state.current_user = "다솔"
    else:
        st.session_state.current_user = "희상"

# 3. 데이터 로딩 (5분 캐싱)
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

col1, col2 = st.columns(2)
with col1:
    st.button("🔄 최신화", on_click=st.cache_data.clear, use_container_width=True)
with col2:
    other_user = "다솔" if st.session_state.current_user == "희상" else "희상"
    st.button(f"➡️ {other_user} 전환", on_click=toggle_user, use_container_width=True)

try:
    df_raw = load_google_sheet_data(st.session_state.current_user)
    
    # ==========================================================
    # 💡 [에러 해결] PC 위젯과 똑같이 C2(iloc[1,2]), J2(iloc[1,9]) 강제 지정
    # ==========================================================
    try:
        vix_str = str(df_raw.iloc[1, 2]).replace(',', '').strip()
        vix = float(vix_str)
    except:
        vix = 0.0
        vix_str = "0"

    try:
        ndx_str = str(df_raw.iloc[1, 9]).strip()
        ndx = float(ndx_str.replace('%', ''))
    except:
        ndx = 0.0
        ndx_str = "0%"

    vix_c = "#1e8e3e" if vix < 20 else "#b8860b" if vix < 30 else "#d95f02" if vix < 40 else "#8b0000"
    ndx_c = "#1e8e3e" if ndx > -20 else "#d4ac0d" if ndx > -30 else "#b8860b" if ndx > -40 else "#ff8c00" if ndx > -50 else "#d95f02" if ndx > -60 else "#ea4335" if ndx > -70 else "#8b0000"

    st.markdown(f"**VIX:** <span style='color:{vix_c}'>{vix_str}</span> &nbsp; | &nbsp; **나스닥 하락:** <span style='color:{ndx_c}'>{ndx_str}</span>", unsafe_allow_html=True)
    
    # 데이터 추출
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
            "수익률": j_val,
            "수익금": k_val,
            "하한선": lower_val,
            "상한선": upper_val,
            "excel_row": row_idx + 1,
            "is_total": row_idx == 23
        })
        
    df_disp = pd.DataFrame(data)

    # 색상 조건 설정
    def apply_styles(row):
        styles = [''] * len(row)
        is_total = row['is_total']
        excel_row = row['excel_row']
        
        if is_total:
            return ['background-color: #fff2cc; font-weight: bold; color: black;'] * len(row)
            
        bg_color, fg_color = "", ""
        if (6 <= excel_row <= 12) or (14 <= excel_row <= 22):
            try:
                curr = float(str(row['현재']).replace('%', '').strip())
                low_v = str(row['하한선'])
                up_v = str(row['상한선'])
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
            styles[2] = f'background-color: {bg_color}; color: {fg_color}; font-weight: bold;' 
            
        # 3(수익률), 4(수익금) 색상
        for i in [3, 4]:
            val = str(row.iloc[i])
            if val:
                if "-" in val:
                    styles[i] = 'color: #1a73e8;'
                elif val not in ["0", "0.00%", "0.0%"]:
                    styles[i] = 'color: #d93025;'
                    
        return styles

    # ==========================================================
    # 💡 [핵심] 가로 스크롤 없는 HTML 표로 렌더링 (st.dataframe 대신 사용)
    # ==========================================================
    # 1. 디자인 입히기 및 불필요한 열 숨기기
    styled_df = df_disp.style.apply(apply_styles, axis=1) \
                     .hide(["하한선", "상한선", "excel_row", "is_total"], axis=1) \
                     .hide(axis="index")

    # 2. HTML로 변환 후 모바일용 CSS 클래스(mobile-table) 연결
    html_table = styled_df.to_html(table_attributes='class="mobile-table"')
    st.markdown(html_table, unsafe_allow_html=True)

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
