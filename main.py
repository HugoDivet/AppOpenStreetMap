import asyncio
import aiohttp
import folium
from flask import Flask
from folium.plugins import MarkerCluster
from flask_caching import Cache

API_URL = "http://127.0.0.1:8000/"
CACHE_TIMEOUT = 3600

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

@app.route("/")
@cache.cached(CACHE_TIMEOUT)
async def tan_map():

    stops = await fetchDatas('arret')
    circuits = await fetchDatas('circuit')

    m = folium.Map(location=[47.2301, -1.5429], zoom_start=13)
    marker_cluster = MarkerCluster(name='Markers').add_to(m)

    stopsTasks = [processStop(stop, marker_cluster) for stop in stops]
    circuitsTasks = [processCircuit(circuit, m) for circuit in circuits]

    await asyncio.gather(*stopsTasks)
    await asyncio.gather(*circuitsTasks)

    folium.LayerControl().add_to(m)
    m.save('index.html')
    return m.get_root().render()

async def processStop(stop, marker_cluster):
    popup = ""

    if stop['fields']['location_type'] == '1':
        if stop['wheelchaired']:
            popup = "<i class='fa-sharp fa-solid fa-wheelchair-move'></i>"

        folium.map.Tooltip(stop['fields']['stop_name'])
        folium.Marker(
            location=stop['fields']['stop_coordinates'],
            popup=folium.Popup(f"<h5><b>{stop['fields']['stop_name']}</b></h5><br><br>" + popup, max_width=150),
            tooltip=stop['fields']['stop_name'],
            icon=folium.Icon(icon="train-subway", prefix="fa")
        ).add_to(marker_cluster)

async def processCircuit(circuit, m):

    folium.PolyLine(
        locations=circuit['coordinates'],
        color=circuit['circuit_color'],
        weight=2,
        opacity=1
    ).add_to(m)

async def fetchDatas(route):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + route) as response:
            return await response.json()

if __name__ == "__main__":
    app.run(debug=True)
