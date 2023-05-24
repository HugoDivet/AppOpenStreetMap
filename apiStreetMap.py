import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse

URL_ARRETS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows="
URL_CIRCUITS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-circuits&q=&facet=route_long_name&facet=route_type&rows="
api = FastAPI()

session =  aiohttp.ClientSession()

@api.get("/")
async def root():
    return RedirectResponse("docs", 301)

@api.get("/arret")
async def arrets(skip: int = 0, limit: int = 3800):
    records = await fetchDatas(URL_ARRETS, limit)

    async def process_record(record):
        record['wheelchaired'] = False
        if record['fields']['location_type'] == '0' and int(record['fields']['wheelchair_boarding']) >= 1:
            await arretFromDatas(record['fields']['parent_station'], records)

    tasks = [process_record(record) for record in records]

    await asyncio.gather(*tasks)

    return records[skip: skip + limit]

@api.get('/circuit')
async def circuits(skip: int = 0, limit: int = 110):

    records = await fetchDatas(URL_CIRCUITS, limit)

    tasks = [process_circuit(circuit) for circuit in records]
    circuitsModel = await asyncio.gather(*tasks)

    return circuitsModel[skip: skip + limit]

async def arretFromDatas(id, datas):
    for data in datas:
        if data['fields']['stop_id'] == id:
            data['wheelchaired'] = True
            return

async def fetchDatas(url, limit):
    url_api_tan = url + str(limit)
    async with session.get(url_api_tan) as response:
        data = await response.json()
        return data['records']

async def process_circuit(circuit):
    inverted_coordinates = []
    for coordinate in circuit['fields']['shape']['coordinates'][0]:
        inverted_coordinate = [coordinate[1], coordinate[0]]
        inverted_coordinates.append(inverted_coordinate)

    circuitModel = {
        'circuit_id': circuit['fields']['route_id'],
        'circuit_name': circuit['fields']['route_long_name'],
        'coordinates': inverted_coordinates,
        'circuit_color': '#' + circuit['fields']['route_color'],
        'circuit_type': circuit['fields']['route_type']
    }

    return circuitModel

if __name__ == "__main__":
    uvicorn.run("apiStreetMap:api", host="127.0.0.1", port=8000, workers=2, reload=True)
