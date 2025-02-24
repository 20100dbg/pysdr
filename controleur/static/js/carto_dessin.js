function draw_point(coordPoint, data = {}, taille = 4, couleur = "#000000")
{

  let layer = L.circleMarker(coordPoint, {
      data: data, radius: taille, stroke:true, 
      color: couleur, weight:1, fill: true, 
      fillColor: couleur, fillOpacity: 1}).addTo(map).on('click', on_click_module);
  return layer;
}

function add_tooltip(layer, label, timeout=0) {
  
  layer.bindTooltip(label.toString(), {permanent:true, opacity: 0.6, className: 'tooltip'}).openTooltip();

  if (timeout > 0) {
    setTimeout(function () {
      layer.closeTooltip();
    }, timeout * 1000);
  }
}


function get_module_layer(module_id) {
  for (var i = 0; i < modules_layers.length; i++) {
    if (modules_layers[i].options.data.module_id == module_id)
      return modules_layers[i];
  }
  return null;
}


function show_heatmap(show)
{
  if (show) layerControl._layers[1].layer.addTo(map);
  else layerControl._layers[1].layer.removeFrom(map);
}

function draw_heatmap(tabPointsHeatmap)
{
  var tabPoints = [];

  for (var i = 0; i < tabPointsHeatmap.length; i++)
  {
    if (tabPointsHeatmap[i].dt >= carto_start_range && tabPointsHeatmap[i].dt <= carto_end_range)
    {
      tabPoints.push(tabPointsHeatmap[i]);
    }
  }
  maxCount = 2;
  maxCount = detections.length;

  heatmapLayer.setData({ max: maxCount, data: tabPoints });
}


function UpdateDrawPoints(points)
{
  /*
  for (let i = 0; i < tabCouchesDessin.length; i++) {
    if (tabCouchesDessin[i].dt >= carto_start_range && tabCouchesDessin[i].dt <= carto_end_range) {
      if (!tabCouchesDessin[i].shown) {
        tabCouchesDessin[i].layer.addTo(map);
        tabCouchesDessin[i].shown = true;
      }
    }
    else {
      if (tabCouchesDessin[i].shown) {
        tabCouchesDessin[i].layer.remove();
        tabCouchesDessin[i].shown = false;
      }
    }
  }
  */
}


function LatLongToMGRS(Lat, Long)
{ 
  if (Lat < -80) return 'Too far South' ; if (Lat > 84) return 'Too far North' ;
  let c = 1 + Math.floor ((Long+180)/6);
  let e = c*6 - 183 ;
  let k = Lat*Math.PI/180;
  let l = Long*Math.PI/180;
  let m = e*Math.PI/180;
  let n = Math.cos (k);
  let o = 0.006739496819936062*Math.pow (n,2);
  let p = 40680631590769/(6356752.314*Math.sqrt(1 + o));
  let q = Math.tan (k);
  let r = q*q;
  let s = (r*r*r) - Math.pow (q,6);
  let t = l - m;
  let u = 1.0 - r + o;
  let v = 5.0 - r + 9*o + 4.0*(o*o);
  let w = 5.0 - 18.0*r + (r*r) + 14.0*o - 58.0*r*o;
  let x = 61.0 - 58.0*r + (r*r) + 270.0*o - 330.0*r*o;
  let y = 61.0 - 479.0*r + 179.0*(r*r) - (r*r*r);
  let z = 1385.0 - 3111.0*r + 543.0*(r*r) - (r*r*r);
  let aa = p*n*t + (p/6.0*Math.pow (n,3)*u*Math.pow (t,3)) + (p/120.0*Math.pow (n,5)*w*Math.pow (t,5)) + (p/5040.0*Math.pow (n,7)*y*Math.pow (t,7));
  let ab = 6367449.14570093*(k - (0.00251882794504*Math.sin (2*k)) + (0.00000264354112*Math.sin (4*k)) - (0.00000000345262*Math.sin (6*k)) + (0.000000000004892*Math.sin (8*k))) + (q/2.0*p*Math.pow (n,2)*Math.pow (t,2)) + (q/24.0*p*Math.pow (n,4)*v*Math.pow (t,4)) + (q/720.0*p*Math.pow (n,6)*x*Math.pow (t,6)) + (q/40320.0*p*Math.pow (n,8)*z*Math.pow (t,8));
  aa = aa*0.9996 + 500000.0;
  ab = ab*0.9996; if (ab < 0.0) ab += 10000000.0;
  let ad = 'CDEFGHJKLMNPQRSTUVWXX'.charAt (Math.floor (Lat/8 + 10));
  let ae = Math.floor (aa/100000);
  let af = ['ABCDEFGH','JKLMNPQR','STUVWXYZ'][(c-1)%3].charAt (ae-1);
  let ag = Math.floor (ab/100000)%20;
  let ah = ['ABCDEFGHJKLMNPQRSTUV','FGHJKLMNPQRSTUVABCDE'][(c-1)%2].charAt (ag);
  function pad (val) {if (val < 10) {val = '0000' + val} else if (val < 100) {val = '000' + val} else if (val < 1000) {val = '00' + val} else if (val < 10000) {val = '0' + val};return val};
  
  let precision = false;

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