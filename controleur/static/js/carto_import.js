function carto_import_modules(_modules)
{
  for (module_id in _modules)
  {
    if (_modules[module_id].lat != 0 && _modules[module_id].lng != 0)
    {
      let layer = draw_point([_modules[module_id].lat, _modules[module_id].lng], 
                              {"module_id": module_id});
      modules_layers.push(layer);
    }
  }
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
        min = tab[i][j][1];
        max = tab[i][j][1];
      }

      if (min > tab[i][j][1]) min = tab[i][j][1];
      if (max < tab[i][j][1]) max = tab[i][j][1];
    }
  }

  return [min, max];
}
