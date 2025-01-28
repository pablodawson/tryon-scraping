import json
from playwright.sync_api import sync_playwright
import sys

urls = open("urls.txt").readlines()
garment_links = []

for url in urls:
    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        
        # cargar todos los productos. apretar "cargar mas" hasta que no exista el boton
        while True:
            # scroll hasta abajo
            while True:
                previous_height = page.evaluate("document.body.scrollHeight")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    break
            
            # apretar "cargar mas productos"
            button_path = "//button[.//text()[contains(., 'Mostrar más')]]"
            
            if page.query_selector(button_path):
                try:
                    page.click(button_path)
                except:
                    print("No se pudo hacer click en el botón, saliendo")
                    break
                print("Cargando más productos...")
            else:
                print("Llegamos al final")
                break
        
        # Sacar todos los links de los productos
        page.wait_for_selector('//*[@id="gallery-layout-container"]')
        items = page.query_selector_all('//*[@id="gallery-layout-container"]/*')
        item_list = [item.inner_text() for item in items]

        for item in items:
            link = item.query_selector("a")
            if link:
                href = link.get_attribute("href")
                garment_links.append(href)
        
        print(f"Se encontraron {len(garment_links)} links")
    browser.close()


# Save the links
with open("garment_links.json", "w") as f:
    json.dump(garment_links, f)