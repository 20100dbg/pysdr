function Import(tabPoints, tabLignes)
{
  //RaZ de la vue, des tableaux, du bandeau et des sliders
  ToutVider();
  
  tabPoints = eval(tabPoints); //{lat, lng, gdh, couleur, label, count}
  tabLignes = eval(tabLignes); //{lat1, lng1, lat2, lng2, couleur, label, count}

  //extraction des dates de début/fin
  [startDate, endDate] = GetMinMaxDate2(tabPoints, tabLignes, []);

  //élargissement fictif de la fenêtre pour un résultat plus lisible
  var diff = (endDate - startDate) * 0.02;
  startDate -= diff;
  endDate += diff;

  //dessin
  for (var i = 0; i < tabLignes.length; i++)
  { DessinerLigne([[tabLignes[i].lat1, tabLignes[i].lng1], [tabLignes[i].lat2, tabLignes[i].lng2]], 
    4, tabLignes[i].couleur, tabLignes[i].gdh); }
  
  for (var i = 0; i < tabPoints.length; i++)
  { DessinerPoint([tabPoints[i].lat, tabPoints[i].lng], 4, tabPoints[i].couleur, tabPoints[i].gdh, tabPoints[i].label); }

  ResetSlider();
  MajPeriode();
  resizeWindow(); //resize window redessine le bandeau


  AfficherHeatmap(true);
  MajDessin();
}

function ImportAjout(tabPoints, tabLignes)
{
  tabPoints = eval(tabPoints); //{lat, lng, gdh, couleur, label, count}
  tabLignes = eval(tabLignes); //{lat1, lng1, lat2, lng2, couleur, label, count}

  //extraction des dates de début/fin
  [min, max] = GetMinMaxDate2(tabPoints, tabLignes, []);

  startDate = (startDate < min) ? startDate : min;
  endDate = (endDate > max) ? endDate : max;

  //dessin
  for (var i = 0; i < tabLignes.length; i++)
  { DessinerLigne([[tabLignes[i].lat1, tabLignes[i].lng1], [tabLignes[i].lat2, tabLignes[i].lng2]], 
    4, tabLignes[i].couleur, tabLignes[i].gdh); }
  
  for (var i = 0; i < tabPoints.length; i++)
  { DessinerPoint([tabPoints[i].lat, tabPoints[i].lng], 4, tabPoints[i].couleur, tabPoints[i].gdh, tabPoints[i].label); }

  resizeWindow(); //resize window redessine le bandeau
  MajDessin();
}

function ImportHeatmap(tabPoints)
{
  tabPointsHeatmap = eval(tabPoints);
  AfficherHeatmap(true);

  MajDessin();
}


function TraiterImport(importedData)
{
    importedData.sort((a, b) => { return a.gdh > b.gdh || -(a.gdh < b.gdh) });
    
    //normalement GetMinMaxDate est inutile, le tableau est trié
    [startDate, endDate] = GetMinMaxDate(importedData);

    var diff = (endDate - startDate) * 0.02;
    startDate -= diff;
    endDate += diff;
}

function ImportKML(filename, kml)
{
  kml = atob(kml);
  const parser = new DOMParser();
  kml = parser.parseFromString(kml, 'text/xml');
  const track = new L.KML(kml);
  //var couche = map.addLayer(track);

  AjouterCoucheGroupe([track], 'Import ' + filename);

  //cocher l'import par défaut
  layerControl._layers[layerControl._layers.length - 1].layer.addTo(map)
}


function ImportSelection(data, nomSelection)
{
  data = eval(data);
  data.sort((a, b) => { return a.gdh > b.gdh || -(a.gdh < b.gdh) });
  //data = FiltrePeriode(data);
  var tabCouches = [];

  for (var i = 0; i < data.length; i++)
  {
    var coordCapteur = [data[i].capteurLat, data[i].capteurLng];
    var coordCible = [data[i].cibleLat, data[i].cibleLng];

    if (data[i].cibleLat != -99999 && data[i].capteurLat != -99999)
      tabCouches.push(L.polyline([coordCapteur, coordCible], {weight: 3, color: data[i].couleur}));

    if (data[i].capteurLat != -99999)
      tabCouches.push(L.circleMarker(coordCapteur, {radius: 4, stroke:true, 
          color: '#000000', weight:1, fill: true, fillColor: '#0000FF', fillOpacity: 1}));

    if (data[i].cibleLat != -99999)
      tabCouches.push(L.circleMarker(coordCible, {radius: 4, stroke:true, 
          color: '#000000', weight:1, fill: true, fillColor: '#FF0000', fillOpacity: 1}));
  }

  AjouterCoucheGroupe(tabCouches, nomSelection);
}

function GetMinMaxDate2(...tab)
{
  var min, max;

  for (var i = 0; i < tab.length; i++)
  {
    for (var j = 0; j < tab[i].length; j++)
    {
      if (typeof min === 'undefined')
      {
        min = tab[i][j].gdh;
        max = tab[i][j].gdh;
      }

      if (min > tab[i][j].gdh) min = tab[i][j].gdh;
      if (max < tab[i][j].gdh) max = tab[i][j].gdh;
    }
  }

  return [min, max];
}


function GetMinMaxDate(tab)
{
  var min = tab[0].gdh;
  var max = tab[0].gdh;

  for (var i = 1; i < tab.length; i++)
  {
    if (min > tab[i].gdh) min = tab[i].gdh;
    if (max < tab[i].gdh) max = tab[i].gdh;
  }

  return [min, max];
}