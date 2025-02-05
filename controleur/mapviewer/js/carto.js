
function AjouterCoucheGroupe(tabCouche, nom)
{
  layerControl.addOverlay(L.layerGroup(tabCouche), nom);
}

function SupprimerCouchesDessin()
{
    for (var i = 0; i < tabCouchesDessin.length; i++) tabCouchesDessin[i].layer.remove();
    tabCouchesDessin = [];
}

function ToutVider()
{
  AfficherHeatmap(false);
  SupprimerCouchesDessin();
  ViderBandeau();
  
  tabCouchesDessin = [];
  tabPointsHeatmap = [];
}

function ChangerSensibiliteHeatmap(radius)
{
  heatmapcfg.radius = radius;
}

function ChangerTypeCoord(mgrs)
{
  typeCoord = (mgrs) ? 'mgrs' : 'latlong';
}

function PeriodeSelectionnee()
{
  return startSpan+";"+endSpan;
}

function DateLisible(dateObj)
{
  return dateObj.toLocaleDateString('fr-fr') + ' ' +
        dateObj.toTimeString().substring(0,8);      
}


function AfficherInfos(drawData)
{
  document.getElementById('info').innerHTML = 
          DateLisible(new Date(startSpan)) + '<br>' + 
          getSpanLisible((endSpan - startSpan) / 1000) + '<br>' 
          +  drawData.length + '/' + importedData.length;
}

function MapperRelevesTabPoints(tabReleves, capteur, cible)
{
    var tabPoints = [];

    tabReleves.map(x => {
      if (capteur && 'capteurLat' in x && x.capteurLat != -99999) tabPoints.push({lat: x.capteurLat, lng: x.capteurLng});
      if (cible && 'cibleLat' in x && x.cibleLat != -99999) tabPoints.push({lat: x.cibleLat, lng: x.cibleLng});
    });

    return tabPoints;
}

function FindBounds(tabPoints)
{
    var N = -99999, S = 99999, E = -99999, W = 99999;

    for (var i = 0; i < tabPoints.length; i++)
    {
        if (tabPoints[i].lat == -99999 || tabPoints[i].lng == -99999) continue;
        if (N < tabPoints[i].lat) N = tabPoints[i].lat;
        if (S > tabPoints[i].lat) S = tabPoints[i].lat;
        
        if (E < tabPoints[i].lng) E = tabPoints[i].lng;
        if (W > tabPoints[i].lng) W = tabPoints[i].lng;
    }

    if ([N,S,E,W].includes(99999) || [N,S,E,W].includes(-99999)) return [[0,0], [0,0]];
    return [[N, W], [S, E]];
}


function CentrerVueCouchesDessin()
{
  var tabPoints = [];

  for (var i = 0; i < tabCouchesDessin.length; i++)
  {
    if (tabCouchesDessin[i].shown)
    {
      //if (Array.isArray(tabCouchesDessin[i].layer))

      if (typeof tabCouchesDessin[i].layer._latlng !== 'undefined')
      {
        tabPoints.push(tabCouchesDessin[i].layer._latlng);
      }
      else
      {
        for (var j = 0; j < tabCouchesDessin[i].layer._latlngs.length; j++)
        {
          tabPoints.push(tabCouchesDessin[i].layer._latlngs[j]);
        }
      }
    }
  }

  CentrerVue(tabPoints);
}

function CentrerVue(tabPoints)
{
    var b = FindBounds(tabPoints);
    map.fitBounds(b, { maxZoom:12 });
}

function ResetSlider()
{
  fromSlider.value = 0;
  toSlider.value = sliderSpanInit;
  fillSlider(fromSlider, toSlider, '#C6C6C6', '#25daa5', toSlider);
}


//autoplay
var valPlaySlider = 0;
var interval;
var delay = 100;

function Autoplay()
{
  var modeCumul = true;

  var fromSlider = document.getElementById('fromSlider');
  var toSlider = document.getElementById('toSlider');

  valPlaySlider = 0;
  fromSlider.value = 0;
  toSlider.value = 1;

  interval = setInterval(PlaySlider2, delay, modeCumul);
}

function StopAutoplay()
{
  clearInterval(interval);
}

function PlaySlider2(modeCumul)
{
  if (!modeCumul)
  {
    fromSlider.value = valPlaySlider;
    fromSlider.dispatchEvent(new Event('input', { }));
  }
  toSlider.value = valPlaySlider + 1;
  toSlider.dispatchEvent(new Event('input', { }));

  valPlaySlider += 1;
  if (valPlaySlider > 100) StopAutoplay();
}


function StartDrawZone()
{
  map.pm.enableDraw('Rectangle',{ snappable: false });
}

function EnvoyerZone()
{
  boxZone = "";
  var tab = map.pm.getGeomanDrawLayers();
  if (tab.length > 0)
  {
    boxZone = tab[0]._latlngs[0][1].lng + "|" + tab[0]._latlngs[0][1].lat + "|" + tab[0]._latlngs[0][3].lng + "|" + tab[0]._latlngs[0][3].lat;
  }

  map.pm.Toolbar.setButtonDisabled("validerZone", true);
  CefSharp.PostMessage("zone=" + boxZone);
  SupprimerZone();
}

function SupprimerZone()
{
  if (coucheZone) coucheZone.pm.remove();
  boxZone = "";
}