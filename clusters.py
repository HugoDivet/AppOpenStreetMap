from folium.plugins import FastMarkerCluster

cluster_options = {
    'busMarkersCluster': {
        'name': 'Arrêts de bus',
        'data': [],
        'options': {'disableClusteringAtZoom': 15}
    },
    'tramMarkersCluster': {
        'name': 'Arrêts de tram',
        'data': [],
        'options': {'disableClusteringAtZoom': 13}
    },
    'ferryMarkersCluster': {
        'name': 'Arrêts de navibus',
        'data': []
    },
    'busLineCluster': {
        'name': 'Lignes de bus',
        'data': []
    },
    'tramLineCluster': {
        'name': 'Lignes de tram',
        'data': []
    },
    'ferryLineCluster': {
        'name': 'Lignes de navibus',
        'data': []
    }
}
