function AfficherHeatmap(afficher)
{
  dessinerHeatmap = afficher;
  if (afficher) layerControl._layers[1].layer.addTo(map);
  else layerControl._layers[1].layer.removeFrom(map);
}


function DessinerPoint(coordPoint, taille, couleur, gdh, label = '')
{
  var layer = L.circleMarker(coordPoint, {radius: taille, stroke:true, 
      color: '#000000', weight:1, fill: true, fillColor: couleur, fillOpacity: 1}).addTo(map);

  if (label != '')
  {
    layer.bindTooltip(label, {permanent:true, opacity: 0.6, className: 'matooltip'}).openTooltip();
  }

  tabCouchesDessin.push({'layer':layer, 'gdh':gdh, 'shown':true});
}


function DessinerLigne(listeCoord, taille, couleur, gdh)
{
  var layer = L.polyline(listeCoord, {weight: taille, color: couleur}).addTo(map);

  tabCouchesDessin.push({'layer':layer, 'gdh':gdh, 'shown':true});
}


function DessinerSurface(listeCoord, taille, couleur, gdh)
{
  var layer = L.polygon(listeCoord, {weight: taille, color: couleur}).addTo(map);

  tabCouchesDessin.push({'layer':layer, 'gdh':gdh, 'shown':true});
}


function MajDessin()
{
  for (var i = 0; i < tabCouchesDessin.length; i++)
  {
    if (tabCouchesDessin[i].gdh >= startSpan && tabCouchesDessin[i].gdh <= endSpan)
    {
      if (!tabCouchesDessin[i].shown)
      {
        tabCouchesDessin[i].layer.addTo(map);
        tabCouchesDessin[i].shown = true;
      }
      
      //if (tabCouchesDessin[i].layer._latlng)
      //  tabPoints.push(tabCouchesDessin[i].layer._latlng);
    }
    else
    {
      if (tabCouchesDessin[i].shown)
      {
        tabCouchesDessin[i].layer.remove();
        tabCouchesDessin[i].shown = false;
      }
    }
  }


  if (dessinerHeatmap)
  {
    var tabPoints = [];

    for (var i = 0; i < tabPointsHeatmap.length; i++)
    {
      if (tabPointsHeatmap[i].gdh >= startSpan && tabPointsHeatmap[i].gdh <= endSpan)
      {
        tabPoints.push(tabPointsHeatmap[i]);
      }
    }

    heatmapLayer.setData({ max: 2, data: tabPoints });
  }
}



function DessinerToile(tabPoints, tabLignes)
{
  for (var i = 0; i < tabLignes.length; i++)
  {
    var c1 = [tabLignes[i].lat1, tabLignes[i].lng1];
    var c2 = [tabLignes[i].lat2, tabLignes[i].lng2];

    DessinerLigne([c1, c2], 3, '#000000');
  }

  for (var i = 0; i < tabPoints.length; i++)
  {
    var sdate = DateLisible(new Date(tabPoints[i].gdh));
    DessinerPoint([tabPoints[i].cibleLat, tabPoints[i].cibleLng], 4, '#FF0000', '<b>' + tabPoints[i].label + '</b><br>' + sdate);
  }
}


function DessinerActivite(drawData)
{
  for (var i = 0; i < drawData.length; i++)
  {
    var coordCible = [drawData[i].cibleLat, drawData[i].cibleLng];
    DessinerPoint(coordCible, 4, drawData[i].couleur, drawData[i].gdh);
  }
}


function DessinerReleves(drawData)
{
  for (var i = 0; i < drawData.length; i++)
  {
    var coordCapteur = [drawData[i].capteurLat, drawData[i].capteurLng];
    var coordCible = [drawData[i].cibleLat, drawData[i].cibleLng];

    if (drawData[i].capteurLat != -99999 && drawData[i].cibleLat != -99999)
      DessinerLigne([coordCapteur, coordCible], 3, drawData[i].couleur, drawData[i].gdh);
    
    if (drawData[i].capteurLat != -99999)
      DessinerPoint(coordCapteur, 4, '#0000FF', drawData[i].gdh);
    
    if (drawData[i].cibleLat != -99999)
      DessinerPoint(coordCible, 4, '#FF0000', drawData[i].gdh);
  }
}


function LatLongToMGRS(Lat, Long)
{ 
  if (Lat < -80) return 'Too far South' ; if (Lat > 84) return 'Too far North' ;
  var c = 1 + Math.floor ((Long+180)/6);
  var e = c*6 - 183 ;
  var k = Lat*Math.PI/180;
  var l = Long*Math.PI/180;
  var m = e*Math.PI/180;
  var n = Math.cos (k);
  var o = 0.006739496819936062*Math.pow (n,2);
  var p = 40680631590769/(6356752.314*Math.sqrt(1 + o));
  var q = Math.tan (k);
  var r = q*q;
  var s = (r*r*r) - Math.pow (q,6);
  var t = l - m;
  var u = 1.0 - r + o;
  var v = 5.0 - r + 9*o + 4.0*(o*o);
  var w = 5.0 - 18.0*r + (r*r) + 14.0*o - 58.0*r*o;
  var x = 61.0 - 58.0*r + (r*r) + 270.0*o - 330.0*r*o;
  var y = 61.0 - 479.0*r + 179.0*(r*r) - (r*r*r);
  var z = 1385.0 - 3111.0*r + 543.0*(r*r) - (r*r*r);
  var aa = p*n*t + (p/6.0*Math.pow (n,3)*u*Math.pow (t,3)) + (p/120.0*Math.pow (n,5)*w*Math.pow (t,5)) + (p/5040.0*Math.pow (n,7)*y*Math.pow (t,7));
  var ab = 6367449.14570093*(k - (0.00251882794504*Math.sin (2*k)) + (0.00000264354112*Math.sin (4*k)) - (0.00000000345262*Math.sin (6*k)) + (0.000000000004892*Math.sin (8*k))) + (q/2.0*p*Math.pow (n,2)*Math.pow (t,2)) + (q/24.0*p*Math.pow (n,4)*v*Math.pow (t,4)) + (q/720.0*p*Math.pow (n,6)*x*Math.pow (t,6)) + (q/40320.0*p*Math.pow (n,8)*z*Math.pow (t,8));
  aa = aa*0.9996 + 500000.0;
  ab = ab*0.9996; if (ab < 0.0) ab += 10000000.0;
  var ad = 'CDEFGHJKLMNPQRSTUVWXX'.charAt (Math.floor (Lat/8 + 10));
  var ae = Math.floor (aa/100000);
  var af = ['ABCDEFGH','JKLMNPQR','STUVWXYZ'][(c-1)%3].charAt (ae-1);
  var ag = Math.floor (ab/100000)%20;
  var ah = ['ABCDEFGHJKLMNPQRSTUV','FGHJKLMNPQRSTUVABCDE'][(c-1)%2].charAt (ag);
  function pad (val) {if (val < 10) {val = '0000' + val} else if (val < 100) {val = '000' + val} else if (val < 1000) {val = '00' + val} else if (val < 10000) {val = '0' + val};return val};
  
  var precision = false;

  if (precision)
  {
    aa = Math.toFixed(aa%100000,3); 
    ab = Math.toFixed(ab%100000,3);
  }
  else
  {
    aa = Math.floor(aa%100000); 
    ab = Math.floor(ab%100000);     
  }
  
  aa = pad(aa);
  ab = pad(ab);
  
  return c + ad + af + ah + ' ' + aa + ' ' + ab;
}