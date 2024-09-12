import fitz  # PyMuPDF
import re
import pandas as pd
import os
import shutil
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Configuración de rutas
DIRECTORIO_PDF = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf'
CSV_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
EXCEL_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
DIRECTORIO_PROCESADOS = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf\\procesados'
HISTORIAL_CSV = r'\\10.78.15.33\e\GOAEGYRS\\BoletinOficial\\Historial\\historial.csv'
DIRECTORIO_ARCHIVO = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf\\procesados\\Archivo'

# Configuración de logs
logging.basicConfig(filename='procesamiento.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Función para limpiar el nombre de archivo
def limpiar_nombre_archivo(nombre):
    return re.sub(r'[\/:*?"<>|]', '-', nombre)

# Función para buscar coincidencias
def buscar_coincidencias(patron, lineas, inicio=0, limite=None):
    for i in range(inicio, len(lineas) if limite is None else limite):
        if re.match(patron, lineas[i].strip()):
            return i, lineas[i].strip()
    return None, None

# Función para extraer el texto que sigue a "VISTO"
def extraer_visto(lineas, idx_visto):
    texto_visto = []
    for linea in lineas[idx_visto + 1:]:
        if not linea.strip() or re.match(r'^CONSIDERANDO:$', linea.strip()):
            break
        texto_visto.append(linea.strip())
    return ' '.join(texto_visto) if texto_visto else 'null'

# Función para extraer los artículos de un documento en base a renglones
def extraer_articulos_por_renglon(lineas, idx_articulo, frase_clave="Boletín Oficial"):
    articulos = []
    for i in range(idx_articulo, len(lineas)):
        linea = lineas[i].strip()
        if frase_clave in linea:
            articulos.append(linea)
            break
        if re.match(r'^(RESOLUCIÓN|DISPOSICIÓN|DECRETO)\b', linea):
            break
        articulos.append(linea)
    return ' '.join(articulos) if articulos else 'null'

# Función para extraer las variables requeridas a nivel de renglón
def extraer_variables(pdf_path):
    try:
        print(f"Extrayendo variables del archivo {pdf_path}")
        logging.info(f"Extrayendo variables del archivo {pdf_path}")
        documento = fitz.open(pdf_path)
        lineas_globales = []

        # Leer todo el documento en una lista de renglones globales
        for pagina_num in range(len(documento)):
            pagina = documento.load_page(pagina_num)
            lineas = pagina.get_text("text").split('\n')
            lineas_globales.extend(lineas)

        resultados = []

        patron_docres = r'^(RESOLUCIÓN|DISPOSICIÓN|DECRETO)\b'
        patron_fecha = r'Buenos Aires,'
        patron_visto = r'^VISTO:'
        patron_articulo = r'^Artículo 1'

        idx = 0
        while idx < len(lineas_globales):
            idx_docres, docres = buscar_coincidencias(patron_docres, lineas_globales, inicio=idx)
            if docres:
                logging.info(f"DocRes encontrada: {docres} en índice {idx_docres}")
                print(f"DocRes encontrada: {docres} en índice {idx_docres}")
                idx_fecha, fecha = buscar_coincidencias(patron_fecha, lineas_globales, inicio=idx_docres)
                idx_visto, visto = buscar_coincidencias(patron_visto, lineas_globales, inicio=idx_docres + 1, limite=idx_docres + 11)
                visto_texto = extraer_visto(lineas_globales, idx_visto) if visto else 'null'
                idx_articulo, articulo = buscar_coincidencias(patron_articulo, lineas_globales, inicio=idx_docres + 1)
                articulos = extraer_articulos_por_renglon(lineas_globales, idx_articulo) if articulo else 'null'

                resultados.append({
                    'DocRes': docres,
                    'Fecha': fecha if fecha else 'null',
                    'Visto': visto_texto,
                    'Artículos': articulos
                })

                idx = idx_docres + 1
            else:
                break

        return resultados
    except Exception as e:
        logging.error(f"Error procesando el PDF: {e}")
        print(f"Error procesando el PDF {pdf_path}: {e}")
        return []

# Función para procesar los PDFs basándose en la interfaz gráfica
def procesar_con_filtros(palabra_clave, anio, tipo_norma):
    # Filtrar y procesar los archivos PDF según la palabra clave, año y tipo de norma
    print(f"Procesando con palabra clave: {palabra_clave}, año: {anio}, tipo: {tipo_norma}")
    procesar_pdfs()

# Interfaz gráfica usando Tkinter
def mostrar_interfaz():
    root = tk.Tk()
    root.title("Búsqueda en Boletín Oficial")

    # Etiquetas y campos de entrada
    label_palabra_clave = tk.Label(root, text="Palabra clave:")
    label_palabra_clave.grid(row=0, column=0, padx=10, pady=10)
    entry_palabra_clave = tk.Entry(root, width=30)
    entry_palabra_clave.grid(row=0, column=1, padx=10, pady=10)

    # Filtro de año
    label_anio = tk.Label(root, text="Año:")
    label_anio.grid(row=1, column=0, padx=10, pady=10)
    combo_anio = ttk.Combobox(root, values=[2024, 2023, 2022, 2021, 2020, 2019], state="readonly", width=28)
    combo_anio.grid(row=1, column=1, padx=10, pady=10)

    # Filtro de tipo de norma
    label_tipo_norma = tk.Label(root, text="Tipo de norma:")
    label_tipo_norma.grid(row=2, column=0, padx=10, pady=10)
    combo_tipo_norma = ttk.Combobox(root, values=["RESOLUCIÓN", "DISPOSICIÓN", "DECRETO"], state="readonly", width=28)
    combo_tipo_norma.grid(row=2, column=1, padx=10, pady=10)

    # Botón para iniciar el procesamiento
    def iniciar_procesamiento():
        palabra_clave = entry_palabra_clave.get()
        anio = combo_anio.get()
        tipo_norma = combo_tipo_norma.get()

        if not palabra_clave or not anio or not tipo_norma:
            messagebox.showwarning("Error", "Por favor, complete todos los campos")
        else:
            procesar_con_filtros(palabra_clave, anio, tipo_norma)

    btn_procesar = tk.Button(root, text="Procesar", command=iniciar_procesamiento)
    btn_procesar.grid(row=3, column=1, pady=20)

    root.mainloop()

if __name__ == "__main__":
    mostrar_interfaz()
