import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

URL_ARRETS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows="
URL_CIRCUITS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-circuits&q=&facet=route_long_name&facet=route_type&rows="
api = FastAPI()

@api.get("/")
async def root():
    return RedirectResponse("docs", 301)

@api.get("/arret")
async def arrets(skip: int = 0, limit: int = 3800):
    async with aiohttp.ClientSession() as session:
        url_api_tan = URL_ARRETS + str(limit)
        async with session.get(url_api_tan) as response:
                data = await response.json()
                records = data['records']

    tasks = []
    for stopChilds in records:
        stopChilds['wheelchaired'] = False
        if stopChilds['fields']['location_type'] == '0':
            if int(stopChilds['fields']['wheelchair_boarding']) >= 1:
                tasks.append(arretFromDatas(stopChilds['fields']['parent_station'], records))

    await asyncio.gather(*tasks)
    return records[skip: skip + limit]

@api.get('/circuit')
async def circuits(skip: int = 0, limit: int = 110):
    async with aiohttp.ClientSession() as session:
        url_api_tan = URL_CIRCUITS + str(limit)
        async with session.get(url_api_tan) as response:
                data = await response.json()
                records = data['records']

    tasks = []
    circuitsModel = []
    for circuit in records:
        tasks.append(createCircuitModel(circuit, circuitsModel))
    await asyncio.gather(*tasks)

    return circuitsModel[skip: skip + limit]

async def arretFromDatas(id, datas):
    for data in datas:
        if data['fields']['stop_id'] == id:
            data['wheelchaired'] = True
            return

async def createCircuitModel(circuit, circuitsModel):
    circuitModel = {}

    inverted_coordinates = []

    for coordinate in circuit['fields']['shape']['coordinates'][0]:
        inverted_coordinate = [coordinate[1], coordinate[0]]
        inverted_coordinates.append(inverted_coordinate)

    circuitModel['circuit_id'] = circuit['fields']['route_id']
    circuitModel['circuit_name'] = circuit['fields']['route_long_name']
    circuitModel['coordinates'] = inverted_coordinates
    circuitModel['circuit_color'] = '#' + circuit['fields']['route_color']
    circuitModel['circuit_type'] = circuit['fields']['route_type']

    circuitsModel.append(circuitModel)

if __name__ == "__main__":
    uvicorn.run("apiStreetMap:api", host="127.0.0.1", port=8000, workers=2, reload=True)
