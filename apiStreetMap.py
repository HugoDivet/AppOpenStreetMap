import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

URL = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows="
api = FastAPI()

@api.get("/")
async def root():
    return RedirectResponse("docs", 301)

@api.get("/arret")
async def arrets(skip: int = 0, limit: int = 3800):
    async with aiohttp.ClientSession() as session:
        url_api_tan = URL + str(limit)
        async with session.get(url_api_tan) as response:
            if response.status == 200:
                data = await response.json()
                records = data['records']
            else:
                print("Erreur lors de la requête : ", response.status)
                return []

    tasks = []
    for stopChilds in records:
        stopChilds['wheelchaired'] = False
        if stopChilds['fields']['location_type'] == '0':
            if int(stopChilds['fields']['wheelchair_boarding']) >= 1:
                tasks.append(arretFromDatas(stopChilds['fields']['parent_station'], records))

    await asyncio.gather(*tasks)
    return records[skip: skip + limit]

async def arretFromDatas(id, datas):
    for data in datas:
        if data['fields']['stop_id'] == id:
            data['wheelchaired'] = True
            return

if __name__ == "__main__":
    uvicorn.run("apiStreetMap:api", host="127.0.0.1", port=8000, workers=2, reload=True)
