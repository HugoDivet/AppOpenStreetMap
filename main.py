import requests
import folium

row = 1000
url_api_tan = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows=" + str(row)

response = requests.get(url_api_tan)

if response.status_code == 200:
    data = response.json()
else:
    print("Erreur lors de la requête : ", response.status_code)
#print(data)
m = folium.Map(location=[47.2301, -1.5429], zoom_start=13)

wheelChairs = {}

for stopChilds in data['records']:
    if stopChilds['fields']['location_type'] == '0':
        accessNumber = int(stopChilds['fields']['wheelchair_boarding'])
        if accessNumber >= 1:
            wheelChairs[stopChilds['fields']['parent_station']] = True

for stop in data['records']:
    popup = ""
    if stop['fields']['location_type'] == '1':
        if stop['fields']['stop_id'] in wheelChairs:
            popup = "<i class='fa-sharp fa-solid fa-wheelchair-move'></i>"

        folium.map.Tooltip(stop['fields']['stop_name'])
        folium.Marker(
            location=stop['fields']['stop_coordinates'],
            popup=f"<b>{stop['fields']['stop_name']}</b><br><br>" + popup,
            tooltip=stop['fields']['stop_name'],
            icon=folium.Icon(icon="train-subway", prefix="fa")
        ).add_to(m)

m.save('index.html')
