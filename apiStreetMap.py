import uvicorn
from fastapi import FastAPI
import requests
from starlette.responses import RedirectResponse

api = FastAPI()

@api.get("/")
async def root():
    return RedirectResponse("docs", 301)

@api.get("/arrets")
async def arrets(skip: int = 0, limit: int = 3800):

    row = 4000
    url_api_tan = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows=" + str(row)
    response = requests.get(url_api_tan)

    if response.status_code == 200:
            data = response.json()
            records = data['records']
    else:
        print("Erreur lors de la requête : ", response.status_code)

    for stopChilds in records:
        stopChilds['wheelchaired'] = False
        if stopChilds['fields']['location_type'] == '0':
            if int(stopChilds['fields']['wheelchair_boarding']) >= 1 :
               parent = await arret(stopChilds['fields']['parent_station'], records)
               parent['wheelchaired'] = True

    return records[skip : skip + limit]

@api.get("/arret")
async def arret(id, datas):
    for data in datas :
        if data['fields']['stop_id'] == id :
            return data

if __name__ == "__main__":
    uvicorn.run("apiStreetMap:api", host="127.0.0.1", port=8000, workers=2, reload=True)
