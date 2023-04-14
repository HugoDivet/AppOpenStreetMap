import folium
import requests

row = 1000
row_circuit = 106
url_api_tan = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows=" + str(row)
url_api_tan_circuit = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-circuits&rows=" + str(row_circuit)
response = requests.get(url_api_tan)
response_circuit = requests.get(url_api_tan_circuit)

if response.status_code == 200:
    data = response.json()
else:
    print("Erreur lors de la requête : ", response.status_code)
if response_circuit.status_code == 200:
    data_circuit = response_circuit.json()
else:
    print("Erreur lors de la requête circuit : ", response_circuit.status_code)
# print(data)

route_type = {}
route_color = {}
for stop in data['records']:
    if stop['fields']['location_type'] == '1':
        coords = stop['fields']['stop_coordinates']
        coords_inverse = [coords[1],coords[0]]
        for circuit in data_circuit['records']:
            for route in circuit['fields']['shape']['coordinates']:
                if route.count(coords_inverse) > 0:
                    route_type[stop['fields']['stop_id']] = circuit['fields']['route_type']
                    route_color[stop['fields']['stop_id']] = circuit['fields']['route_color']
print(route_color)
m = folium.Map(location=[47.2301,-1.5429], zoom_start=13)
for stop in data['records']:
    icon = "question"
    color = "black"
    if stop['fields']['location_type'] == '1':
        if stop['fields']['stop_id'] in route_type:
            if route_type[stop['fields']['stop_id']] == "Bus":
                icon = "bus"
                color = "red"
            elif route_type[stop['fields']['stop_id']] == "Tram":
                icon = "train-tram"
                color = "green"
            else:
                icon = "ferry"
                color = "blue"
        folium.Marker(
            location=stop['fields']['stop_coordinates'],
            popup=stop['fields']['stop_name'],
            icon=folium.Icon(icon=icon,prefix="fa",color=color),

        ).add_to(m)

m.save('index.html')
