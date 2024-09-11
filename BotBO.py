import fitz  # PyMuPDF
import re
import pandas as pd
import os
import shutil

# Configuración de rutas
DIRECTORIO_PDF = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf'
CSV_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
EXCEL_PATH = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Excelycsv'
DIRECTORIO_PROCESADOS = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\pdf\\procesados'
HISTORIAL_CSV = r'\\10.78.15.33\\e\\GOAEGYRS\\BoletinOficial\\Historial\\historial.csv'


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
def extraer_articulos_por_renglon(lineas, idx_articulo, frase_clave="Publíquese en el Boletín Oficial"):
    articulos = []
    for i in range(idx_articulo, len(lineas)):
        linea = lineas[i].strip()
        if frase_clave in linea:
            articulos.append(linea)  # Incluir la frase clave en los artículos
            break
        if re.match(r'^(RESOLUCIÓN|DISPOSICIÓN|DECRETO)\b', linea):
            print(f"Encontrado nuevo DocRes: {linea}")
            break
        articulos.append(linea)
    return ' '.join(articulos) if articulos else 'null'

# Función para extraer las variables requeridas a nivel de renglón
def extraer_variables(pdf_path):
    try:
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
                print(f"DocRes encontrada: {docres} en índice {idx_docres}")  # Depuración
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

                # Avanzar el índice para buscar la siguiente DocRes
                idx = idx_docres + 1  # Avanzar al siguiente renglón después de la última DocRes
            else:
                break

        return resultados
    except Exception as e:
        print(f"Error procesando el PDF: {e}")
        return []

# Función para verificar y crear directorios si no existen
def verificar_o_crear_directorio(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para actualizar historial en CSV
def actualizar_historial_csv(pdf_path):
    nombre_pdf = os.path.basename(pdf_path).split('.')[0]
    anio, mes, dia = nombre_pdf[:4], nombre_pdf[4:6], nombre_pdf[6:8]

    # Crear directorio para historial si no existe
    verificar_o_crear_directorio(os.path.dirname(HISTORIAL_CSV))

    # Cargar o crear el archivo CSV
    try:
        if not os.path.exists(HISTORIAL_CSV):
            df_historial = pd.DataFrame(columns=['Archivo', 'YYYY', 'MM', 'DD'])
        else:
            df_historial = pd.read_csv(HISTORIAL_CSV, encoding='utf-8-sig')

        # Verificar si el archivo ya fue procesado
        if df_historial[(df_historial['Archivo'] == nombre_pdf)].empty:
            nuevo_historial = pd.DataFrame([[nombre_pdf, anio, mes, dia]], columns=['Archivo', 'YYYY', 'MM', 'DD'])
            df_historial = pd.concat([df_historial, nuevo_historial], ignore_index=True)
            df_historial.to_csv(HISTORIAL_CSV, index=False, encoding='utf-8-sig')
            print(f"'{nombre_pdf}' agregado al historial CSV.")
        else:
            print(f"'{nombre_pdf}' ya está en el historial, no se procesará de nuevo.")
            return False

    except Exception as e:
        print(f"Error al actualizar el historial: {e}")
        return False

    return True

# Función para dividir el PDF y guardar según tipo de DocRes
def dividir_pdf_por_docres(pdf_path, resultados):
    nombre_pdf = os.path.basename(pdf_path).split('.')[0]
    anio, mes = nombre_pdf[:4], nombre_pdf[4:6]
    carpeta_anio_mes = os.path.join(DIRECTORIO_PROCESADOS, anio, mes)

    # Crear las carpetas para RESOLUCIONES, DISPOSICIONES, y DECRETOS
    carpetas_tipos = {'RESOLUCIÓN': 'RESOLUCIONES', 'DISPOSICIÓN': 'DISPOSICIONES', 'DECRETO': 'DECRETOS'}
    for carpeta in carpetas_tipos.values():
        verificar_o_crear_directorio(os.path.join(carpeta_anio_mes, carpeta))

    documento = fitz.open(pdf_path)
    for i, resultado in enumerate(resultados):
        docres = resultado['DocRes']
        if docres != 'null':
            tipo_doc = next((tipo for tipo in carpetas_tipos if docres.startswith(tipo)), None)
            if tipo_doc:
                carpeta_tipo = os.path.join(carpeta_anio_mes, carpetas_tipos[tipo_doc])
                pdf_salida = fitz.open()

                pagina_inicio = buscar_pagina_por_docres(documento, docres)
                pagina_fin = buscar_pagina_por_docres(documento, resultados[i + 1]['DocRes']) if i + 1 < len(resultados) else documento.page_count
                for pagina_num in range(pagina_inicio, pagina_fin):
                    pdf_salida.insert_pdf(documento, from_page=pagina_num, to_page=pagina_num)

                pdf_salida_path = os.path.join(carpeta_tipo, f'{sanitizar_nombre_archivo(DocRes)}.pdf')
                pdf_salida.save(pdf_salida_path)
                pdf_salida.close()
                print(f"PDF guardado en {pdf_salida_path}")

# Función para mover el archivo PDF a la carpeta de procesados
def mover_pdf_a_procesados(pdf_path):
    archivo = os.path.basename(pdf_path)
    destino = os.path.join(DIRECTORIO_PROCESADOS, archivo)
    shutil.move(pdf_path, destino)
    print(f"Archivo movido a {destino}")

# Función para buscar la página de inicio de un documento
def buscar_pagina_por_docres(documento, docres):
    for pagina_num in range(documento.page_count):
        pagina = documento.load_page(pagina_num)
        texto_pagina = pagina.get_text("text")
        if docres in texto_pagina:
            return pagina_num
    return None

# Función para sanitizar nombres de archivos
def sanitizar_nombre_archivo(nombre):
    return re.sub(r'[\\/:*?"<>|]', '_', nombre)

# Función principal para procesar los archivos en el directorio
def procesar_archivos_en_directorio(directorio_pdf):
    verificar_o_crear_directorio(directorio_pdf)
    archivos_pdf = [f for f in os.listdir(directorio_pdf) if f.lower().endswith('.pdf')]
    for archivo in archivos_pdf:
        pdf_path = os.path.join(directorio_pdf, archivo)
        if actualizar_historial_csv(pdf_path):
            resultados = extraer_variables(pdf_path)
            if resultados:
                print(f"Resultados para {archivo}: {resultados}")
                try:
                    df = pd.DataFrame(resultados)
                    df.to_csv(CSV_PATH, index=False, sep='|', encoding='utf-8-sig')
                    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')
                    print(f"Datos exportados a CSV en {CSV_PATH}")
                    print(f"Archivo Excel generado: {EXCEL_PATH}")
                except Exception as e:
                    print(f"Error al guardar el archivo CSV/Excel: {e}")
                dividir_pdf_por_docres(pdf_path, resultados)
            else:
                print(f"No se encontraron resultados para {archivo}.")
            mover_pdf_a_procesados(pdf_path)
        else:
            print(f"El archivo {archivo} ya está en el historial, se omite.")

# Ejecutar el procesamiento de archivos PDF
procesar_archivos_en_directorio(DIRECTORIO_PDF)