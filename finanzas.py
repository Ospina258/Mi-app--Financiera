"""
💰 Finzen — Gestor de Finanzas Personales
App completa con Streamlit + Plotly
"""
import streamlit as st
import json, os
from datetime import datetime, date
from collections import defaultdict
import pandas as pd
import plotly.express as px

ARCHIVO = "finanzas.json"

CATEGORIAS_GASTO = ["Alimentación", "Transporte", "Vivienda", "Servicios",
    "Salud", "Entretenimiento", "Educación", "Ropa", "Restaurantes",
    "Suscripciones", "Ahorro", "Otros"]
CATEGORIAS_INGRESO = ["Salario", "Freelance", "Inversiones", "Regalo", "Otros"]
CATEGORIAS_ESENCIALES = {"Vivienda", "Servicios", "Alimentación", "Transporte", "Salud", "Educación"}

# ==================== PERSISTENCIA ====================
def load_data():
    if os.path.exists(ARCHIVO):
        try:
            with open(ARCHIVO, "r", encoding="utf-8") as f:
                d = json.load(f)
                for k in ["transacciones", "metas", "prestamos"]:
                    d.setdefault(k, [])
                d.setdefault("presupuestos", {})
                d.setdefault("proximo_id", 1)
                d.setdefault("proximo_id_prestamo", 1)
                return d
        except Exception:
            pass
    return {"transacciones": [], "presupuestos": {}, "metas": [],
            "prestamos": [], "proximo_id": 1, "proximo_id_prestamo": 1}

def save_data(d):
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False, default=str)

def datos():
    if "datos" not in st.session_state:
        st.session_state.datos = load_data()
    return st.session_state.datos

def save():
    save_data(st.session_state.datos)

# ==================== HELPERS ====================
def fmt(n):  return f"${n:,.0f}"
def mes_actual(): return datetime.now().strftime("%Y-%m")

def dias_restantes_mes():
    hoy = date.today()
    prox = date(hoy.year + (hoy.month == 12), (hoy.month % 12) + 1, 1)
    return max((prox - hoy).days, 1)

def total_mes(d, periodo, tipo):
    return sum(t["monto"] for t in d["transacciones"]
               if t["tipo"] == tipo and t["fecha"].startswith(periodo))

def gasto_por_categoria(d, periodo):
    out = defaultdict(float)
    for t in d["transacciones"]:
        if t["tipo"] == "gasto" and t["fecha"].startswith(periodo):
            out[t["categoria"]] += t["monto"]
    return dict(out)

def gasto_hoy(d):
    hoy = date.today().strftime("%Y-%m-%d")
    return sum(t["monto"] for t in d["transacciones"]
               if t["tipo"] == "gasto" and t["fecha"] == hoy)

# ==================== PRESUPUESTO INTELIGENTE ====================
def calcular_presupuesto(d):
    """Calcula cuánto puedes gastar por día."""
    ing = total_mes(d, mes_actual(), "ingreso")
    gas = total_mes(d, mes_actual(), "gasto")

    comprometido = 0
    for cat, monto in d["presupuestos"].items():
        if cat in CATEGORIAS_ESENCIALES:
            gastado = sum(t["monto"] for t in d["transacciones"]
                          if t["tipo"] == "gasto" and t["categoria"] == cat
                          and t["fecha"].startswith(mes_actual()))
            comprometido += max(monto - gastado, 0)

    ahorro_obj = ing * 0.10

    deudas = sum(max(p["monto"] - p["pagado"], 0)
                 for p in d["prestamos"] if p["tipo"] == "debo")

    disponible = ing - gas - comprometido - ahorro_obj - deudas
    dias = dias_restantes_mes()

    return {
        "ingreso": ing, "gastado": gas, "comprometido": comprometido,
        "ahorro": ahorro_obj, "deudas": deudas,
        "disponible": disponible,
        "limite_diario": max(disponible / dias, 0),
        "dias_restantes": dias,
    }

