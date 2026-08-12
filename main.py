import streamlit as st
import pandas as pd

st.set_page_config(page_title="Formulario de Plantilla", layout="wide")

st.title("📋 Formulario de Configuración de Sesión")
st.write("Complete la información necesaria para rellenar la plantilla del documento.")

# --- SESSION STATE INITIALIZATION ---
if "tema_count" not in st.session_state:
    st.session_state.tema_count = 1

# Store detailed data for each topic sub-form dynamically
if "temas_details" not in st.session_state:
    st.session_state.temas_details = {}

# Ensure we keep structure for current number of themes
def adjust_temas_state():
    for i in range(1, st.session_state.tema_count + 1):
        if i not in st.session_state.temas_details:
            st.session_state.temas_details[i] = {
                "titulo": "",
                "inicio": "",
                "subtemas": [{"subtema": "", "resumen": ""}],  # Starts with 1 row
                "cierre": "¿Qué aprendimos?, ¿Cómo lo aprendimos?",
                "tarea": ""
            }

adjust_temas_state()

# --- GROUP 1: Datos generales ---
st.header("🏛️ 1. Datos Generales")
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        colegio = st.text_input("Colegio", value="I.E.P. Tradiciones Ricardo Palma")
        area = st.selectbox("Área", options=["Historia", "Geografía", "Economía"])
        nivel = st.selectbox("Nivel", options=["Primaria", "Secundaria"])
        grado = st.selectbox("Grado", options=["1º", "2º", "3º", "4º", "5º", "6º"])
    with col2:
        seccion = st.text_input("Sección", value="Única")
        docente = st.text_input("Docente", value="Mary Y. Gamez Montesinos")
        mes = st.selectbox("Mes", options=[
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ])

# --- GROUP 2: Propósito de la sesión ---
st.header("🎯 2. Propósito de la Sesión")
with st.container(border=True):
    if "rows_proposito" not in st.session_state:
        st.session_state.rows_proposito = [{"competencias": "", "capacidades": "", "desempenos": ""}]

    action_col1, action_col2, _ = st.columns([1.5, 1.5, 7])
    with action_col1:
        if st.button("➕ Añadir Fila", key="add_row_prop"):
            st.session_state.rows_proposito.append({"competencias": "", "capacidades": "", "desempenos": ""})
            st.rerun()
    with action_col2:
        if st.button("🗑️ Eliminar Última", key="del_row_prop") and len(st.session_state.rows_proposito) > 1:
            st.session_state.rows_proposito.pop()
            st.rerun()

    st.write("---")
    header_col1, header_col2, header_col3 = st.columns([2, 4, 4])
    header_col1.markdown("**Competencias**")
    header_col2.markdown("**Capacidades**")
    header_col3.markdown("**Desempeños**")

    for idx, row in enumerate(st.session_state.rows_proposito):
        col1, col2, col3 = st.columns([2, 4, 4])
        with col1:
            st.session_state.rows_proposito[idx]["competencias"] = st.text_area("C", value=row["competencias"], label_visibility="collapsed", key=f"comp_{idx}", height=80)
        with col2:
            st.session_state.rows_proposito[idx]["capacidades"] = st.text_area("Ca", value=row["capacidades"], label_visibility="collapsed", key=f"cap_{idx}", height=80)
        with col3:
            st.session_state.rows_proposito[idx]["desempenos"] = st.text_area("D", value=row["desempenos"], label_visibility="collapsed", key=f"des_{idx}", height=80)

# --- GROUP 3: Enfoque Transversal ---
st.header("🌍 3. Enfoque Transversal")
with st.container(border=True):
    enfoque_inicial = pd.DataFrame([
        {"ENFOQUES TRANSVERSALES": "Enfoque ambiental", "ACCIONES OBSERVABLES": ""},
        {"ENFOQUES TRANSVERSALES": "Enfoque de derechos", "ACCIONES OBSERVABLES": ""},
        {"ENFOQUES TRANSVERSALES": "VALOR", "ACCIONES OBSERVABLES": ""}
    ])
    edited_enfoque = st.data_editor(enfoque_inicial, num_rows="fixed", use_container_width=True, column_config={
        "ENFOQUES TRANSVERSALES": st.column_config.TextColumn("ENFOQUES TRANSVERSALES", disabled=True),
        "ACCIONES OBSERVABLES": st.column_config.TextColumn("ACCIONES OBSERVABLES")
    }, key="enfoque_editor")

