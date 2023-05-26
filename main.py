import asyncio
import aiohttp
import folium
from flask import Flask
from folium import Tooltip
from folium.plugins import FastMarkerCluster
from clusters import cluster_options

API_URL = "http://127.0.0.1:8000/"

app = Flask(__name__)

@app.route("/")
async def tan_map():

    circuits = await fetchDatas('circuit')
    stops = await fetchDatas('arret')

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
    dict = {}
    stopsTasks = [processStop(stop, circuits, m, busMarkersCluster, tramMarkersCluster, ferryMarkersCluster, dict) for stop in stops]
    circuitsTasks = [processCircuit(circuit, m, busLineCluster, tramLineCluster, ferryLineCluster) for circuit in circuits]

    await asyncio.gather(*stopsTasks, *circuitsTasks)

    create_legend(m)
    folium.LayerControl().add_to(m)
    m.save('index.html')

    return m.get_root().render()

async def processStop(stop, circuits, m, busmarkerscluster, trammarkerscluster, ferrymarkerscluster, dict):

    popup = ""

    if stop is not None and 'type' in stop:

        if stop['parent_id'] not in dict:
            dict[stop['parent_id']] = {}
        if stop['type'] not in dict[stop['parent_id']]:
            stop_name = stop['name']
            dict[stop['parent_id']][stop['type']] = [True]

            if stop['wheelchaired']:
                popup = "<i class='fa-sharp fa-solid fa-wheelchair-move' style='font-size: 24px;'></i><br><br>"
                if stop_name == 'Ile de Nantes':
                    image_url = "/static/IleDeNantes.png"
                    popup += f"<br><br><img src='{image_url}' alt='Photo de l'arrêt' width='300' height='168'>"

            markerCluster, color, icon = getMarkerCluster(stop['type'], busmarkerscluster, trammarkerscluster, ferrymarkerscluster)
            correspondences = await createCorrespondences(stop)
            folium.map.Tooltip(stop_name)
            folium.Marker(
                location=stop['coordinate'],
                popup=folium.Popup(f"<h5 style='white-space: nowrap;overflow: hidden;text-overflow: ellipsis;'>"
                                   f"<b>{stop_name}</b></h5><br><br>" + popup + "<br>" + correspondences, max_width='auto'),
                tooltip=stop_name,
                icon=folium.Icon(color, icon=icon, prefix="fa"),
            ).add_to(markerCluster)

async def processCircuit(circuit, m, buslinecluster, tramlinecluster, ferrylinecluster):

    if circuit is not None:

        circuit_name = circuit['circuit_name']
        circuit_color = circuit['circuit_color']

        text_color = "#000000" if circuit_color == "#ffffff" else "#ffffff"
        popup = f"<h4 style='white-space: nowrap;'>Numéro de la ligne : <span><b><div style='display:inline-block;background-color:{circuit_color};color:{text_color};" \
            f"padding:5px;border-radius:5px;'>{circuit_name}</div></b></span></h4><br>"

        if circuit['circuit_type'] == 'Bus':
            lineCluster = buslinecluster
            popup += "<i class='fa-sharp fa-solid fa-bus' style='font-size: 24px;'></i><br><br>"
        elif circuit['circuit_type'] == 'Tram':
            lineCluster = tramlinecluster
            popup += "<i class='fa-sharp fa-solid fa-train-tram' style='font-size: 24px;'></i><br><br>"
        elif circuit['circuit_type'] == 'Ferry':
            lineCluster = ferrylinecluster
            popup += "<i class='fa-sharp fa-solid fa-ship' style='font-size: 24px;'></i><br><br>"

        line = folium.PolyLine(
            locations=circuit['coordinates'],
            color=circuit['circuit_color'],
            weight=4,
            opacity=1
        ).add_to(lineCluster)

        line.add_child(Tooltip(popup))


async def fetchDatas(route):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL + route) as response:
            return await response.json()

def getMarkerCluster(type, busmarkerscluster, trammarkerscluster, ferrymarkerscluster):
    if type == 'Bus':
        return busmarkerscluster, 'blue', 'bus'
    elif type == 'Tram':
        return trammarkerscluster, 'green', 'train-tram'
    elif type == 'Ferry':
        return ferrymarkerscluster, 'red', 'ship'

def create_legend(m):
    legend_html = """
            <div class="card legend-card" style="position: absolute; bottom: 20px; right: 20px; z-index: 1000;">
                <div class="card-header">
                    <h5 class="card-title" style="margin-bottom: 0;">
                        Légende :
                        <span class="legend-toggle" style="cursor: pointer;float: right;"><i class="fas fa-minus"></i></span>
                    </h5>
                </div>
                <div class="card-body" style="display: block;">
                    <div class="legend">
                        <div>
                            <i class="fa fa-bus" style="color: blue;"></i>
                            <span>Arrêts de bus</span>
                        </div>
                        <div>
                            <i class="fa fa-train-tram" style="color: green;"></i>
                            <span>Arrêts de tram</span>
                        </div>
                        <div>
                            <i class="fa fa-ship" style="color: red;"></i>
                            <span>Arrêts de navibus</span>
                        </div>
                    </div>
                </div>
            </div>
        """

    # Add the legend to the map
    folium.Element(legend_html).add_to(m.get_root().html)

    # Add JavaScript code to toggle legend visibility
    javascript = """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                var toggleElement = document.querySelector('.legend-toggle');
                var legendBody = document.querySelector('.legend-card .card-body');

                toggleElement.addEventListener('click', function() {
                    if (legendBody.style.display === 'none') {
                        legendBody.style.display = 'block';
                        toggleElement.innerHTML = '<i class="fas fa-minus"></i>';
                    } else {
                        legendBody.style.display = 'none';
                        toggleElement.innerHTML = '<i class="fas fa-plus"></i>';
                    }
                });
            });
            </script>
        """

    # Add the JavaScript code to the map
    m.get_root().html.add_child(folium.Element(javascript))

async def createCorrespondences(stop):
    popup_content = """
    <h4>Lignes :</p>
    <table>
        <tr>
            {correspondences}
        </tr>
    </table>
    """
    correspondence_list = "<td style='vertical-align:top'><ul style='list-style:none;'>"
    ligne_list = ""

    for i, correspondence in enumerate(stop['correspondences'], 1):
        line_color = correspondence['color']
        line_name = correspondence['name']
        text_color = "#000000" if line_color == "#ffffff" else "#ffffff"
        square_html = f"<div>"
        square_html += f"<div style='display: flex; align-items: center; justify-content: center; width: 55px; height: 40px; background-color: {line_color};'><span style='font-weight: bold; color:{text_color};'>{line_name}</span></div>"
        square_html += "</div>"
        correspondence_html = f"<li style='margin-bottom: 5px;'>{square_html}</li>"
        ligne_list += correspondence_html

        if i % 3 == 0 or i == len(stop['correspondences']):
            correspondence_list += ligne_list
            ligne_list = ""
            if i != len(stop['correspondences']):
                correspondence_list += "</ul></td><td style='vertical-align:top'><ul style='list-style:none;'>"
    correspondence_list += "</ul></td>"


    popup_content = popup_content.format(correspondences=correspondence_list)

    return popup_content

if __name__ == "__main__":
    app.run(debug=True)
