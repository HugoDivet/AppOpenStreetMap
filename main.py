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
    # add ?skip=X&limit=X to add or remove some stops
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + "arret") as response:
            stops = await response.json()

    m = folium.Map(location=[47.2301, -1.5429], zoom_start=13)
    marker_cluster = MarkerCluster(name='Markers').add_to(m)

    tasks = [process_stop(stop, marker_cluster) for stop in stops]
    await asyncio.gather(*tasks)

    folium.LayerControl().add_to(m)

    m.save('index.html')
    return m.get_root().render()

async def process_stop(stop, marker_cluster):
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

if __name__ == "__main__":
    app.run(debug=True)
