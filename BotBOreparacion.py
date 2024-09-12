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


# Función para verificar y crear directorios si no existen
def verificar_o_crear_directorio(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Función para actualizar historial en CSV
def actualizar_historial_csv(pdf_path):
    nombre_pdf = limpiar_nombre_archivo(os.path.basename(pdf_path).split('.')[0])
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
        nombre_pdf = limpiar_nombre_archivo(os.path.basename(pdf_path).split('.')[0])
        excel_path = os.path.join(EXCEL_PATH, f'{nombre_pdf}.xlsx')
        df_resultados = pd.DataFrame(resultados)
        df_resultados.to_excel(excel_path, index=False)
        logging.info(f"Resultados guardados en {excel_path}")
        print(f"Resultados guardados en {excel_path}")
    except Exception as e:
        logging.error(f"Error al guardar los resultados en Excel: {e}")
        print(f"Error al guardar los resultados en Excel: {e}")

def dividir_pdf_por_docres(pdf_path, resultados):
    try:
        documento = fitz.open(pdf_path)

        for i, resultado in enumerate(resultados):
            # Validar que exista la clave 'Pagina' y ajustar el índice a 0-index si es necesario
            inicio = resultado.get('Pagina', None)
            if inicio is None:
                logging.warning(f"No se encontró la página de inicio para el documento {resultado['DocRes']}.")
                continue

            inicio -= 1  # Convertir a 0-index

            # Determinar la página final
            fin = resultados[i + 1].get('Pagina', len(documento)) - 1 if i + 1 < len(resultados) else len(documento) - 1

            # Validar que los índices estén dentro del rango del documento
            if inicio < 0 or fin >= len(documento) or inicio > fin:
                logging.warning(f"Rango de páginas inválido para {resultado['DocRes']}: inicio={inicio}, fin={fin}.")
                continue

            docres = limpiar_nombre_archivo(resultado['DocRes'])

            # Obtener el año y mes del resultado
            fecha = resultado.get('Fecha', 'UnknownDate')  # Asegúrate de que la clave 'Fecha' esté en los resultados
            ano, mes = obtener_ano_mes(fecha)

            # Crear las carpetas si no existen
            carpeta_docres = os.path.join(DIRECTORIO_ARCHIVO, docres, ano, mes)
            os.makedirs(carpeta_docres, exist_ok=True)

            # Crear nuevo PDF
            nuevo_pdf = fitz.open()

            # Insertar las páginas dentro del rango
            for pagina_num in range(inicio, fin + 1):
                nuevo_pdf.insert_pdf(documento, from_page=pagina_num, to_page=pagina_num)

            # Guardar el nuevo documento en la ruta especificada
            nuevo_pdf_path = os.path.join(carpeta_docres, f'{docres}.pdf')
            nuevo_pdf.save(nuevo_pdf_path)
            nuevo_pdf.close()

            logging.info(f"Nuevo PDF guardado: {nuevo_pdf_path}")
            print(f"Nuevo PDF guardado: {nuevo_pdf_path}")

    except Exception as e:
        logging.error(f"Error al dividir el PDF: {e}")
        print(f"Error al dividir el PDF: {e}")

# Proceso principal
def procesar_pdfs():
    try:
        archivos_pdf = [f for f in os.listdir(DIRECTORIO_PDF) if f.lower().endswith('.pdf')]
        
        for archivo_pdf in archivos_pdf:
            pdf_path = os.path.join(DIRECTORIO_PDF, archivo_pdf)

            if not actualizar_historial_csv(pdf_path):
                continue

            resultados = extraer_variables(pdf_path)
            guardar_resultados_excel(pdf_path, resultados)
            
            # Mover el archivo procesado al directorio de archivo
            destino = os.path.join(DIRECTORIO_ARCHIVO, archivo_pdf)
            shutil.move(pdf_path, destino)
            logging.info(f"PDF movido a {destino}")
            print(f"PDF movido a {destino}")

    except Exception as e:
        logging.error(f"Error en el proceso principal: {e}")
        print(f"Error en el proceso principal: {e}")

if __name__ == "__main__":
    procesar_pdfs()