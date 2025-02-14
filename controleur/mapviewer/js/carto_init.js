let map, heatmapLayer;
let tabCouchesDessin = [];

let startDate = 0, endDate = 0;
let startSpan = 0, endSpan = 0;
let sliderSpan = 100;

let typeCoord = "mgrs";


////////
let modules = {
  '1': {'lat':48.88888, 'lng': 7.90017},
  '2': {'lat':48.89113, 'lng': 7.96126},
  '3': {'lat':48.88594, 'lng': 7.99696}
};

let detections = [
  {'module_id': 1, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557211000 },
  {'module_id': 2, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557222000 },
  {'module_id': 3, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557233000 },
  {'module_id': 2, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557242000 },
  {'module_id': 2, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557244000 },
  {'module_id': 2, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557246000 },
  {'module_id': 2, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557248000 },
  {'module_id': 1, 'frq': 415.5, 'pwr': -20, 'gdh': 1739557255000 }
];

function zou() {
  ImportModules(modules);
  ImportDetections(detections);
}



var heatmapcfg = {
  "radius": 30,
  "maxOpacity": .7,
  "scaleRadius": false,
  "useLocalExtrema": false,
  "pane" : "heatmap",
  latField: 'lat', lngField: 'lng', valueField: 'count'
};


/////////


function resizeWindow()
{
  var largeur = window.innerWidth - 20;
  document.getElementById("fromSlider").style.width = largeur + 'px';
  document.getElementById("toSlider").style.width = largeur + 'px';
  InitBandeau(largeur);
  FillBandeau(detections);
}

window.onresize = function() { resizeWindow(); }

window.onload = function() {

  resizeWindow();


  //var URL_CARTO = "../tiles"; //dossier local
  var URL_CARTO = "https://{s}.tile.openstreetmap.org"; //carto online
  
  var baseLayer = L.tileLayer(URL_CARTO + '/{z}/{x}/{y}.png', { });
  heatmapLayer = new HeatmapOverlay(heatmapcfg);

  
  map = new L.Map('map', {
    editable: true,
    center: {lat:48.87420, lng:8},
    zoom: 12,
    layers: [baseLayer]
  });
  

  let layerControl = L.control.layers({'Fond carto': baseLayer }).addTo(map);
  layerControl.addOverlay(L.layerGroup([heatmapLayer]), 'Carte de chaleur');
  layerControl._layers[1].layer.addTo(map);

  //mise à jour du zoom
  map.on('zoomend', function (e) { 
    document.querySelector('.leaflet-control-coordinates-zoom').innerHTML = " <strong>z:</strong> " + map._zoom; 
  });

  //coordonnées
  var objCoord = new L.Control.Coordinates({position:'bottomright'});
  objCoord.addTo(map);
  map.on('mousemove', function (e) { objCoord.setCoordinates(e, true); });

  //échelle
  L.control.scale({imperial:false}).addTo(map);

  //détection du clic
  map.on('contextmenu', function (e) { 
    console.log(e.latlng);
    //LatLongToMGRS(obj.latlng.lat, obj.latlng.lng);
  });


};