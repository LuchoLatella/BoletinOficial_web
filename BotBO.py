import fitz  # PyMuPDF
import re
import pandas as pd
import os
import shutil
import logging
import tkinter as tk
from tkinter import ttk

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

# Funciones previamente definidas...

def procesar_pdfs(filtro_palabra_clave, filtro_anio, filtro_tipo):
    try:
        archivos_pdf = [f for f in os.listdir(DIRECTORIO_PDF) if f.lower().endswith('.pdf')]
        
        for archivo_pdf in archivos_pdf:
            pdf_path = os.path.join(DIRECTORIO_PDF, archivo_pdf)

            if not actualizar_historial_csv(pdf_path):
                continue

            resultados = extraer_variables(pdf_path)

            # Aplicar filtros
            resultados_filtrados = [
                resultado for resultado in resultados
                if filtro_palabra_clave in resultado['DocRes'] and
                resultado['Fecha'][:4] == str(filtro_anio) and
                filtro_tipo in resultado['DocRes']
            ]

            if resultados_filtrados:
                guardar_resultados_excel(pdf_path, resultados_filtrados)

                # Mover el archivo procesado al directorio de archivo
                destino = os.path.join(DIRECTORIO_ARCHIVO, archivo_pdf)
                shutil.move(pdf_path, destino)
                logging.info(f"PDF movido a {destino}")
                print(f"PDF movido a {destino}")

    except Exception as e:
        logging.error(f"Error en el proceso principal: {e}")
        print(f"Error en el proceso principal: {e}")


# Función que será llamada cuando se presione el botón
def iniciar_procesamiento():
    palabra_clave = entrada_palabra_clave.get()
    anio = combo_anio.get()
    tipo_norma = combo_tipo.get()
    
    procesar_pdfs(palabra_clave, anio, tipo_norma)

# Interfaz gráfica con Tkinter
ventana = tk.Tk()
ventana.title("Filtro de Procesamiento de PDF")

# Etiqueta y campo de entrada para la palabra clave
tk.Label(ventana, text="Palabra clave:").grid(row=0, column=0, padx=10, pady=10)
entrada_palabra_clave = tk.Entry(ventana)
entrada_palabra_clave.grid(row=0, column=1, padx=10, pady=10)

# Desplegable para el año de la norma (2024 a 2005)
tk.Label(ventana, text="Año:").grid(row=1, column=0, padx=10, pady=10)
combo_anio = ttk.Combobox(ventana, values=[str(year) for year in range(2024, 2004, -1)])
combo_anio.grid(row=1, column=1, padx=10, pady=10)
combo_anio.current(0)  # Seleccionar el año 2024 por defecto

# Desplegable para el tipo de norma
tk.Label(ventana, text="Tipo de norma:").grid(row=2, column=0, padx=10, pady=10)
combo_tipo = ttk.Combobox(ventana, values=["RESOLUCIÓN", "DISPOSICIÓN", "DECRETO"])
combo_tipo.grid(row=2, column=1, padx=10, pady=10)
combo_tipo.current(0)  # Seleccionar "RESOLUCIÓN" por defecto

# Botón para iniciar el procesamiento
boton_procesar = tk.Button(ventana, text="Iniciar procesamiento", command=iniciar_procesamiento)
boton_procesar.grid(row=3, columnspan=2, padx=10, pady=20)

ventana.mainloop()
