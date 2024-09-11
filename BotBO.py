import fitz  # PyMuPDF
import re
import pandas as pd
import os
import shutil
import requests
import os
import pandas as pd
import shutil
from api.api import obtener_datos  # Importar la función de la API local

# Configuración de rutas
DIRECTORIO_PDF = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf'
CSV_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
EXCEL_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
DIRECTORIO_PROCESADOS = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf\\procesados'
HISTORIAL_CSV = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Historial\\historial.csv'

# Función para interactuar con la API
def obtener_datos_de_api(palabra_clave, anio, tipo_norma):
    api_url = "http://127.0.0.1:5000/api/obtener_datos"
    params = {
        'palabra_clave': palabra_clave,
        'anio': anio,
        'tipo_norma': tipo_norma
    }
    try:
        response = requests.get(api_url, params=params)
        if response.status_code == 200:
            return response.json()  # Datos en formato JSON
        else:
            print(f"Error al conectar con la API. Código: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error en la solicitud a la API: {e}")
        return None

# Procesar PDFs usando la API para obtener datos
def procesar_archivos_con_api(directorio_pdf):
    verificar_o_crear_directorio(directorio_pdf)
    archivos_pdf = [f for f in os.listdir(directorio_pdf) if f.lower().endswith('.pdf')]
    
    palabra_clave = input("Ingresa la palabra clave: ")
    anio = input("Ingresa el año: ")
    tipo_norma = input("Ingresa el tipo de norma: ")

    for archivo in archivos_pdf:
        pdf_path = os.path.join(directorio_pdf, archivo)
        datos_api = obtener_datos_de_api(palabra_clave, anio, tipo_norma)
        
        if datos_api:
            print(f"Datos obtenidos de la API para {archivo}: {datos_api}")
            
            # Aquí continúas con el procesamiento de PDFs como antes...
            if actualizar_historial_csv(pdf_path):
                resultados = extraer_variables(pdf_path)
                if resultados:
                    print(f"Resultados para {archivo}: {resultados}")
                    df = pd.DataFrame(resultados)
                    df.to_csv(CSV_PATH, index=False, sep='|', encoding='utf-8-sig')
                    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
                    dividir_pdf_por_docres(pdf_path, resultados)
                mover_pdf_a_procesados(pdf_path)
        else:
            print(f"No se obtuvieron datos de la API para {archivo}")

# Funciones de apoyo (copiadas de tu script original)
def verificar_o_crear_directorio(path):
    if not os.path.exists(path):
        os.makedirs(path)

def actualizar_historial_csv(pdf_path):
    # Función para verificar si el archivo ya fue procesado
    # Código de historial CSV aquí...
    pass

def extraer_variables(pdf_path):
    # Lógica para extraer variables de PDFs
    pass

def dividir_pdf_por_docres(pdf_path, resultados):
    # Lógica para dividir los PDFs según tipo de documento
    pass

def mover_pdf_a_procesados(pdf_path):
    # Lógica para mover los PDFs procesados a otra carpeta
    pass

# Ejecutar el procesamiento
procesar_archivos_con_api(DIRECTORIO_PDF)
