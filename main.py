from flask import Flask, render_template_string
import folium
import requests

app = Flask(__name__)


@app.route("/")
def fullscreen():
    row = 100
    url_api_tan = "https://data.nantesmetropole.fr/api/records/1.0/search/?dataset=244400404_tan-arrets&rows=" + str(
        row)

    response = requests.get(url_api_tan)

    if response.status_code == 200:
        data = response.json()
    else:
        print("Erreur lors de la requête : ", response.status_code)
    print(data)

    m = folium.Map(location=[47.2301, -1.5429], zoom_start=13)
    for stop in data['records']:
        if stop['fields']['location_type'] == '1':
            folium.Marker(
                location=stop['fields']['stop_coordinates'],
                popup=stop['fields']['stop_name'],
                icon=folium.Icon(icon="cloud")
            ).add_to(m)

    m.save('index.html')
    return m.get_root().render()


if __name__ == "__main__":
    app.run(debug=True)
