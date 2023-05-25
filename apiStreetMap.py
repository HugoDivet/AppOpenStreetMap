import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
from starlette.responses import RedirectResponse
from cachetools import TTLCache, cached
from asyncio import run as run_asyncio

URL_ARRETS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows="
URL_CIRCUITS = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-circuits&q=&facet=route_long_name&facet=route_type&rows="
API_URL = "http://127.0.0.1:8000/"
api = FastAPI()

cache = TTLCache(maxsize=128, ttl=3600)

@api.get("/")
async def root():
    return RedirectResponse("docs", 301)

@api.get("/arret")
@cached(cache)
def cached_arrets(skip: int = 0, limit: int = 3800):
    return run_asyncio(arrets(skip, limit))

async def arrets(skip: int = 0, limit: int = 3800):
    # Get datas from API
    stopsDatas = await fetchDatas(URL_ARRETS, limit)

    # Create stops's model
    tasksStops = [processStop(stop, stopsDatas) for stop in stopsDatas]
    stops = await asyncio.gather(*tasksStops)

    # Add circus's info to stops
    circuits = await fetchDatasFromRoute('circuit')
    tasksInformationsStops = [addInformationsToStops(stop, circuits) for stop in stops]
    informationsStops = await asyncio.gather(*tasksInformationsStops)

    # Merge correspondences of same stops
    tasksMergeCorrespondences = [mergeCorrespondences(informationsStop, informationsStops) for informationsStop in informationsStops]
    correspondancesMerged = await asyncio.gather(*tasksMergeCorrespondences)

    # Delete redondant stops
    tasksMergeStops = [deleteRedondantStops(stop, correspondancesMerged) for stop in correspondancesMerged]
    mergeStops = await asyncio.gather(*tasksMergeStops)
    return mergeStops[skip: skip + limit]

async def processStop(stop, stops):
    if stop['fields']['location_type'] == '0' :
        arretModel = {
            'id' : stop['fields']['stop_id'],
            'name' : stop['fields']['stop_name'],
            'coordinate' : stop['fields']['stop_coordinates'],
            'wheelchaired': True if stop['fields']['wheelchair_boarding'] >= str(1) else False
        }
    else :
        arretModel = {
            'id' : stop['fields']['stop_id'],
            'name' : stop['fields']['stop_name'],
            'coordinate' : stop['fields']['stop_coordinates'],
            'wheelchaired': await getWheelchair(stop['fields']['stop_id'], stops)
        }
    return arretModel

async def addInformationsToStops(stopModel, circuits):
    correspondences = []
    for circuit in circuits:
        if circuit is not None and stopModel['coordinate'] in circuit['coordinates']:
            stopModel['type'] = circuit['circuit_type']
            stopModel['color'] = circuit['circuit_color']
            correspondence = {
                'type': circuit['circuit_type'],
                'color': circuit['circuit_color'],
                'name': circuit['circuit_name']
            }
            correspondences.append(correspondence)
        else :
            pass
    stopModel['correspondences'] = correspondences
    return stopModel

async def mergeCorrespondences(stop, existingStops):
    for existingStop in existingStops:
        if existingStop != stop \
                and 'type' in existingStop \
                and 'type' in stop \
                and existingStop['name'] == stop['name'] \
                and existingStop['type'] == stop['type'] \
                and abs(existingStop['coordinate'][1] - stop['coordinate'][1]) <= 0.01 \
                and abs(existingStop['coordinate'][0] - stop['coordinate'][0]) <= 0.01 \
                and stop['correspondences'] != existingStop['correspondences'] :

            for correspondence in existingStop['correspondences'] :
                if correspondence not in stop['correspondences']:
                    stop['correspondences'].extend([correspondence])

    return stop

async def deleteRedondantStops(stop, correspondancesMerged, stops = []):

    tasksMergeStops = []
    elementsASupprimer = []

    for correspondanceMerged in correspondancesMerged:
        if correspondanceMerged['correspondences'] != [] and correspondanceMerged['name'] == stop['name'] \
                and 'type' in correspondanceMerged \
                and 'type' in stop \
                and correspondanceMerged['type'] == stop['type'] \
                and await listAreSame(correspondanceMerged['correspondences'], stop['correspondences']) :
            elementsASupprimer.append(correspondanceMerged)
    #print("Elements à supp : " + str(elementsASupprimer))
    #print("Before : " + str(correspondancesMerged))
    for element in elementsASupprimer:
        correspondancesMerged.remove(element)
    #print("After : " + str(correspondancesMerged))

    return stop


async def listAreSame(list1, list2):
    if len(list1) == len(list2):
        for item in list1:
            if item not in list2:
                return False
        else:
            return True
    else:
        return False

@api.get('/circuit')
@cached(cache)
def cached_circuits(skip: int = 0, limit: int = 110):
    return run_asyncio(circuits(skip, limit))

async def circuits(skip: int = 0, limit: int = 110):
    records = await fetchDatas(URL_CIRCUITS, limit)

    tasks = [process_circuit(circuit) for circuit in records]
    circuitsModel = await asyncio.gather(*tasks)

    return circuitsModel[skip: skip + limit]

async def process_circuit(circuit):
    inverted_coordinates = [[coordinate[1], coordinate[0]] for coordinate in circuit['fields']['shape']['coordinates'][0]]
    route_short_name = circuit['fields']['route_short_name']

    if not route_short_name.isalpha() :
        circuitModel = {
            'circuit_id': circuit['fields']['route_id'],
            'circuit_name': circuit['fields']['route_short_name'],
            'coordinates': inverted_coordinates,
            'circuit_color': '#' + circuit['fields']['route_color'],
            'circuit_type': circuit['fields']['route_type']
        }
        return circuitModel

async def getWheelchair(id, stops):
    for stop in stops:
        if stop['fields']['location_type'] == '0' and stop['fields']['parent_station'] == id:
            return stop['fields']['wheelchair_boarding'] >= str(1)

async def fetchDatas(url, limit):
    async with aiohttp.ClientSession() as session:
        url_api_tan = url + str(limit)
        async with session.get(url_api_tan) as response:
            data = await response.json()
            return data['records']

async def fetchDatasFromRoute(route):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + route) as response:
            return await response.json()

if __name__ == "__main__":
    uvicorn.run("apiStreetMap:api", host="127.0.0.1", port=8000, workers=2, reload=True)
