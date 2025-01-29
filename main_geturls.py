import asyncio
import sqlite3
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import tqdm

# Scrape product URLs from the category page
async def scrape_product_urls(page, category_url, file_handle, preset_length=164):
    await page.goto(category_url)
    content = await page.content()
    soup = BeautifulSoup(content, 'html.parser')
    
    # Extract the total number of pages
    pagination_elements = soup.select('#products-listing-section ol li')
    total_pages = int(pagination_elements[-2].text) if pagination_elements else preset_length
    
    seen_urls = set()
    
    for page_number in tqdm.tqdm(range(1, total_pages + 1), total=total_pages):
        paginated_url = f"{category_url}&page={page_number}"
        try:
            await page.goto(paginated_url)
        except:
            print("Could not load page")
            break
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        product_elements_container = soup.select('#products-listing-section > ul')
        product_elements = product_elements_container[0].find_all('li')
        for elem in product_elements:
            url_elem = elem.find('a')
            if url_elem:
                url = url_elem['href']
                if url not in seen_urls:
                    seen_urls.add(url)
                    file_handle.write(url + '\n')
                    file_handle.flush() 
        await page.wait_for_timeout(2000)  # Wait for new products to load

# Main function to orchestrate the scraping process
async def main():
    category_url_girl = 'https://www2.hm.com/en_us/women/products/view-all.html?productTypes=Vest,Toiletry+bag,Top,Top+Coat,T-shirt,Swimsuit,Swim+Top,Slippers,Skirt,Shorts,Shoes,Shirt,Scarf,Poncho,Pants,Pajamas,Pajama+Pants,Nightshirt,Necklace,Leggings,Knit+Sweater,Jumpsuit,Jeans,Jacket,Hat,Hair+Claw,Dress,Coat,Cardigan,Cap,Bra,Bodysuit,Blouse,Blazer,Bikini+Top,Bikini+bottoms,Bib+Cycling+Shorts,Belt,Bag,Tights'
    category_url_men = 'https://www2.hm.com/en_us/men/products/view-all.html?productTypes=Bib+Cycling+Shorts,Blazer,Briefs,Cardigan,Coat,Jacket,Jeans,Knit+Sweater,Pajama+Pants,Pajamas,Pants,Shirt,Shorts,Socks,Swim+Shorts,T-shirt,Top,Vest'
    category_url_kids = 'https://www2.hm.com/en_us/kids/9-14y/clothing/view-all.html?productTypes=Bikini+Top,Bikini+bottoms,Blazer,Blouse,Bodysuit,Briefs,Cardigan,Coat,Crop+Top,Dress,Jacket,Jeans,Jumpsuit,Knit+Sweater,Leggings,Pants,Shirt,Shorts,Skirt,Swim+Shorts,Swim+Top,T-shirt,Vest,Top'

    category_urls = [category_url_girl, category_url_men, category_url_kids]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        with open('product_urls.txt', 'w') as f:
            for category_url in category_urls:
                print(f'Scraping category: {category_url}')
                await scrape_product_urls(page, category_url, f)
        
        await browser.close()

# Run the main function
asyncio.run(main())
