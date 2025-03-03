function carto_import_modules(_modules)
{

  for (let i = 0; i < _modules.length; i++)
  {
    if (_modules[i].lat != 0 && _modules[i].lng != 0)
    {
      let layer = draw_point([_modules[i].lat, _modules[i].lng], {"module_id": _modules[i].module_id});
      modules_layers.push(layer);
    }
  }
}


function carto_import_detections(_detections)
{  
  //draw_heatmap(detections);
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
