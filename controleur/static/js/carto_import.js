function carto_import_modules(_modules)
{
  for (module_id in _modules)
  {
    draw_point([_modules[module_id].lat, _modules[module_id].lng], module_id);
  }

  //UpdateDrawPoints();
}


function carto_import_detections(_detections)
{
  //extraction des dates de début/fin
  [min, max] = get_min_max_date(_detections);

  carto_min_date = (carto_min_date < min && carto_min_date != 0) ? carto_min_date : min;
  carto_max_date = (carto_max_date > max && carto_max_date != 0) ? carto_max_date : max;
  /*
  let diff = (endDate - carto_min_date) * 0.02;
  startDate -= diff;
  endDate += diff;
  */

  _detections = AttachModuleLocation(modules, _detections);
  detections.concat(_detections)

  update_slider_range();
  bandeau_init(detections);
  
  draw_heatmap(detections);
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



function get_min_max_date(...tab)
{
  let min, max;

  for (let i = 0; i < tab.length; i++)
  {
    for (let j = 0; j < tab[i].length; j++)
    {
      if (typeof min === 'undefined')
      {
        min = tab[i][j].dt;
        max = tab[i][j].dt;
      }

      if (min > tab[i][j].dt) min = tab[i][j].dt;
      if (max < tab[i][j].dt) max = tab[i][j].dt;
    }
  }

  return [min, max];
}
