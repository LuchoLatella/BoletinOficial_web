import fitz  # PyMuPDF
import re
import pandas as pd
import os
import shutil
import logging

# Configuración de rutas
DIRECTORIO_PDF = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf'
CSV_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
EXCEL_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
DIRECTORIO_PROCESADOS = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf\\procesados'
HISTORIAL_CSV = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Historial\\historial.csv'

# Configuración de logs
logging.basicConfig(filename='procesamiento.log', level=logging.INFO,
                    format='%(asctime)s:%(levelname)s:%(message)s')

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

# Función para buscar la página que contiene el patrón DocRes
def buscar_pagina_por_docres(documento, docres):
    for pagina_num in range(len(documento)):
        pagina = documento.load_page(pagina_num)
        texto = pagina.get_text("text")
        if re.search(docres, texto):
            return pagina_num
    return None  # Retorna None si no se encuentra la página

# Función para buscar la página que contiene el patrón Artículo
def buscar_pagina_articulo(documento, articulo):
    for pagina_num in range(len(documento)):
        pagina = documento.load_page(pagina_num)
        texto = pagina.get_text("text")
        if re.search(articulo, texto):
            return pagina_num
    return None  # Retorna None si no se encuentra la página

# Función para verificar y crear directorios si no existen
def verificar_o_crear_directorio(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para actualizar historial en CSV
def actualizar_historial_csv(pdf_path):
    nombre_pdf = os.path.basename(pdf_path).split('.')[0]
    anio, mes, dia = nombre_pdf[:4], nombre_pdf[4:6], nombre_pdf[6:8]

    verificar_o_crear_directorio(os.path.dirname(HISTORIAL_CSV))

    try:
        df_historial = pd.read_csv(HISTORIAL_CSV, encoding='utf-8-sig') if os.path.exists(HISTORIAL_CSV) else pd.DataFrame(columns=['Archivo', 'YYYY', 'MM', 'DD'])
        
        if df_historial[(df_historial['Archivo'] == nombre_pdf)].empty:
            nuevo_historial = pd.DataFrame([[nombre_pdf, anio, mes, dia]], columns=['Archivo', 'YYYY', 'MM', 'DD'])
            df_historial = pd.concat([df_historial, nuevo_historial], ignore_index=True)
            df_historial.to_csv(HISTORIAL_CSV, index=False, encoding='utf-8-sig')
            logging.info(f"'{nombre_pdf}' agregado al historial CSV.")
            print(f"'{nombre_pdf}' agregado al historial CSV.")
        else:
            logging.info(f"'{nombre_pdf}' ya está en el historial, no se procesará de nuevo.")
            print(f"'{nombre_pdf}' ya está en el historial, no se procesará de nuevo.")
            return False
    except Exception as e:
        logging.error(f"Error al actualizar el historial: {e}")
        print(f"Error al actualizar el historial: {e}")
        return False

    return True

# Función para guardar los resultados en un archivo Excel específico para cada PDF
def guardar_resultados_excel(pdf_path, resultados):
    try:
        nombre_pdf = os.path.basename(pdf_path).split('.')[0]
        excel_path = os.path.join(EXCEL_PATH, f'{nombre_pdf}.xlsx')
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_excel(excel_path, index=False)
        logging.info(f"Resultados guardados en {excel_path}")
        print(f"Resultados guardados en {excel_path}")
    except Exception as e:
        logging.error(f"Error al guardar los resultados en Excel: {e}")
        print(f"Error al guardar los resultados en Excel: {e}")

# Función para dividir el PDF y guardar según tipo de DocRes
def dividir_pdf_por_docres(pdf_path, resultados):
    nombre_pdf = os.path.basename(pdf_path).split('.')[0]
    anio, mes = nombre_pdf[:4], nombre_pdf[4:6]
    carpeta_anio_mes = os.path.join(DIRECTORIO_PROCESADOS, anio, mes)

    carpetas_tipos = {'RESOLUCIÓN': 'RESOLUCIONES', 'DISPOSICIÓN': 'DISPOSICIONES', 'DECRETO': 'DECRETOS'}
    for carpeta in carpetas_tipos.values():
        verificar_o_crear_directorio(os.path.join(carpeta_anio_mes, carpeta))

    documento = fitz.open(pdf_path)
    for i, resultado in enumerate(resultados):
        docres = resultado['DocRes']
        if docres != 'null':
            tipo_doc = next((tipo for tipo in carpetas_tipos if tipo in docres), 'Otros')
            carpeta_tipo = os.path.join(carpeta_anio_mes, carpetas_tipos.get(tipo_doc, 'OTROS'))

            verificar_o_crear_directorio(carpeta_tipo)
            
            pdf_salida = fitz.open()
            pagina_inicio = buscar_pagina_por_docres(documento, docres)
            if i + 1 < len(resultados):
                siguiente_docres = resultados[i + 1]['DocRes']
                pagina_fin = buscar_pagina_por_docres(documento, siguiente_docres) if siguiente_docres != 'null' else documento.page_count
            else:
                pagina_fin = documento.page_count

            for pagina_num in range(pagina_inicio, pagina_fin):
                pdf_salida.insert_pdf(documento, from_page=pagina_num, to_page=pagina_num)

            if pdf_salida.page_count > 0:
                pdf_salida_path = os.path.join(carpeta_tipo, f'{docres}.pdf')
                verificar_o_crear_directorio(os.path.dirname(pdf_salida_path))
                pdf_salida.save(pdf_salida_path)
                logging.info(f"PDF {pdf_salida_path} guardado correctamente.")
                print(f"PDF {pdf_salida_path} guardado correctamente.")
                pdf_salida.close()

# Función principal para procesar todos los archivos PDF en el directorio
def procesar_archivos_pdf():
    for archivo in os.listdir(DIRECTORIO_PDF):
        if archivo.lower().endswith('.pdf'):
            pdf_path = os.path.join(DIRECTORIO_PDF, archivo)
            if actualizar_historial_csv(pdf_path):
                resultados = extraer_variables(pdf_path)
                guardar_resultados_excel(pdf_path, resultados)
                dividir_pdf_por_docres(pdf_path, resultados)

# Ejecución del script
if __name__ == "__main__":
    procesar_archivos_pdf()
