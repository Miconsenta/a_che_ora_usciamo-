import re
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

FORMATO = "%H:%M"
MAX_LIMITE = "23:45"

# ---------- Helpers ----------
def round_pause_to_45_60_75(pausa_td: timedelta) -> timedelta:
    minuti = pausa_td.total_seconds() / 60.0
    if minuti <= 45:
        return timedelta(minutes=45)
    elif minuti <= 60:
        return timedelta(minutes=60)
    elif minuti <= 75:
        return timedelta(minutes=75)
    else:
        return timedelta(minutes=75)

_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")

def parse_hhmm(s: str) -> datetime:
    s = s.strip()
    if not _TIME_RE.match(s):
        raise ValueError(f"Orario non valido: '{s}'. Usa formato HH:MM (es. 09:03).")
    return datetime.strptime(s, FORMATO).replace(year=2000, month=1, day=1)

def minutes(td: timedelta) -> int:
    return int(td.total_seconds() // 60)

# ---------- UI ----------
st.set_page_config(page_title="A che ora usciamo", page_icon="🕒", layout="centered")

st.markdown(
    """
    <style>
      .block-container {max-width: 880px; padding-top: 2rem;}
      div[data-testid="stMetric"] {background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        padding: 14px 16px; border-radius: 14px;}
      .card {background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        padding: 18px 18px; border-radius: 16px;}
      .muted {opacity: .75; font-size: 0.95rem;}
      .tiny {opacity: .7; font-size: 0.85rem;}
      input[type="text"] {font-variant-numeric: tabular-nums;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🕒 Calcolo uscita teorica + slot straordinario")
st.caption(f"Limite superiore fisso: **{MAX_LIMITE}** (non modificabile).")

with st.sidebar:
    st.subheader("Parametri")
    ore_giornaliere = st.number_input("Ore giornaliere", min_value=0, max_value=24, value=7, step=1)
    minuti_giornali = st.number_input("Minuti giornalieri", min_value=0, max_value=59, value=36, step=1)
    st.markdown(f"<div class='tiny'>Limite slot: <b>{MAX_LIMITE}</b></div>", unsafe_allow_html=True)

st.markdown("<div class='card'>", unsafe_allow_html=True)
st.subheader("Orari (inserimento manuale)")

c1, c2, c3 = st.columns(3)
ingresso_str = c1.text_input("Ingresso (HH:MM)", value="09:00", placeholder="es. 09:03")
uscita_pranzo_str = c2.text_input("Uscita pranzo (HH:MM)", value="13:00", placeholder="es. 13:02")
rientro_pranzo_str = c3.text_input("Rientro pranzo (HH:MM)", value="14:00", placeholder="es. 14:01")

st.markdown("<div class='muted'>Suggerimento: puoi scrivere qualsiasi minuto (es. 09:03), non a step di 5.</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

st.write("")

if st.button("Calcola", type="primary", use_container_width=True):
    try:
        ingresso = parse_hhmm(ingresso_str)
        uscita_pranzo = parse_hhmm(uscita_pranzo_str)
        rientro_pranzo = parse_hhmm(rientro_pranzo_str)
        limite_superiore = parse_hhmm(MAX_LIMITE)

        pausa_effettiva = rientro_pranzo - uscita_pranzo
        if pausa_effettiva.total_seconds() < 0:
            raise ValueError("La pausa risulta negativa: verifica uscita/rientro pranzo.")

        pausa_normata = round_pause_to_45_60_75(pausa_effettiva)
        tempo_lavoro = timedelta(hours=int(ore_giornaliere), minutes=int(minuti_giornali))
        uscita_teorica = ingresso + tempo_lavoro + pausa_normata

        m1, m2, m3 = st.columns(3)
        m1.metric("Pausa effettiva", f"{minutes(pausa_effettiva)} min")
        m2.metric("Pausa considerata", f"{minutes(pausa_normata)} min")
        m3.metric("Uscita teorica", uscita_teorica.strftime(FORMATO))

        if uscita_teorica.hour >= 18:
            st.info('🫠  "Dura portarla a casa oggi eh??"')

        # slot ogni 15'
        incremento = timedelta(minutes=15)
        rows = []
        k = 1
        while True:
            corrente = uscita_teorica + incremento * k
            if corrente > limite_superiore:
                break
            rows.append(
                {
                    "Straordinario maturato": f"+{k*15} min",
                    "Orario": corrente.strftime(FORMATO),
                }
            )
            k += 1

        st.subheader("Slot ogni 15'")
        if not rows:
            st.write(f"Nessuno slot entro il limite delle {MAX_LIMITE}.")
        else:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Scarica CSV slot",
                data=csv,
                file_name="slot_straordinario.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except Exception as e:
        st.error(str(e))
