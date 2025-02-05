var map, heatmapLayer;
var tabCouchesDessin = [];
var tabPointsHeatmap = [];
var layerControl;

var startDate = 0, endDate = 0;
var startSpan = 0, endSpan = 0;

var sliderSpanInit = 100;
var sliderSpan = sliderSpanInit;

var coucheZone = "";
var boxZone = "";
var typeCoord = "mgrs";
var blockCoordMouse = false;

var dessinerHeatmap = false;

/*
 // radius should be small ONLY if scaleRadius is true (or small radius is intended)
  // if scaleRadius is false it will be the constant radius used in pixels
  "radius": 2,
  "maxOpacity": .8,
  // scales the radius based on map zoom
  "scaleRadius": true,
  */

var heatmapcfg = {
  "radius": 30,
  "maxOpacity": .7,
  "scaleRadius": false,
  "useLocalExtrema": false,
  "pane" : "heatmap",
  latField: 'lat', lngField: 'lng', valueField: 'count'
};

function resizeWindow()
{
  var largeur = window.innerWidth - 20;
  document.getElementById("fromSlider").style.width = largeur + 'px';
  document.getElementById("toSlider").style.width = largeur + 'px';

  CreerBandeau(largeur);
}

window.onresize = function() {
  resizeWindow();
}

window.onload = function() {

  resizeWindow();

  var URL_CARTO = "../tiles"; //dossier local
  //var URL_CARTO = "https://{s}.tile.openstreetmap.org"; //carto online
  
  var baseLayer = L.tileLayer(URL_CARTO + '/{z}/{x}/{y}.png', { });
  
  heatmapLayer = new HeatmapOverlay(heatmapcfg);

  map = new L.Map('map', {
    editable: true,
    center: {lat:48, lng:8},
    zoom: 4,
    layers: [baseLayer]
  });
  
  map.createPane('heatmap');
  map.getPane('heatmap').style.zIndex = 650;

  layerControl = L.control.layers({'Fond carto': baseLayer }).addTo(map);
  AjouterCoucheGroupe([heatmapLayer], 'Carte de chaleur');

  map.pm.setLang('fr');
  map.pm.addControls({ position: 'topleft', drawMarker: false,drawCircleMarker: false,
    drawPolyline: false,drawText: false,cutPolygon: false, rotateMode: false,
    drawPolygon:false, drawCircle:false, editMode:false, removalMode: false, dragMode:false });

  map.pm.Toolbar.createCustomControl(
    { name: "moveZone", block: "edit", className: "control-icon leaflet-pm-icon-drag", 
    title: "Déplacer la zone", 
    onClick: () => { if (coucheZone) coucheZone.pm.enableLayerDrag(); } });

  map.pm.Toolbar.createCustomControl(
    { name: "deleteZone", block: "edit", className: "control-icon leaflet-pm-icon-delete", 
    title: "Effacer la zone", 
    onClick: () => { SupprimerZone(); } });

  map.pm.Toolbar.createCustomControl(
    { name: "zoomTo", block: "custom", className: "control-icon leaflet-pm-icon-zoomto", 
    title: "Centrer sur les vecteurs", 
    onClick: () => {
        CentrerVueCouchesDessin();
     } });


  map.pm.Toolbar.createCustomControl(
    { name: "validerZone", block: "edit", className: "control-icon leaflet-pm-icon-valider", 
    title: "Valider la zone", 
    onClick: (e) => { 
      if (e && !map.pm.Toolbar.buttons.validerZone._button.disabled) { EnvoyerZone(); }
      }});

  map.pm.Toolbar.setButtonDisabled("validerZone", true);

  //mise à jour du zoom
  map.on('zoomend', function (e) { 
    document.querySelector('.leaflet-control-coordinates-zoom').innerHTML = " <strong>z:</strong> " + map._zoom; 
  });

  //coordonnées
  var objCoord = new L.Control.Coordinates({position:'bottomright'});
  objCoord.addTo(map);
  map.on('mousemove', function (e) { if (!blockCoordMouse) objCoord.setCoordinates(e, true); });

  //échelle
  L.control.scale({imperial:false}).addTo(map);

  //détection du clic
  map.on('click', function (e) { blockCoordMouse = !blockCoordMouse; });

  //minimap
  var map2 = new L.TileLayer(URL_CARTO + '/{z}/{x}/{y}.png', { minZoom: 0, maxZoom: 12 });
  var miniMap = new L.Control.MiniMap(map2, { zoomLevelOffset: -5, toggleDisplay: true, width:100, height:100 }).addTo(map);



  //Events dessin de la zone de recherche
  map.on('pm:drawstart', (e) => { 
    if (coucheZone) { SupprimerZone(); }
    map.pm.Toolbar.setButtonDisabled("validerZone", false);
  });
  
  //map.on('pm:remove', (e) => { });

  map.on('pm:create', (e) => {
    coucheZone = e.layer;

    //coucheZone.on('pm:change', (e) => { SauvegarderZone(); });
  });
};