function ImportModules(tabPoints)
{
  //dessin
  for (mod in tabPoints) {
    DessinerPoint([tabPoints[mod].lat, tabPoints[mod].lng], mod);
  }

  UpdateDrawPoints();
}


function ImportDetections(tabPoints)
{
  //extraction des dates de début/fin
  [min, max] = GetMinMaxDate2(tabPoints);

  startDate = (startDate < min && startDate != 0) ? startDate : min;
  endDate = (endDate > max && endDate != 0) ? endDate : max;
  let diff = (endDate - startDate) * 0.02;
  startDate -= diff;
  endDate += diff;

  detections = AttachModuleLocation(modules, tabPoints);

  UpdateSliderSelection();
  FillBandeau(detections);
  
  DessinerHeatmap(detections);
}


function AttachModuleLocation(modules, detections)
{
  for (let i = 0; i < detections.length; i++) {
    let module_id = detections[i]['module_id'];
    detections[i]['lat'] = modules[module_id]['lat'];
    detections[i]['lng'] = modules[module_id]['lng'];
    detections[i]['count'] = 1;
  }

  return detections;
}



function GetMinMaxDate2(...tab)
{
  let min, max;

  for (let i = 0; i < tab.length; i++)
  {
    for (let j = 0; j < tab[i].length; j++)
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