# ==================== CONFIG ====================
st.set_page_config(page_title="Finzen", page_icon="💰",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .big-title {font-size: 2.3rem; font-weight: 700; color: #2E86AB; margin-bottom: 0;}
    .subtitle  {color: #888; font-size: 0.9rem; margin-top: 0;}
    .card {background: linear-gradient(135deg,#667eea,#764ba2); padding: 22px;
           border-radius: 14px; color: white; text-align: center;}
    .card h3 {margin: 0; font-size: 0.85rem; opacity: 0.9;}
    .card h1 {margin: 6px 0 0 0; font-size: 2rem;}
    div[data-testid="stMetricValue"] {font-size: 1.6rem;}
</style>
""", unsafe_allow_html=True)

d = datos()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 💰 Finzen")
    st.caption("Tu dinero, bajo control")
    st.divider()
    seccion = st.radio("Nav", [
        "📊 Dashboard",
        "💸 Registrar",
        "🎯 Presupuesto inteligente",
        "📈 Presupuestos",
        "🏦 Metas de ahorro",
        "🤝 Préstamos",
        "📋 Historial",
        "💡 Consejos",
    ], label_visibility="collapsed")
    st.divider()
    st.caption(f"📅 {date.today().strftime('%d/%m/%Y')}")

# ==================== 📊 DASHBOARD ====================
if seccion == "📊 Dashboard":
    st.markdown('<p class="big-title">📊 Dashboard</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Vista general de tus finanzas</p>', unsafe_allow_html=True)

    info = calcular_presupuesto(d)
    hoy_gastado = gasto_hoy(d)

    limite = info["limite_diario"]
    if limite == 0:
        estado, color = "❌ Sin presupuesto disponible", "#e74c3c"
    elif hoy_gastado >= limite:
        estado, color = "🚨 Ya superaste tu límite de hoy", "#e74c3c"
    elif hoy_gastado >= limite * 0.8:
        estado, color = "⚠️ Estás cerca del límite de hoy", "#f39c12"
    else:
        estado, color = "✅ Puedes seguir gastando hoy", "#27ae60"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg,{color}22,{color}44);
                padding: 22px; border-radius: 14px; border-left: 6px solid {color};
                margin-bottom: 18px;">
        <div style="font-size: 0.9rem; color: #555;">💡 Límite de gasto para HOY</div>
        <div style="font-size: 2.6rem; font-weight: 800; color: {color};">
            {fmt(limite)}
        </div>
        <div style="color: #333; font-size: 0.95rem;">
            Ya gastaste hoy: <b>{fmt(hoy_gastado)}</b> · {estado}
        </div>
        <div style="color: #666; font-size: 0.8rem; margin-top: 4px;">
            Quedan {info['dias_restantes']} días del mes · Disponible: {fmt(info['disponible'])}
        </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ingresos del mes", fmt(info["ingreso"]))
    c2.metric("Gastos del mes", fmt(info["gastado"]))
    bal = info["ingreso"] - info["gastado"]
    c3.metric("Balance", fmt(bal), delta=f"{(bal/info['ingreso']*100) if info['ingreso'] else 0:.0f}%")
    c4.metric("Ahorro sugerido", fmt(info["ahorro"]))

    st.divider()

    colA, colB = st.columns([2, 1])
    with colA:
        st.subheader("📊 Gastos por categoría")
        cats = gasto_por_categoria(d, mes_actual())
        if cats:
            df = pd.DataFrame(list(cats.items()), columns=["Categoría", "Monto"])
            fig = px.pie(df, values="Monto", names="Categoría", hole=0.45,
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_traces(textinfo="percent+label", textposition="inside")
            fig.update_layout(height=380, showlegend=False,
                              margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin gastos este mes aún.")

    with colB:
        st.subheader("🎯 Metas activas")
        if d["metas"]:
            for m in d["metas"][:3]:
                pct = min((m["ahorrado"] / m["objetivo"] * 100) if m["objetivo"] else 0, 100)
                st.markdown(f"**{m['nombre']}**")
                st.progress(pct / 100, text=f"{fmt(m['ahorrado'])} / {fmt(m['objetivo'])} ({pct:.0f}%)")
        else:
            st.caption("Sin metas todavía.")

        st.subheader("🤝 Préstamos")
        me_deben = sum(max(p["monto"] - p["pagado"], 0) for p in d["prestamos"] if p["tipo"] == "prestado")
        debo = sum(max(p["monto"] - p["pagado"], 0) for p in d["prestamos"] if p["tipo"] == "debo")
        st.metric("💚 Me deben", fmt(me_deben))
        st.metric("❤️ Yo debo", fmt(debo))

# ==================== 💸 REGISTRAR ====================
elif seccion == "💸 Registrar":
    st.markdown('<p class="big-title">💸 Registrar movimiento</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Ingreso", "➖ Gasto"])

    with tab1:
        with st.form("form_ingreso", clear_on_submit=True):
            c1, c2 = st.columns(2)
            monto = c1.number_input("Monto ($)", min_value=0.01, step=100.0)
            cat = c2.selectbox("Categoría", CATEGORIAS_INGRESO)
            desc = st.text_input("Descripción (opcional)")
            fecha = st.date_input("Fecha", value=date.today())
            if st.form_submit_button("✅ Registrar ingreso", use_container_width=True):
                d["transacciones"].append({
                    "id": d["proximo_id"], "tipo": "ingreso", "monto": round(monto, 2),
                    "categoria": cat, "descripcion": desc,
                    "fecha": fecha.strftime("%Y-%m-%d")})
                d["proximo_id"] += 1
                save()
                st.toast(f"✅ Ingreso de {fmt(monto)} registrado")
                st.rerun()

    with tab2:
        with st.form("form_gasto", clear_on_submit=True):
            c1, c2 = st.columns(2)
            monto = c1.number_input("Monto ($)", min_value=0.01, step=10.0)
            cat = c2.selectbox("Categoría", CATEGORIAS_GASTO)
            desc = st.text_input("Descripción (opcional)")
            fecha = st.date_input("Fecha", value=date.today())

            if cat in d["presupuestos"]:
                gastado_cat = sum(t["monto"] for t in d["transacciones"]
                                  if t["tipo"] == "gasto" and t["categoria"] == cat
                                  and t["fecha"].startswith(mes_actual()))
                restante = d["presupuestos"][cat] - gastado_cat
                st.caption(f"📊 Presupuesto {cat}: {fmt(gastado_cat)} / {fmt(d['presupuestos'][cat])} "
                           f"· Te quedan {fmt(max(restante, 0))}")

            if st.form_submit_button("✅ Registrar gasto", use_container_width=True):
                d["transacciones"].append({
                    "id": d["proximo_id"], "tipo": "gasto", "monto": round(monto, 2),
                    "categoria": cat, "descripcion": desc,
                    "fecha": fecha.strftime("%Y-%m-%d")})
                d["proximo_id"] += 1
                save()

                if cat in d["presupuestos"]:
                    gastado_cat = sum(t["monto"] for t in d["transacciones"]
                                      if t["tipo"] == "gasto" and t["categoria"] == cat
                                      and t["fecha"].startswith(mes_actual()))
                    pct = gastado_cat / d["presupuestos"][cat] * 100
                    if pct >= 100:
                        st.toast(f"🚨 ¡Superaste el presupuesto de {cat}!", icon="🚨")
                    elif pct >= 80:
                        st.toast(f"⚠️ Llevas {pct:.0f}% en {cat}", icon="⚠️")
                    else:
                        st.toast(f"✅ Gasto de {fmt(monto)} registrado")
                else:
                    st.toast(f"✅ Gasto de {fmt(monto)} registrado")
                st.rerun()

# ==================== 🎯 PRESUPUESTO INTELIGENTE ====================
elif seccion == "🎯 Presupuesto inteligente":
    st.markdown('<p class="big-title">🎯 Presupuesto inteligente</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Así se calcula cuánto puedes gastar y cuánto NO</p>',
                unsafe_allow_html=True)

    info = calcular_presupuesto(d)

    st.markdown("### 🧮 Desglose del cálculo")
    desglose = pd.DataFrame([
        {"Concepto": "➕ Ingreso total del mes", "Monto": info["ingreso"], "Tipo": "positivo"},
        {"Concepto": "➖ Ya gastado", "Monto": -info["gastado"], "Tipo": "negativo"},
        {"Concepto": "🔒 Comprometido (fijos pendientes)", "Monto": -info["comprometido"], "Tipo": "neutro"},
        {"Concepto": "🎯 Ahorro objetivo (10%)", "Monto": -info["ahorro"], "Tipo": "neutro"},
        {"Concepto": "🤝 Deudas pendientes", "Monto": -info["deudas"], "Tipo": "negativo"},
        {"Concepto": "💰 DISPONIBLE LIBRE", "Monto": info["disponible"], "Tipo": "positivo"},
    ])
    st.dataframe(desglose, use_container_width=True, hide_index=True)

    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("📅 Días restantes", info["dias_restantes"])
    col2.metric("💵 Disponible total", fmt(info["disponible"]))
    col3.metric("🎯 Límite por día", fmt(info["limite_diario"]))

    st.markdown(f"""
    <div style="background:#e8f5e9; padding: 20px; border-radius: 12px;
                border-left: 6px solid #27ae60; margin-top: 15px;">
        <h3 style="margin:0; color:#27ae60;">💡 Regla de oro para este mes</h3>
        <p style="font-size: 1.1rem; margin-top: 10px;">
        Puedes gastar hasta <b style="font-size:1.6rem; color:#27ae60;">{fmt(info['limite_diario'])}</b> por día.<br>
        Si gastas más, sacrificarás ahorro o tendrás que endeudarte.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("🚨 Estado de hoy")
    hoy = gasto_hoy(d)
    limite = info["limite_diario"]
    if limite > 0:
        pct_hoy = min(hoy / limite * 100, 200)
        st.progress(min(pct_hoy / 100, 1.0), text=f"{fmt(hoy)} de {fmt(limite)} ({pct_hoy:.0f}%)")
        if hoy > limite:
            st.error(f"🚨 Superaste el límite diario por {fmt(hoy - limite)}")
        elif hoy > limite * 0.8:
            st.warning(f"⚠️ Cerca del límite: te quedan {fmt(limite - hoy)}")
        else:
            st.success(f"✅ Bien: puedes gastar {fmt(limite - hoy)} más hoy")
    else:
        st.error("❌ No tienes margen de gasto hoy. Revisa tus gastos o ingresos.")

# ==================== 📈 PRESUPUESTOS ====================
elif seccion == "📈 Presupuestos":
    st.markdown('<p class="big-title">📈 Presupuestos por categoría</p>', unsafe_allow_html=True)

    with st.expander("➕ Definir / actualizar presupuesto", expanded=not d["presupuestos"]):
        with st.form("form_presupuesto", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cat = c1.selectbox("Categoría", CATEGORIAS_GASTO)
            monto = c2.number_input("Límite mensual ($)", min_value=1.0, step=100.0)
            if st.form_submit_button("Guardar presupuesto", use_container_width=True):
                d["presupuestos"][cat] = round(monto, 2)
                save()
                st.toast(f"✅ Presupuesto {cat} guardado")
                st.rerun()

    st.divider()

    if not d["presupuestos"]:
        st.info("Aún no hay presupuestos. Define los más importantes (Vivienda, Alimentación, Transporte...).")
    else:
        st.subheader("Estado del mes")
        for cat, monto in sorted(d["presupuestos"].items()):
            gastado = sum(t["monto"] for t in d["transacciones"]
                          if t["tipo"] == "gasto" and t["categoria"] == cat
                          and t["fecha"].startswith(mes_actual()))
            pct = min(gastado / monto * 100 if monto else 0, 100)
            col1, col2 = st.columns([4, 1])
            with col1:
                label = f"**{cat}** — {fmt(gastado)} / {fmt(monto)}"
                st.progress(pct / 100, text=label)
            with col2:
                if pct >= 100:
                    st.error(f"{pct:.0f}%")
                elif pct >= 80:
                    st.warning(f"{pct:.0f}%")
                else:
                    st.success(f"{pct:.0f}%")
                if st.button("🗑️", key=f"del_{cat}"):
                    del d["presupuestos"][cat]
                    save()
                    st.rerun()

# ==================== 🏦 METAS ====================
elif seccion == "🏦 Metas de ahorro":
    st.markdown('<p class="big-title">🏦 Metas de ahorro</p>', unsafe_allow_html=True)

    with st.expander("➕ Nueva meta"):
        with st.form("form_meta", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre", placeholder="Fondo de emergencia")
            objetivo = c2.number_input("Objetivo ($)", min_value=1.0, step=100.0)
            if st.form_submit_button("Crear meta", use_container_width=True) and nombre:
                d["metas"].append({"nombre": nombre, "objetivo": round(objetivo, 2), "ahorrado": 0})
                save()
                st.toast(f"✅ Meta '{nombre}' creada")
                st.rerun()

    if not d["metas"]:
        st.info("Sin metas. Crea una para empezar a ahorrar con propósito 💪")
    else:
        for i, m in enumerate(d["metas"]):
            pct = min((m["ahorrado"] / m["objetivo"] * 100) if m["objetivo"] else 0, 100)
            faltante = max(m["objetivo"] - m["ahorrado"], 0)

            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(m["nombre"])
                    st.progress(pct / 100, text=f"{fmt(m['ahorrado'])} / {fmt(m['objetivo'])} ({pct:.0f}%)")
                    if faltante > 0:
                        st.caption(f"Faltan {fmt(faltante)}")
                    else:
                        st.success("🎉 ¡Meta cumplida!")
                with col2:
                    abono = st.number_input("Abonar $", min_value=0.0, step=50.0,
                                            key=f"abono_{i}")
                    if st.button("💰 Abonar", key=f"btn_{i}", use_container_width=True) and abono > 0:
                        m["ahorrado"] += abono
                        save()
                        st.toast(f"✅ {fmt(abono)} abonado a '{m['nombre']}'")
                        st.rerun()
                    if st.button("🗑️ Eliminar", key=f"delm_{i}", use_container_width=True):
                        d["metas"].pop(i)
                        save()
                        st.rerun()

# ==================== 🤝 PRÉSTAMOS ====================
elif seccion == "🤝 Préstamos":
    st.markdown('<p class="big-title">🤝 Préstamos</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Controla quién te debe y a quién le debes</p>',
                unsafe_allow_html=True)

    me_deben = sum(max(p["monto"] - p["pagado"], 0) for p in d["prestamos"] if p["tipo"] == "prestado")
    debo = sum(max(p["monto"] - p["pagado"], 0) for p in d["prestamos"] if p["tipo"] == "debo")

    c1, c2 = st.columns(2)
    c1.metric("💚 Me deben", fmt(me_deben))
    c2.metric("❤️ Yo debo", fmt(debo))

    st.divider()

    tab1, tab2 = st.tabs(["💚 Me deben (presté)", "❤️ Yo debo (me prestaron)"])

    def render_prestamos(tipo, titulo):
        st.subheader(titulo)
        with st.expander("➕ Nuevo préstamo"):
            with st.form(f"form_{tipo}", clear_on_submit=True):
                c1, c2 = st.columns(2)
                persona = c1.text_input("Persona")
                monto = c2.number_input("Monto ($)", min_value=1.0, step=50.0)
                desc = st.text_input("Motivo (opcional)")
                fecha = st.date_input("Fecha", value=date.today())
                if st.form_submit_button("Registrar", use_container_width=True) and persona:
                    d["prestamos"].append({
                        "id": d["proximo_id_prestamo"], "tipo": tipo,
                        "persona": persona, "monto": round(monto, 2),
                        "pagado": 0, "descripcion": desc,
                        "fecha": fecha.strftime("%Y-%m-%d"), "pagos": []})
                    d["proximo_id_prestamo"] += 1
                    save()
                    st.toast(f"✅ Préstamo registrado con {persona}")
                    st.rerun()

        activos = [p for p in d["prestamos"] if p["tipo"] == tipo and p["pagado"] < p["monto"]]
        if not activos:
            st.info("Sin préstamos pendientes.")
        else:
            for p in activos:
                pendiente = p["monto"] - p["pagado"]
                pct = p["pagado"] / p["monto"] * 100 if p["monto"] else 0

                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{p['persona']}** — {p['descripcion'] or 'Sin motivo'}")
                        st.caption(f"Fecha: {p['fecha']}")
                        st.progress(pct / 100, text=f"Pagado {fmt(p['pagado'])} / {fmt(p['monto'])} ({pct:.0f}%)")
                        st.markdown(f"Pendiente: **{fmt(pendiente)}**")
                        if p["pagos"]:
                            with st.expander(f"📜 Ver {len(p['pagos'])} pago(s)"):
                                for pg in p["pagos"]:
                                    st.caption(f"{pg['fecha']}: {fmt(pg['monto'])}")
                    with col2:
                        monto_pago = st.number_input("Pago $", min_value=0.0, step=20.0,
                                                     key=f"pp_{p['id']}")
                        if st.button("💸 Registrar pago", key=f"pb_{p['id']}",
                                     use_container_width=True) and monto_pago > 0:
                            real = min(monto_pago, pendiente)
                            p["pagado"] += real
                            p["pagos"].append({"fecha": date.today().strftime("%Y-%m-%d"),
                                               "monto": real})
                            save()
                            st.toast(f"✅ {fmt(real)} registrado")
                            st.rerun()
                        if st.button("🗑️", key=f"pd_{p['id']}", use_container_width=True):
                            d["prestamos"].remove(p)
                            save()
                            st.rerun()

    with tab1:
        render_prestamos("prestado", "💚 Préstamos que di")
    with tab2:
        render_prestamos("debo", "❤️ Préstamos que recibí")

# ==================== 📋 HISTORIAL ====================
elif seccion == "📋 Historial":
    st.markdown('<p class="big-title">📋 Historial</p>', unsafe_allow_html=True)

    if not d["transacciones"]:
        st.info("Sin movimientos registrados todavía.")
    else:
        filtro = st.selectbox("Filtrar", ["Todos", "Solo ingresos", "Solo gastos"])
        txs = d["transacciones"]
        if filtro == "Solo ingresos":
            txs = [t for t in txs if t["tipo"] == "ingreso"]
        elif filtro == "Solo gastos":
            txs = [t for t in txs if t["tipo"] == "gasto"]

        if txs:
            df = pd.DataFrame(txs)
            df["fecha"] = pd.to_datetime(df["fecha"])
            df = df.sort_values("fecha", ascending=False)
            df["Monto"] = df.apply(lambda r: f"+{fmt(r['monto'])}" if r["tipo"] == "ingreso"
                                    else f"-{fmt(r['monto'])}", axis=1)
            df = df[["fecha", "tipo", "categoria", "descripcion", "Monto"]]
            df.columns = ["Fecha", "Tipo", "Categoría", "Descripción", "Monto"]
            df["Fecha"] = df["Fecha"].dt.strftime("%Y-%m-%d")
            st.dataframe(df, use_container_width=True, hide_index=True,
                         height=min(400, 40 * len(df) + 40))

            with st.expander("🗑️ Eliminar movimiento"):
                tid = st.number_input("ID a eliminar", min_value=1, step=1)
                if st.button("Eliminar"):
                    d["transacciones"] = [t for t in d["transacciones"] if t["id"] != tid]
                    save()
                    st.toast("✅ Eliminado")
                    st.rerun()

# ==================== 💡 CONSEJOS ====================
elif seccion == "💡 Consejos":
    st.markdown('<p class="big-title">💡 Consejos personalizados</p>', unsafe_allow_html=True)

    info = calcular_presupuesto(d)
    cats = gasto_por_categoria(d, mes_actual())

    if info["gastado"] == 0:
        st.info("Registra algunos gastos para recibir consejos personalizados.")
    else:
        if info["ingreso"] > 0 and info["gastado"] > info["ingreso"]:
            st.error(f"🚨 Estás gastando {fmt(info['gastado'] - info['ingreso'])} MÁS de lo que ingresas.")

        st.subheader("📐 Regla 50/30/20")
        if info["ingreso"] > 0:
            c1, c2, c3 = st.columns(3)
            c1.metric("🏠 Necesidades (50%)", fmt(info["ingreso"] * 0.5),
                     help="Vivienda, comida, transporte, servicios")
            c2.metric("🎉 Gustos (30%)", fmt(info["ingreso"] * 0.3),
                     help="Restaurantes, entretenimiento, ropa")
            c3.metric("💰 Ahorro (20%)", fmt(info["ingreso"] * 0.2),
                     help="Metas, fondo de emergencia, inversión")

        if cats:
            st.subheader("🎯 Tu mayor gasto")
            top, monto = max(cats.items(), key=lambda x: x[1])
            pct = monto / info["gastado"] * 100
            st.warning(f"**{top}** representa el **{pct:.0f}%** de tus gastos ({fmt(monto)}).\n\n"
                      f"💡 Si lo reduces un 20%, ahorrarías **{fmt(monto * 0.2)}/mes** "
                      f"({fmt(monto * 0.2 * 12)}/año).")

        if "Suscripciones" in cats:
            st.info(f"🔍 Revisa tus suscripciones ({fmt(cats['Suscripciones'])}/mes). "
                   "¿Realmente usas todas?")

        st.subheader("📈 Proyección fin de mes")
        hoy = date.today()
        dias_transcurridos = hoy.day
        promedio_diario = info["gastado"] / max(dias_transcurridos, 1)
        proyeccion = promedio_diario * 30
        st.markdown(f"Al ritmo actual (**{fmt(promedio_diario)}/día**) terminarás el mes "
                   f"gastando **{fmt(proyeccion)}**.")
        if info["ingreso"] > 0 and proyeccion > info["ingreso"]:
            st.error(f"🚨 Proyectas gastar {fmt(proyeccion - info['ingreso'])} más que tu ingreso.")
        elif info["ingreso"] > 0:
            st.success(f"✅ Vas bien: ahorrarías {fmt(info['ingreso'] - proyeccion)} este mes.")

        st.subheader("✅ Recomendaciones")
        faltan = [c for c in CATEGORIAS_GASTO[:8] if c not in d["presupuestos"] and c in cats]
        if faltan:
            st.write(f"📊 Define presupuesto para: **{', '.join(faltan[:4])}**")
        if not d["metas"]:
            st.write("🎯 Crea una meta de ahorro (ej: fondo de emergencia de 3 meses de gastos).")
        if info["limite_diario"] > 0 and gasto_hoy(d) > info["limite_diario"]:
            st.write(f"⚠️ Hoy ya superaste tu límite ({fmt(info['limite_diario'])}). "
                    "Intenta no gastar más hasta mañana.")
