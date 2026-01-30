import extraccion
import time
import os
from openpyxl import Workbook
from openpyxl.styles import Font # Para poner los títulos en negrita

# --- 1. CONFIGURACIÓN ---
url_web = 'https://www.falabella.com/falabella-cl'
archivo_entrada = 'scrapping_data_example.csv'
archivo_salida = 'resultados_falabella.xlsx' # Extensión .xlsx

# --- 2. PREPARACIÓN DEL EXCEL ---
wb = Workbook()
ws = wb.active
ws.title = "Resultados Falabella"

# Encabezados de columnas
encabezados = [
    'Criterio Búsqueda', 
    'Nombre Producto', 
    'SKU', 
    'Precio Normal', 
    'Precio Oferta', 
    'Vendedor', 
    'Estrellas', 
    'Llega Mañana', 
    'Retira Mañana'
]

# Escribir encabezados en la fila 1
ws.append(encabezados)

# Dar estilo negrita a la primera fila (opcional, pero se ve mejor)
for cell in ws[1]:
    cell.font = Font(bold=True)

# --- 3. LECTURA Y PROCESO ---
if os.path.exists(archivo_entrada):
    with open(archivo_entrada, 'r', encoding='utf-8') as f_in:
        criterios = [line.strip() for line in f_in if line.strip()]
    
    print(f"--- Iniciando proceso para {len(criterios)} criterios ---")

    for i, criterio in enumerate(criterios):
        print(f"[{i+1}/{len(criterios)}] Buscando: {criterio}...")
        
        # Llamada al módulo de extracción
        try:
            datos = extraccion.extraer_datos(url_web, criterio)
        except Exception as e:
            print(f"Error crítico en modulo extracción: {e}")
            datos = []

        # Si no hay datos, escribimos una fila indicando que no se encontró
        if not datos:
            # Fila vacía con el mensaje de "No encontrado"
            fila_vacia = [criterio, "No encontrado / Sin stock", "", 0, "", "", "", "", ""]
            ws.append(fila_vacia)
            print("   -> Sin resultados.")
        
        # --- 4. AGREGAR DATOS AL EXCEL ---
        for item in datos:
            # Convertimos True/False a texto "SI"/"NO" para que se vea bien
            llega = "SI" if item.get('llega_manana') else "NO"
            retira = "SI" if item.get('retira_manana') else "NO"

            # Armamos la fila (lista de valores)
            fila = [
                criterio,
                item.get('nombre'),
                item.get('sku'),
                item.get('precio normal'),
                item.get('precio oferta'), # Si es None, Excel deja la celda vacía automáticamente
                item.get('canal de venta'),
                item.get('estrellas'),
                llega,
                retira
            ]
            
            ws.append(fila)
            
            # Feedback en consola
            p_oferta = item.get('precio oferta') if item.get('precio oferta') else "-"
            print(f"   -> Guardado: {item.get('sku')} | Oferta: {p_oferta}")

        # Guardamos el archivo en cada iteración por seguridad 
        # (así si se corta la luz, tienes lo avanzado)
        wb.save(archivo_salida)

        # Pausa de seguridad
        time.sleep(2)

else:
    print(f"Error: No se encontró el archivo de entrada {archivo_entrada}")

print('=' * 40)
print(f'PROCESO FINALIZADO. Archivo creado: {archivo_salida}')
print('=' * 40)