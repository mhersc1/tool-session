# adapters/streamlit_ui.py
import streamlit as st
import pandas as pd
import traceback
from application.ports.inbound import UISessionToolPort # Imports Inbound Port
from domain.models import (
    SessionContext, 
    GeneralData, 
    SessionPurposeRow, 
    TransversalFocusRow, 
    TopicDetail, 
    SubtopicRow
)

DEFAULT_ENFOQUES = pd.DataFrame([
    {"ENFOQUES TRANSVERSALES": "Enfoque ambiental", "ACCIONES OBSERVABLES": ""},
    {"ENFOQUES TRANSVERSALES": "Enfoque de derechos", "ACCIONES OBSERVABLES": ""}
])

def _init_default_session_state():
    st.session_state.setdefault("colegio", "I.E.P. Tradiciones Ricardo Palma")
    st.session_state.setdefault("area", "Historia")
    st.session_state.setdefault("nivel", "Primaria")
    st.session_state.setdefault("grado", "1º")
    st.session_state.setdefault("seccion", "Única")
    st.session_state.setdefault("docente", "Mary Y. Gamez Montesinos")
    st.session_state.setdefault("mes", "Enero")
    st.session_state.setdefault("tema_count", 1)
    st.session_state.setdefault("temas_details", {})
    st.session_state.setdefault("topic_subject_count", 1)
    st.session_state.setdefault("topic_subjects", [""])
    st.session_state.setdefault(
        "rows_proposito",
        [{"competencia": "", "capacidades": [], "desempenos": []}],
    )
    st.session_state.setdefault("enfoque_data", DEFAULT_ENFOQUES.copy())

def _hydrate_session_state(context: SessionContext) -> None:
    st.session_state.rows_proposito = [
         {
             "competencia": row.competencia,
             "capacidades": row.capacidades,
             "desempenos": row.desempenos,
         }
         for row in context.proposito
     ] or [{"competencia": "", "capacidades": [], "desempenos": []}]

    # Update widget keys directly to reflect new hydrated values
    for idx, row in enumerate(st.session_state.rows_proposito):
        st.session_state[f"comp_{idx}"] = row["competencia"]
        st.session_state[f"cap_{idx}"] = (
            "\n".join(row["capacidades"])
            if isinstance(row["capacidades"], list)
            else row["capacidades"]
        )
        st.session_state[f"des_{idx}"] = (
            "\n".join(row["desempenos"])
            if isinstance(row["desempenos"], list)
            else row["desempenos"]
        )

    st.session_state.enfoque_data = pd.DataFrame([
        {
            "ENFOQUES TRANSVERSALES": row.enfoque,
            "ACCIONES OBSERVABLES": row.acciones,
        }
        for row in context.enfoques
    ]) if context.enfoques else DEFAULT_ENFOQUES.copy()

    st.session_state.valor = context.valor

    st.session_state.tema_count = max(len(context.temas), 1)
    st.session_state.temas_details = {
        i + 1: {
            "titulo": tema.titulo,
            "inicio": tema.inicio,
            "subtemas": [
                {"subtema": sub.subtema, "resumen": sub.resumen}
                for sub in tema.subtemas
            ] or [{"subtema": "", "resumen": ""}],
            "cierre": tema.cierre or "¿Qué aprendimos?, ¿Cómo lo aprendimos?",
            "tarea": tema.tarea,
        }
        for i, tema in enumerate(context.temas)
    }

    # Sync Temas widget keys directly so inputs update on screen
    for i, tema in enumerate(context.temas, start=1):
        st.session_state[f"titulo_tema_input_{i}"] = tema.titulo
        st.session_state[f"inicio_tema_{i}"] = tema.inicio
        st.session_state[f"cierre_tema_{i}"] = tema.cierre or "¿Qué aprendimos?, ¿Cómo lo aprendimos?"
        st.session_state[f"tarea_tema_{i}"] = tema.tarea

        for s_idx, sub in enumerate(tema.subtemas):
            st.session_state[f"sub_txt_{i}_{s_idx}"] = sub.subtema
            st.session_state[f"res_txt_{i}_{s_idx}"] = sub.resumen

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

