import streamlit as st
import matplotlib.pyplot as plt
from core.inference import create_inference_engine
from core.solutions import get_solution_guide

def draw_variable(variable, input_value=None, title=""):
    fig, ax = plt.subplots(figsize=(6, 2.5))
    x = variable.universe
    for label in variable.terms:
        y = variable[label].mf
        ax.plot(x, y, label=label, linewidth=1.5)
        ax.fill_between(x, y, alpha=0.1)
    if input_value is not None:
        ax.vlines(input_value, 0, 1, colors='r', linestyles='dashed', label='Input')
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(True, alpha=0.3)
    return fig

@st.cache_resource
def load_engine():
    return create_inference_engine()

simulation, all_vars = load_engine()
inputs_dict = all_vars['inputs']

st.set_page_config(page_title="ГІС Експерт", layout="wide")
st.title("🖨️ ГІС Діагностики (Full Coverage)")

# --- САЙДБАР ---
st.sidebar.header("Вхідні дані")
device_type = st.sidebar.radio("Пристрій:", ["Принтер", "Сканер"], horizontal=True)

# ПРЕСЕТИ (ІДЕАЛЬНО ВИВІРЕНІ ЧИСЛА)
if device_type == "Принтер":
    presets = {
        "--- Оберіть ситуацію ---": None,
        # Queue Full (49) + Time Timeout (115) -> Spooler Critical
        "1. ЧЕРГА ВИСИТЬ (Critical Spooler)": {"time": 115, "queue": 49, "qual": 10, "conn": 100},
        
        # Time Instant (2) + Quality Terrible (1) -> Driver Critical
        "2. ІЄРОГЛІФИ (Critical Driver)": {"time": 2, "queue": 0, "qual": 1, "conn": 100},
        
        # Quality Perfect (10) + Time Slow (90) -> Network High
        "3. МЕРЕЖА ЛАГАЄ (High Network)": {"time": 90, "queue": 5, "qual": 10, "conn": 100},
        
        # Quality Bad (4) + Queue Empty (0) -> Hardware High
        "4. БЛІДИЙ ДРУК (High Hardware)": {"time": 20, "queue": 0, "qual": 4, "conn": 100},
        
        # All Good
        "5. ВСЕ ІДЕАЛЬНО": {"time": 5, "queue": 2, "qual": 10, "conn": 100}
    }
else:
    presets = {
        "--- Оберіть ситуацію ---": None,
        "1. РОЗРИВ КАБЕЛЮ (Critical Cable)": {"time": 60, "conn": 0},
        "2. ЗАВИС ДРАЙВЕР (Critical TWAIN)": {"time": 115, "conn": 100}, # Stable (100) + Timeout (115)
        "3. ПЕРЕШКОДИ (Medium Cable)": {"time": 80, "conn": 50},
        "4. ВСЕ ДОБРЕ": {"time": 5, "conn": 100}
    }

complaint = st.sidebar.selectbox("Швидкий вибір:", list(presets.keys()))
if presets[complaint]:
    vals = presets[complaint]
    st.session_state.time = vals.get("time", 0)
    st.session_state.queue = vals.get("queue", 0)
    st.session_state.qual = vals.get("qual", 10)
    st.session_state.conn = vals.get("conn", 100)
elif 'time' not in st.session_state:
    st.session_state.time = 5
    st.session_state.queue = 0
    st.session_state.qual = 10
    st.session_state.conn = 100

st.sidebar.markdown("---")
val_time = st.sidebar.slider("Час (сек)", 0, 120, st.session_state.time)

if device_type == "Принтер":
    val_queue = st.sidebar.slider("Черга (шт)", 0, 50, st.session_state.queue)
    val_qual = st.sidebar.slider("Якість (0-10)", 0, 10, st.session_state.qual)
    val_conn = 100
else:
    val_conn = st.sidebar.slider("Зв'язок (%)", 0, 100, st.session_state.conn)
    val_queue, val_qual = 0, 10

if st.button("🚀 ЗАПУСТИТИ ДІАГНОСТИКУ", type="primary"):
    try:
        # 1. Transfer of real data
        simulation.input['time'] = val_time
        
        # 2. "Stub" for inactive device
        # To prevent scikit-fuzzy from crashing due to missing rules for the inactive part
        if device_type == "Принтер":
            # Printer data
            simulation.input['queue'] = val_queue
            simulation.input['quality'] = val_qual
            # Stub for scanner (Ideal) -> so that risk_twain is not empty
            simulation.input['connection'] = 100 
        else:
            # Scanner data
            simulation.input['connection'] = val_conn
            # Printer stub -> so that risk_network is not empty
            simulation.input['queue'] = 0
            simulation.input['quality'] = 10 

        simulation.compute()
        
        res = {
            "Spooler": simulation.output['risk_spooler'],
            "Network": simulation.output['risk_network'],
            "Driver": simulation.output['risk_driver'],
            "Hardware": simulation.output['risk_hardware'],
            "TWAIN": simulation.output['risk_twain'],
            "Cable": simulation.output['risk_cable']
        }

        # Фільтр
        relevant_keys = ["Spooler", "Network", "Driver", "Hardware"] if device_type == "Принтер" else ["TWAIN", "Cable"]
        relevant_res = {k: v for k, v in res.items() if k in relevant_keys}

        max_risk = max(relevant_res.values())
        max_cause = max(relevant_res, key=relevant_res.get)

        c1, c2 = st.columns([1, 2])
        with c1:
            st.write("### Ризики:")
            for k, v in relevant_res.items():
                color = "normal"
                if v > 75: color = "off"
                elif v > 40: color = "inverse"
                st.metric(k, f"{v:.1f}%", delta_color=color)
        
        with c2:
            st.write("### Висновок:")
            if max_risk < 35:
                st.success(f"✅ **Норма.** (Макс: {max_risk:.1f}%)")
            else:
                st.error(f"🚨 **{max_cause}** ({max_risk:.1f}%)")
                instruction = get_solution_guide(max_cause)
                with st.expander("🛠️ **Інструкція**", expanded=True):
                    st.markdown(instruction)

        st.write("---")
        cols = st.columns(3)
        with cols[0]: st.pyplot(draw_variable(inputs_dict['time'], val_time, "Час"))
        if device_type == "Принтер":
            with cols[1]: st.pyplot(draw_variable(inputs_dict['queue'], val_queue, "Черга"))
            with cols[2]: st.pyplot(draw_variable(inputs_dict['quality'], val_qual, "Якість"))
        else:
            with cols[1]: st.pyplot(draw_variable(inputs_dict['connection'], val_conn, "Зв'язок"))
    except Exception as e:
        st.error(f"Помилка розрахунку: {e}. Спробуйте змінити вхідні дані.")