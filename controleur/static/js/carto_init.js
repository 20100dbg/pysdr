let map, heatmapLayer;
let modules_layers = [];
let master_layer = null;

//current slider width in percent. Is modified elsewhere
let sliderSpan = 100;
let carto_coord_type = "latlng";

let heatmapcfg = {
  "radius": 30,
  "maxOpacity": .7,
  "scaleRadius": false,
  "useLocalExtrema": false,
  "pane" : "heatmap",
  latField: 'latitude', lngField: 'longitude', valueField: 'count'
};

let available_zooms = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15];
let start_point = [48.8, 7.84];
let start_zoom = 8;



function get_windows_width() {
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
  
  var baseLayer = L.tileLayer(URL_CARTO + '/{z}/{x}/{y}.png', { 
    nativeZooms: available_zooms });
  heatmapLayer = new HeatmapOverlay(heatmapcfg);

  
  map = new L.Map('map', {
    editable: true,
    //center: {lat:48.8, lng:7.84},
    //center: {lat:, lng:4.49},
    //zoom: 8,
    minZoom: 1,
    layers: [baseLayer]
  }).setView(start_point, start_zoom);
  

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
  });

  map.on('click', function (e) { 
    console.log("click event on map");
  });

  resizeWindow();
}