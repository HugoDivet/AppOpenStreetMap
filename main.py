import httpx
from flask import Flask
import folium
from folium.plugins import MarkerCluster
from flask_caching import Cache

API_URL = "http://127.0.0.1:8000/"

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple"})

@app.route("/")
@cache.cached(timeout=3600)
async def tan_map():
    # add ?skip=X&limit=X to add or remove some stops
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL + "arrets")
        stops = response.json()

    m = folium.Map(location=[47.2301, -1.5429], zoom_start=13)

    marker_cluster = MarkerCluster(name='Markers').add_to(m)

    for stop in stops:
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

    folium.LayerControl().add_to(m)

    m.save('index.html')
    return m.get_root().render()

if __name__ == "__main__":
    app.run(debug=True)
