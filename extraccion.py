import time
import re  # IMPORTANTE: Necesario para buscar números en el texto
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def extraer_datos(url_base, criterio_busqueda):
    lista_productos = []
    
    options = Options()
    # options.add_argument("--headless") 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        busqueda_fmt = criterio_busqueda.replace(" ", "+")
        url_final = f"{url_base}/search?Ntt={busqueda_fmt}"
        
        # print(f"--- Iniciando búsqueda en: {url_final} ---")
        driver.get(url_final)

        wait = WebDriverWait(driver, 10) # Bajé un poco el tiempo de espera para agilizar
        # Esperamos cualquier titulo para confirmar carga
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//b[contains(@id, "testId-pod-displaySubTitle")]')))
        except:
            print(f"No se encontraron resultados para: {criterio_busqueda}")
            return []

        elementos_titulos = driver.find_elements(By.XPATH, '//b[contains(@id, "testId-pod-displaySubTitle")]')

        for titulo_el in elementos_titulos:
            try:
                item = {}
                
                # 1. Nombre y SKU
                item["nombre"] = titulo_el.text
                id_string = titulo_el.get_attribute("id")
                sku = id_string.split("-")[-1] if "-" in id_string else "N/A"
                item["sku"] = sku

                # 2. Contexto
                try:
                    summary_container = titulo_el.find_element(By.XPATH, './ancestor::div[contains(@class, "pod-details")]/following-sibling::div[contains(@class, "pod-summary")]')
                except:
                    summary_container = titulo_el.find_element(By.XPATH, './ancestor::div[3]') 

                # 3. PRECIOS (LÓGICA MEJORADA)
                precio_normal = 0
                precio_oferta = None  # Por defecto None

                # MÉTOD 1: Buscar atributos data (Preciso para ofertas)
                li_elements = summary_container.find_elements(By.XPATH, './/li[contains(@class, "prices-")]')
                
                temp_prices = []
                
                # Extraer de atributos data- (si existen)
                for li in li_elements:
                    p_normal = li.get_attribute("data-normal-price")
                    p_event = li.get_attribute("data-event-price") 
                    
                    if p_normal: temp_prices.append(float(p_normal.replace(".", "")))
                    if p_event: temp_prices.append(float(p_event.replace(".", "")))

                # Si encontramos precios por atributos
                if temp_prices:
                    precio_max = max(temp_prices)
                    precio_min = min(temp_prices)
                    
                    if precio_max != precio_min:
                        precio_normal = int(precio_max)
                        precio_oferta = int(precio_min)
                    else:
                        precio_normal = int(precio_max)
                        precio_oferta = None

                # MÉTODO 2 (RESPALDO): Si precio_normal sigue siendo 0, leer TEXTO VISIBLE
                # Esto soluciona el caso del producto "Sodimac" que muestra solo "$ 8.790" sin atributos
                if precio_normal == 0:
                    texto_contenedor = summary_container.text
                    # Regex: Busca números que pueden tener puntos (ej: 8.790 o 14.990)
                    # Explicación regex: \d+ (digitos) seguidos opcionalmente de . y más digitos
                    numeros_encontrados = re.findall(r'\d{1,3}(?:\.\d{3})*(?:\,\d+)?', texto_contenedor)
                    
                    # Limpieza: quitar puntos y convertir a int
                    valores_limpios = []
                    for n in numeros_encontrados:
                        # Quitamos puntos para convertir a int. Si hay coma decimal, lo ignoramos o manejamos (CLP no usa decimales usualmente)
                        val_str = n.replace(".", "").split(",")[0] 
                        if val_str.isdigit():
                            val_int = int(val_str)
                            # Filtro de seguridad: ignorar números muy pequeños que puedan ser cuotas (ej: "3" cuotas)
                            # Asumimos que un producto vale más de $500 pesos
                            if val_int > 500: 
                                valores_limpios.append(val_int)
                    
                    if valores_limpios:
                        # Si encontramos solo un precio (ej: [8790])
                        if len(valores_limpios) == 1:
                            precio_normal = valores_limpios[0]
                            precio_oferta = None
                        else:
                            # Si encontramos dos (ej: [17990, 14990]) y falló el método 1
                            precio_normal = max(valores_limpios)
                            precio_oferta = min(valores_limpios)

                item["precio normal"] = precio_normal
                item["precio oferta"] = precio_oferta

                # 4. Canal de venta
                try:
                    seller_el = titulo_el.find_element(By.XPATH, '../span/b[contains(@id, "sellerText")] | ../span/b[contains(@class, "seller-text")]')
                    item["canal de venta"] = seller_el.text.replace("Por", "").strip()
                except:
                    item["canal de venta"] = "Falabella"

                # 5. Estrellas
                try:
                    rating_div = summary_container.find_element(By.XPATH, './/div[contains(@class, "ratings")]')
                    item["estrellas"] = rating_div.get_attribute("data-rating")
                    if not item["estrellas"]: item["estrellas"] = "0"
                except:
                    item["estrellas"] = "0"

                # 6. Badges
                item["llega_manana"] = False
                item["retira_manana"] = False
                try:
                    if summary_container.find_elements(By.XPATH, './/span[contains(@id, "badges-next_day")]'):
                        item["llega_manana"] = True
                    if summary_container.find_elements(By.XPATH, './/span[contains(@id, "badges-cc_next_day")]'):
                        item["retira_manana"] = True
                except:
                    pass

                lista_productos.append(item)

            except Exception as ex:
                continue

    except Exception as e:
        print(f"Error general en {criterio_busqueda}: {e}")
    finally:
        driver.quit()
    
    return lista_productos