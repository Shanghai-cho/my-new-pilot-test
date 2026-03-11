import streamlit as st
import pandas as pd
import requests
import io

# ==========================================================
# 💡 [설정] 구글 시트 URL
# ==========================================================
URL_HEESANG = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=368982410&single=true&output=csv"
URL_DASOL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSPgj2WLYMx6eeQTFt9ChqKL3NykgNUpxrjWrDxQCrPw98fLN9OnpfipptOyugxzmHWh9tZNOZViYhI/pub?gid=573600297&single=true&output=csv"

# 1. 페이지 설정
st.set_page_config(page_title="투자 대시보드", layout="centered", initial_sidebar_state="collapsed")

# ==========================================================
# 💡 [모바일 최적화 디자인] 가로 스크롤 방지 & 표 비율 고정
# ==========================================================
st.markdown("""
<style>
    .block-container {
        padding: 1.5rem 0.5rem 1rem 0.5rem !important;
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
    
    .mobile-table {
        width: 100%;
        table-layout: fixed; 
        border-collapse: collapse;
        font-size: 11px !important; 
        margin-top: 10px;
    }
    .mobile-table th {
        background-color: #f0f2f6;
        color: #333;
        text-align: center !important;
        padding: 6px 1px;
        border-bottom: 2px solid #ccc;
    }
    .mobile-table td {
        padding: 6px 1px;
        border-bottom: 1px solid #eee;
        text-align: right;
        white-space: nowrap; 
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .mobile-table th:nth-child(1), .mobile-table td:nth-child(1) { 
        width: 38%; 
        text-align: left !important; 
        white-space: normal !important; 
        word-break: keep-all; 
    }
    .mobile-table th:nth-child(2), .mobile-table td:nth-child(2) { width: 11%; text-align: center !important; }
    .mobile-table th:nth-child(3), .mobile-table td:nth-child(3) { width: 13%; text-align: center !important; }
    .mobile-table th:nth-child(4), .mobile-table td:nth-child(4) { width: 15%; }
    .mobile-table th:nth-child(5), .mobile-table td:nth-child(5) { width: 23%; }
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

# 3. 데이터 로딩 (캐시 60초)
@st.cache_data(ttl=60)
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
    # 💡 [핵심 해결] 구글 시트의 1번째 줄(C1, J1)과 2번째 줄(C2, J2)을 모두 스캔하여 확실하게 숫자를 낚아챕니다!
    # ==========================================================
    # 1. VIX 찾기 (C열 = 인덱스 2)
    vix = 0.0
    vix_str = "0"
    for r in [0, 1]:  # 파이썬 인덱스 0(첫 번째 줄), 1(두 번째 줄) 순차 확인
        try:
            temp = str(df_raw.iloc[r, 2]).replace(',', '').strip()
            if temp.lower() not in ["nan", "none", ""]:
                vix = float(temp)
                vix_str = temp
                break # 진짜 숫자를 찾으면 탐색 종료!
        except:
            pass

    # 2. 나스닥 하락률 찾기 (J열 = 인덱스 9)
    ndx = 0.0
    ndx_str = "0%"
    for r in [0, 1]:
        try:
            temp = str(df_raw.iloc[r, 9]).strip()
            if temp.lower() not in ["nan", "none", ""]:
                ndx = float(temp.replace('%', ''))
                ndx_str = temp
                break # 진짜 숫자를 찾으면 탐색 종료!
        except:
            pass

    # 시장 지표 색상 입히기
    vix_c = "#1e8e3e" if vix < 20 else "#b8860b" if vix < 30 else "#d95f02" if vix < 40 else "#8b0000"
    ndx_c = "#1e8e3e" if ndx > -20 else "#d4ac0d" if ndx > -30 else "#b8860b" if ndx > -40 else "#ff8c00" if ndx > -50 else "#d95f02" if ndx > -60 else "#ea4335" if ndx > -70 else "#8b0000"

    st.markdown(f"**VIX:** <span style='color:{vix_c}'>{vix_str}</span> &nbsp; | &nbsp; **나스닥 하락:** <span style='color:{ndx_c}'>{ndx_str}</span>", unsafe_allow_html=True)
    
    # 데이터 표 정리
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
            "종목": c_val,
            "목표": d_val,
            "현재": e_val,
            "수익%": j_val,
            "수익금": k_val,
            "하한선": lower_val,
            "상한선": upper_val,
            "excel_row": row_idx + 1,
            "is_total": row_idx == 23
        })
        
    df_disp = pd.DataFrame(data)

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
            except: pass
        
        if bg_color:
            styles[2] = f'background-color: {bg_color}; color: {fg_color}; font-weight: bold;' 
            
        for i in [3, 4]:
            val = str(row.iloc[i])
            if val:
                if "-" in val:
                    styles[i] = 'color: #1a73e8;'
                elif val not in ["0", "0.00%", "0.0%"]:
                    styles[i] = 'color: #d93025;'
                    
        return styles

    # HTML 테이블 변환 적용
    styled_df = df_disp.style.apply(apply_styles, axis=1) \
                     .hide(["하한선", "상한선", "excel_row", "is_total"], axis=1) \
                     .hide(axis="index")

    html_table = styled_df.to_html(table_attributes='class="mobile-table"')
    st.markdown(html_table, unsafe_allow_html=True)

except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