# --- GROUP 4: Temas ---
st.header("📚 4. Configuración de Temas")
with st.container(border=True):
    # Buttons to control topic addition/removal
    btn_col1, btn_col2, _ = st.columns([1.5, 1.5, 7])
    with btn_col1:
        if st.button("➕ Añadir Tema", key="add_tema_global"):
            st.session_state.tema_count += 1
            adjust_temas_state()
            st.rerun()
    with btn_col2:
        if st.button("🗑️ Eliminar Último Tema", key="del_tema_global") and st.session_state.tema_count > 1:
            st.session_state.temas_details.pop(st.session_state.tema_count, None)
            st.session_state.tema_count -= 1
            st.rerun()
            
    st.write("---")
    
    # Generate form sections dynamically for each topic using st.expander
    for i in range(1, st.session_state.tema_count + 1):
        tema_data = st.session_state.temas_details[i]
        
        # Display dynamic topic label. Changes if user inputs a specific title
        expander_title = f"📘 Tema {i}: {tema_data['titulo'] if tema_data['titulo'] else '(Por definir)'}"
        
        with st.expander(expander_title, expanded=(i == st.session_state.tema_count)):
            # 1. Main Topic Title Input
            st.session_state.temas_details[i]["titulo"] = st.text_input(
                f"Nombre del Tema {i}", 
                value=tema_data["titulo"], 
                key=f"titulo_tema_input_{i}"
            )
            
            # 2. Inicio Text Area
            st.session_state.temas_details[i]["inicio"] = st.text_area(
                "Inicio", 
                value=tema_data["inicio"], 
                placeholder="El campo está vacío. Describa las actividades iniciales aquí...", 
                key=f"inicio_tema_{i}",
                height=100
            )
            
            # 3. Dynamic Sub-Table (Subtema y Resumen)
            st.write("**Estructura de Contenidos (Subtemas):**")
            sub_btn1, sub_btn2, _ = st.columns([2, 2, 6])
            with sub_btn1:
                if st.button(f"➕ Añadir Subtema", key=f"add_sub_{i}"):
                    st.session_state.temas_details[i]["subtemas"].append({"subtema": "", "resumen": ""})
                    st.rerun()
            with sub_btn2:
                if st.button(f"🗑️ Eliminar Último Subtema", key=f"del_sub_{i}") and len(tema_data["subtemas"]) > 1:
                    st.session_state.temas_details[i]["subtemas"].pop()
                    st.rerun()
                    
            # Headers for the Sub-table grid
            sub_h1, sub_h2 = st.columns([4, 6])
            sub_h1.caption("**Subtema**")
            sub_h2.caption("**Resumen (Soporta viñetas)**")
            
            for s_idx, s_row in enumerate(tema_data["subtemas"]):
                scol1, scol2 = st.columns([4, 6])
                with scol1:
                    st.session_state.temas_details[i]["subtemas"][s_idx]["subtema"] = st.text_area(
                        "S", value=s_row["subtema"], label_visibility="collapsed", key=f"sub_txt_{i}_{s_idx}", height=70
                    )
                with scol2:
                    st.session_state.temas_details[i]["subtemas"][s_idx]["resumen"] = st.text_area(
                        "R", value=s_row["resumen"], label_visibility="collapsed", key=f"res_txt_{i}_{s_idx}", height=70
                    )
            
            # 4. Cierre & Tarea Fields
            st.write("---")

            st.session_state.temas_details[i]["cierre"] = st.text_input(
                "Cierre", 
                value=tema_data["cierre"], 
                key=f"cierre_tema_{i}"
            )

            st.session_state.temas_details[i]["tarea"] = st.text_input(
                "Tarea", 
                value=tema_data["tarea"], 
                placeholder="El campo está vacío",
                key=f"tarea_tema_{i}"
            )

# --- SUBMIT ---
st.write("---")
if st.button("💾 Guardar Datos del Formulario", type="primary", use_container_width=True):
    st.success("¡Todos los datos estructurados guardados con éxito!")
    
    datos_completos = {
        "datos_generales": {
            "colegio": colegio, "area": area, "nivel": nivel, "grado": grado, "seccion": seccion, "docente": docente, "mes": mes
        },
        "proposito": st.session_state.rows_proposito,
        "enfoques": edited_enfoque.to_dict(orient="records"),
        "temas": st.session_state.temas_details
    }
    st.json(datos_completos)