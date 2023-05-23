import asyncio
import aiohttp
import folium
from flask import Flask
from folium.plugins import FastMarkerCluster
from flask_caching import Cache
from clusters import cluster_options

API_URL = "http://127.0.0.1:8000/"
CACHE_TIMEOUT = 3600

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

@app.route("/")
@cache.cached(CACHE_TIMEOUT)
async def tan_map():

    stops = await fetchDatas('arret')
    circuits = await fetchDatas('circuit')

    m = folium.Map(location=[47.2301, -1.5429], zoom_start=12, tiles='cartodbdark_matter')

    clusters = {}

    for cluster_name, options in cluster_options.items():
        clusters[cluster_name] = FastMarkerCluster(name=options['name'], data=options['data'], options=options.get('options')).add_to(m)

    busMarkersCluster = clusters['busMarkersCluster']
    tramMarkersCluster = clusters['tramMarkersCluster']
    ferryMarkersCluster = clusters['ferryMarkersCluster']
    busLineCluster = clusters['busLineCluster']
    tramLineCluster = clusters['tramLineCluster']
    ferryLineCluster = clusters['ferryLineCluster']

    stopsTasks = []
    for stop in stops:
        stopsTasks.append(asyncio.create_task(processStop(stop, circuits, m, busMarkersCluster, tramMarkersCluster, ferryMarkersCluster)))

    circuitsTasks = []
    for circuit in circuits:
        circuitsTasks.append(asyncio.create_task(processCircuit(circuit, m, busLineCluster, tramLineCluster, ferryLineCluster)))

    await asyncio.gather(*stopsTasks, *circuitsTasks)

    folium.LayerControl().add_to(m)
    m.save('index.html')
    return m.get_root().render()

async def processStop(stop, circuits, m, busmarkerscluster, trammarkerscluster, ferrymarkerscluster):

    popup = ""

    if stop['fields']['location_type'] == '1':
        if stop['wheelchaired']:
            popup = "<i class='fa-sharp fa-solid fa-wheelchair-move'></i>"

        arrayStop = getStopArray(getAssociatedCircuitType(stop, circuits))

        if arrayStop is not None :
            if arrayStop[1] == 'busMarkersCluster':
                markerCluster = busmarkerscluster
                color = 'red'
            elif arrayStop[1] == 'tramMarkersCluster':
                markerCluster = trammarkerscluster
                color = 'green'
            elif arrayStop[1] == 'ferryMarkersCluster':
                markerCluster = ferrymarkerscluster
                color = 'blue'

            folium.map.Tooltip(stop['fields']['stop_name'])
            folium.Marker(
                location=stop['fields']['stop_coordinates'],
                popup=folium.Popup(f"<h5><b>{stop['fields']['stop_name']}</b></h5><br><br>" + popup, max_width=150),
                tooltip=stop['fields']['stop_name'],
                icon=folium.Icon(color, icon=arrayStop[0], prefix="fa"),
            ).add_to(markerCluster)

async def processCircuit(circuit, m, buslinecluster, tramlinecluster, ferrylinecluster):

    if circuit['circuit_type'] == 'Bus':
        lineCluster = buslinecluster
    elif circuit['circuit_type'] == 'Tram':
        lineCluster = tramlinecluster
    elif circuit['circuit_type'] == 'Ferry':
        lineCluster = ferrylinecluster

    folium.PolyLine(
        locations=circuit['coordinates'],
        color=circuit['circuit_color'],
        weight=2,
        opacity=1
    ).add_to(lineCluster)

async def fetchDatas(route):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + route) as response:
            return await response.json()

def getAssociatedCircuitType(stop, circuits):
    stop_coords = stop['fields']['stop_coordinates']

    return next(
            (circuit['circuit_type'] for circuit in circuits if any(
                abs(circuit_coord[0] - stop_coords[0]) <= 0.002
                and abs(circuit_coord[1] - stop_coords[1]) <= 0.002
                for circuit_coord in circuit['coordinates']
            )),
            'None'
    )

def getStopArray(stop):
    match stop:
        case 'Bus':
            return ['bus', 'busMarkersCluster']
        case 'Tram':
            return ['train-subway', 'tramMarkersCluster']
        case 'Ferry':
            return ['ship', 'ferryMarkersCluster']


if __name__ == "__main__":
    app.run(debug=True)
