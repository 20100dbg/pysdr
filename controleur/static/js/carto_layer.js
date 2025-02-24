
function on_click_module(e) {
    let module_id = e.target.options.data.module_id;
    let module_layer = get_module_layer(module_id);

    let label = "";
    let nb_detections_max = 3;
    let nb_detections = 0;

    for (let i = 0; i < detections.length; i++) {
      if (detections[i].module_id == module_id && nb_detections++ < nb_detections_max) {
        label += pretty_frq(detections[i].frq) + "<br>";
      }
    }
    add_tooltip(module_layer, label, 5);
}

function SupprimerCouchesDessin()
{
    for (let i = 0; i < tabCouchesDessin.length; i++) tabCouchesDessin[i].layer.remove();
    tabCouchesDessin = [];
}

function ToutVider()
{
  SupprimerCouchesDessin();
  ViderBandeau();
  
  carto_min_date = carto_max_date = 0;
  tabCouchesDessin = [];
}

function ChangerTypeCoord(mgrs)
{
  typeCoord = (mgrs) ? 'mgrs' : 'latlong';
}

/*
function PeriodeSelectionnee()
{
  return startSpan+";"+endSpan;
}
*/


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


function FindBounds(tabPoints)
{
    let N = -99999, S = 99999, E = -99999, W = 99999;

    for (let i = 0; i < tabPoints.length; i++)
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


function CentrerVue(tabPoints)
{
    let b = FindBounds(tabPoints);
    map.fitBounds(b, { maxZoom:12 });
}


function ResetSlider()
{
  fromSlider.value = 0;
  toSlider.value = 100;
  fillSlider(fromSlider, toSlider, '#C6C6C6', '#25daa5', toSlider);
}

