import os
from playwright.async_api import async_playwright
import asyncio
from bs4 import BeautifulSoup
import json
import aiohttp
import time

product_urls = open("product_urls.txt").readlines()[882:]
dataset_path = "hm_dataset"
os.makedirs(dataset_path, exist_ok=True)

async def fetch_image(session, url, output_folder):
    async with session.get(url) as response:
        img_data = await response.read()
        img_path = os.path.join(output_folder, os.path.basename(url).split("?")[0])
        with open(img_path, "wb") as img_file:
            img_file.write(img_data)

async def download_images(images, output_folder):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for image in images:
            try:
                img_tag = image.select("img")[-1]
            except:
                continue
            
            img_url = img_tag.attrs.get("src")
            tasks.append(fetch_image(session, img_url, output_folder))
        await asyncio.gather(*tasks)

async def wait_for_selector_soup(page, selectors):
    while True:
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        if all(soup.select(selector) for selector in selectors):
            return soup
        await page.wait_for_timeout(500)

async def scrape_images():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        for url in product_urls:
            url = url.strip()
            await page.goto(url)

            subproducts_selector = "#__next > main > div.rOGz > div > div > div:nth-child(2) > div > div > div.fe4979 > section > div.ff18ac.ab7eab > div"

            # Wait for the subproducts to load
            try:
                soup = await asyncio.wait_for(wait_for_selector_soup(page, [subproducts_selector]), timeout=30)
            except asyncio.TimeoutError:
                print(f"Timeout while waiting for subproducts on {url}")
                continue

            subproducts_container = soup.select(subproducts_selector)
            subproducts = subproducts_container[0].find_all('a')
            
            for subproduct in subproducts:
                timestart = time.time()

                url = subproduct['href']
                await page.goto("https://www2.hm.com" + url)
                sku = url.split(".")[-2]

                output_folder = os.path.join(dataset_path, sku)
                os.makedirs(output_folder, exist_ok=True)

                product_info = {}

                images_selector = "#__next > main > div.rOGz > div > div > div.c58e1c.e218ea.ce69b3.b1d39a.c9ee6e > div > ul"
                color_selector = "#__next > main > div.rOGz > div > div > div:nth-child(2) > div > div > div.fe4979 > section > label"
                description_selector = "#section-descriptionAccordion > div > div > p"
                features_selector = "#section-descriptionAccordion > div > div > dl"

                try:
                    soup = await asyncio.wait_for(wait_for_selector_soup(page, [images_selector, color_selector, description_selector, features_selector]), timeout=30)
                except asyncio.TimeoutError:
                    print(f"Timeout while waiting for product details on {url}")
                    continue

                images_container = soup.select(images_selector)
                images = images_container[0].find_all('li')

                product_info["title"] = soup.select("h1")[0].contents[0]
                product_info["color"] = soup.select(color_selector)[0].contents[0]
                product_info["description"] = soup.select(description_selector)[0].contents[0]
                
                features = soup.select(features_selector)[0].find_all("div")
                
                for feature in features:
                    key = feature.select("dt")[0].contents[0]
                    value = feature.select("dd")[0].contents[0]

                    if key not in ["Imported: ", "Concept: "]:
                        product_info[key] = value
                
                with open(os.path.join(output_folder, "info.json"), "w") as info_file:
                    json.dump(product_info, info_file)
                
                await download_images(images, output_folder)

                print(f"{sku}: {time.time()-timestart} seconds")
        
        await browser.close()

asyncio.run(scrape_images())