def render_ui(
    use_case: UISessionToolPort,
    initial_context: SessionContext | None = None,
):

    st.set_page_config(page_title="Formulario de Plantilla", layout="wide")

    st.title("📋 Formulario de Configuración de Sesión")
    st.write("Complete la información necesaria para rellenar la plantilla del documento.")
    if initial_context is not None and "form_loaded" not in st.session_state:
        _hydrate_session_state(initial_context)
        st.session_state.form_loaded = True
    else:
        _init_default_session_state()

    adjust_temas_state()

    # --- GROUP 1: Datos generales ---
    st.header("🏛️ 1. Datos Generales")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            colegio = st.text_input("Colegio", key="colegio")
            area = st.selectbox("Área", options=["Historia", "Geografía", "Economía"], key="area")
            nivel = st.selectbox("Nivel", options=["Primaria", "Secundaria"], key="nivel")
            grado = st.selectbox("Grado", options=["1º", "2º", "3º", "4º", "5º", "6º"], key="grado")
        with col2:
            seccion = st.text_input("Sección", key="seccion")
            docente = st.text_input("Docente", key="docente")
            mes = st.selectbox("Mes", options=[
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ], key="mes")

    # --- GROUP 1.1: Temas (Topic Subjects) ---
    st.header("📝 1.1 Temas (Topic Subjects)")
    st.number_input(
        "Número de Temas (máx. 10)",
        min_value=1,
        max_value=10,
        step=1,
        key="topic_subject_count",
    )

    # Ensure topic_subjects exists
    if "topic_subjects" not in st.session_state:
        st.session_state.topic_subjects = [""]
    # Keep the topic_subjects list length in sync with the selected count
    while len(st.session_state.topic_subjects) < st.session_state.topic_subject_count:
        st.session_state.topic_subjects.append("")
    while len(st.session_state.topic_subjects) > st.session_state.topic_subject_count:
        st.session_state.topic_subjects.pop()

    for idx in range(st.session_state.topic_subject_count):
        st.session_state.topic_subjects[idx] = st.text_input(
            f"Topic Subject {idx + 1}",
            value=st.session_state.topic_subjects[idx],
            key=f"topic_subject_{idx}",
        )

    # --- AGENT FORM FILLING BUTTON ---
    if st.button("🤖 Autocompletar con Agente", type="primary", use_container_width=True):
        # Trigger the agent to fill the forms based on topic subjects
        try:
           
            # Generate context based on current form data and topic subjects
            datos_generales_model = GeneralData(
                colegio=st.session_state.colegio,
                area=st.session_state.area,
                nivel=st.session_state.nivel,
                grado=st.session_state.grado,
                seccion=st.session_state.seccion,
                docente=st.session_state.docente,
                mes=st.session_state.mes
            )

                        # Create prompt from topic subjects
            topics_text = ", ".join([subj for subj in st.session_state.topic_subjects if subj.strip()])
            
            # Enhanced prompt that includes existing form data as context
            prompt = f"""Generar sesión de aprendizaje sobre los siguientes temas: {topics_text}

            Datos existentes del formulario:
            - Colegio: {datos_generales_model.colegio}
            - Área: {datos_generales_model.area}
            - Nivel: {datos_generales_model.nivel}
            - Grado: {datos_generales_model.grado}
            - Sección: {datos_generales_model.seccion}
            - Docente: {datos_generales_model.docente}
            - Mes: {datos_generales_model.mes}

            Por favor, preserva estos datos generales y genera el resto del contenido (propósito, enfoques transversales, temas y valor) considerando esta información contextual.
            Para los temas SÓLO mantén los títulos, sus demás atributos generalos. Asigna SÓLO un valor educativo que englobe la sesión de aprendizaje.
            """

            print("Prompt: ", prompt)
            # Call agent to generate context
            agent_context = use_case.preload(prompt)
            print(agent_context)
                       
            _hydrate_session_state(agent_context)
            st.rerun()
            st.success("🎉 ¡Formularios autocompletados con éxito por el agente!")
        except Exception as e:
            # Captura el stacktrace completo como una cadena de texto
            error_traceback = traceback.format_exc()
            
            # Muestra el mensaje amigable y el rastreo detallado
            st.error(f"Ocurrió un error al autocompletar: {e}")
            st.code(error_traceback, language="python")

    # --- GROUP 2: Propósito de la sesión ---
    st.header("🎯 2. Propósito de la Sesión")
    with st.container(border=True):
        action_col1, action_col2, _ = st.columns([1.5, 1.5, 7])
        with action_col1:
            if st.button("➕ Añadir Fila", key="add_row_prop"):
                st.session_state.rows_proposito.append({"competencia": "", "capacidades": [], "desempenos": []})
                st.rerun()
        with action_col2:
            if st.button("🗑️ Eliminar Última", key="del_row_prop") and len(st.session_state.rows_proposito) > 1:
                st.session_state.rows_proposito.pop()
                st.rerun()

        header_col1, header_col2, header_col3 = st.columns([2, 4, 4])
        header_col1.markdown("**Competencias**")
        header_col2.markdown("**Capacidades**")
        header_col3.markdown("**Desempeños**")

        for idx, row in enumerate(st.session_state.rows_proposito):
            col1, col2, col3 = st.columns([2, 4, 4])
            with col1:
                st.session_state.rows_proposito[idx]["competencia"] = st.text_area("C", label_visibility="collapsed", key=f"comp_{idx}", height=80)
            with col2:                
                st.session_state.rows_proposito[idx]["capacidades_text"] = st.text_area("Ca", label_visibility="collapsed", key=f"cap_{idx}", height=80)
                # Ensure we store as list
                st.session_state.rows_proposito[idx]["capacidades"] = st.session_state.rows_proposito[idx]["capacidades_text"].splitlines()
            with col3:
                st.session_state.rows_proposito[idx]["desempenos_text"] = st.text_area("D", label_visibility="collapsed", key=f"des_{idx}", height=80)
                st.session_state.rows_proposito[idx]["desempenos"] = st.session_state.rows_proposito[idx]["desempenos_text"].splitlines()

    # --- GROUP 3: Enfoque Transversal ---
    st.header("🌍 3. Enfoque Transversal")
    with st.container(border=True):
        edited_enfoque = st.data_editor(
            st.session_state.enfoque_data,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "ENFOQUES TRANSVERSALES": st.column_config.TextColumn(
                    "ENFOQUES TRANSVERSALES", disabled=True
                ),
                "ACCIONES OBSERVABLES": st.column_config.TextColumn("ACCIONES OBSERVABLES"),
            },
        )
        st.session_state.enfoque_data = edited_enfoque
        st.text_input("Valor", placeholder="Ingresa el valor para la sesión", key="valor")

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
        
        # Generate form sections dynamically for each topic using st.expander
        for i in range(1, st.session_state.tema_count + 1):
            tema_data = st.session_state.temas_details[i]
            
            # Display dynamic topic label. Changes if user inputs a specific title
            expander_title = f"📘 Tema {i}: {tema_data['titulo'] if tema_data['titulo'] else '(Por definir)'}"
            
            with st.expander(expander_title, expanded=(i == st.session_state.tema_count)):
                # 1. Main Topic Title Input
                st.session_state.temas_details[i]["titulo"] = st.text_input(
                    f"Nombre del Tema {i}",
                    key=f"titulo_tema_input_{i}"
                )
                
                # 2. Inicio Text Area
                st.session_state.temas_details[i]["inicio"] = st.text_area(
                    "Inicio", 
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
                            "S", label_visibility="collapsed", key=f"sub_txt_{i}_{s_idx}", height=70
                        )
                    with scol2:
                        st.session_state.temas_details[i]["subtemas"][s_idx]["resumen"] = st.text_area(
                            "R", label_visibility="collapsed", key=f"res_txt_{i}_{s_idx}", height=70
                        )
                
                # 4. Cierre & Tarea Fields
                st.write("---")

                st.session_state.temas_details[i]["cierre"] = st.text_input(
                    "Cierre",                     
                    key=f"cierre_tema_{i}"
                )

                st.session_state.temas_details[i]["tarea"] = st.text_input(
                    "Tarea", 
                    placeholder="El campo está vacío",
                    key=f"tarea_tema_{i}"
                )


    # --- GENERATE DOCUMENT BUTTON ---  
    if st.button("📄 Generar Documento Word", type="primary", use_container_width=True):
        try:
            # 1. Map Group 1: Datos Generales (directly from widget variables)
            datos_generales_model = GeneralData(
                colegio=colegio,
                area=area,
                nivel=nivel,
                grado=grado,
                seccion=seccion,
                docente=docente,
                mes=mes
            )
            
            # 2. Map Group 2: Propósito de la sesión (looping through your text area rows list)
            propositos_model = [
                SessionPurposeRow(
                    competencia=row["competencia"], 
                    capacidades=row["capacidades"], 
                    desempenos=row["desempenos"]
                )
                for row in st.session_state.rows_proposito
            ]
            
            # 3. Map Group 3: Enfoque Transversal (from the st.data_editor dataframe payload)
            enfoques_model = [
                TransversalFocusRow(
                    enfoque=row["ENFOQUES TRANSVERSALES"], 
                    acciones=row["ACCIONES OBSERVABLES"]
                )
                for row in edited_enfoque.to_dict(orient="records")
            ]
            
            # 4. Map Group 4: Temas (looping through the nested dict structure you created)
            temas_model = []
            for i in range(1, st.session_state.tema_count + 1):
                # Retrieve raw dict for topic 'i'
                raw_tema = st.session_state.temas_details[i]
                
                # Build the subtopic rows list for this specific topic first
                subtemas_list = [
                    SubtopicRow(
                        subtema=sub["subtema"], 
                        resumen=sub["resumen"]
                    ) 
                    for sub in raw_tema["subtemas"]
                ]
                
                # Instantiate the Topic Detail entity
                topic_detail_entity = TopicDetail(
                    titulo=raw_tema["titulo"],
                    inicio=raw_tema["inicio"],
                    subtemas=subtemas_list,   # Injecting the list of SubtopicRow objects
                    cierre=raw_tema["cierre"],
                    tarea=raw_tema["tarea"]
                )
                temas_model.append(topic_detail_entity)

            valor = st.session_state.valor

            # 5. ASSEMBLE THE AGGREGATE CORE CONTEXT!
            context = SessionContext(
                datos_generales=datos_generales_model,
                proposito=propositos_model,
                enfoques=enfoques_model,
                temas=temas_model,
                valor=valor
            )
            
            # 6. Pass this structured context safely through your Inbound Port Use Case
            docx_buffer = use_case.execute(context)

            # 7. Guardar los bytes en el estado de la sesión de Streamlit
            st.session_state["docx_bytes"] = docx_buffer.getvalue()
            print("Contexto: ")
            print(context)
            st.success("🎉 ¡Documento generado con éxito en memoria! Haz clic abajo para descargarlo.")
        except Exception as e:
            # Captura el stacktrace completo como una cadena de texto
            error_traceback = traceback.format_exc()
            
            # Muestra el mensaje amigable y el rastreo detallado
            st.error(f"Ocurrió un error en la generación: {e}")
            st.code(error_traceback, language="python")

    # --- BOTÓN DE DESCARGA DIRECTA ---
    if "docx_bytes" in st.session_state and st.session_state["docx_bytes"]:
        st.download_button(
            label="⬇️ Descargar Documento Word (.docx)",
            data=st.session_state["docx_bytes"],
            file_name="sesion_de_aprendizaje.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )