from scrapybara import Scrapybara
import asyncio
from playwright.async_api import async_playwright
import os
import requests
import json
import time

async def get_scrapybara_browser():
    client = Scrapybara(api_key="")
    instance = client.start_browser()
    return instance
async def generate_yc_summary(instance, start_url: str) -> list[dict]:
   
    cdp_url = instance.get_cdp_url().cdp_url
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()

        await page.goto(start_url)

        # scroll to the bottom of the page to load all items 
        #await page.locator('#footer').scroll_into_view_if_needed()
        #await asyncio.sleep(5)

        # get all store items
        store_items = page.locator('a[class^="_company"]')
        start_time = time.time()
        while time.time() - start_time < 10:
            await page.evaluate("window.scrollBy(0, 10000)")
            await asyncio.sleep(0.1)  # scroll delay
            print("scrolling")
        count = await store_items.count()
        print(count)
        
        companies = []
        for i in range(count):
            item = store_items.nth(i)


            # get item description + clean up
            nameL = item.locator('div').nth(4)
            name = await nameL.locator('span').first.inner_text()
            name = (name.strip()).replace("\n", " ")

            descL = item.locator('div').nth(5)
            desc = await descL.locator('span').first.inner_text()
            desc = (desc.strip()).replace("\n", " ")

            companies.append({
                "name": name,
                "description": desc
            })

            #print(name) #- for debugging if needed
        response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "deepseek/deepseek-chat-v3-0324:free",
            "messages": [
            {
                        "role": "system",
                        "content": (
                            "You are a startup analyst specializing in early-stage companies, "
                            "especially Y Combinator startups. Your job is to identify trends, emerging technologies, "
                            "and startup categories based on company descriptions. Use examples from the data provided."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"""Here is a list of companies with their descriptions:
{json.dumps(companies, indent=2)}

Please identify key startup trends from this list and mention a few representative companies for each trend."""
                    }
            ],
            
        })
        )
        print(response.json().get("choices")[0].get("message").get("content"))
        return companies
        

async def main():
    instance = await get_scrapybara_browser()

    try:
        await generate_yc_summary(
            instance,
            "https://www.ycombinator.com/companies/?batch=Spring%202025&batch=Winter%202025&batch=Fall%202024&batch=Summer%202024&batch=Winter%202024&batch=Summer%202023&batch=Winter%202023",
        )
    finally:
        # Be sure to close the browser instance after you're done!
        instance.stop()


if __name__ == "__main__":
    asyncio.run(main())
