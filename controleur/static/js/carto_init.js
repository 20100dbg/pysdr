let map, heatmapLayer;
let tabCouchesDessin = [];
let sliderSpan = 100;

let carto_min_date = 0, carto_max_date = 0;
let carto_start_range = 0, carto_end_range = 0;
let carto_coord_type = "mgrs";

let heatmapcfg = {
  "radius": 30,
  "maxOpacity": .7,
  "scaleRadius": false,
  "useLocalExtrema": false,
  "pane" : "heatmap",
  latField: 'lat', lngField: 'lng', valueField: 'count'
};



function get_windows_width() {
  //return 500;
  return window.innerWidth - 30;
}

function resizeWindow()
{
  let largeur = get_windows_width();
  document.getElementById("fromSlider").style.width = largeur + 'px';
  document.getElementById("toSlider").style.width = largeur + 'px';
  bandeau_init(detections);
}

window.onresize = function() { resizeWindow(); }

function carto_init() {

  var URL_CARTO = "../tiles"; //dossier local
  //var URL_CARTO = "https://{s}.tile.openstreetmap.org"; //carto online
  
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

  resizeWindow();
}