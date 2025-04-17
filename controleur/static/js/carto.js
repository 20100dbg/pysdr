/*** Bandeau ***/

//Must be called whenever user modify the slider range
//update global vars carto_start_range and carto_end_range
function update_slider_range()
{
  const [from, to] = getParsed(fromSlider, toSlider);
  let diff = carto_max_date - carto_min_date;
  
  carto_start_range = Math.round(carto_min_date + from * diff / 100);
  carto_end_range = Math.round(carto_min_date + to * diff / 100);

  document.getElementById('fromSliderTooltip').innerText = DateLisible(new Date(carto_start_range));
  document.getElementById('toSliderTooltip').innerText = DateLisible(new Date(carto_end_range));
}

//init bandeau using timestamp in points array
function bandeau_init(points)
{
  bandeau_empty();
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  c.width = get_windows_width();

  let diff = carto_max_date - carto_min_date;

  for (let i = 0; i < points.length; i++)
  {
    let tmp = diff - (carto_max_date - points[i][1]);
    let x = tmp * c.width / diff;

    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 20);
    ctx.stroke();
  }
}

//empty bandeau
function bandeau_empty()
{
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  ctx.clearRect(0,0,c.width,c.height);
}



/*** Import ***/

function carto_import_modules(_modules)
{
  for (module_id in _modules)
  {
    if (_modules[module_id].latitude != 0 && _modules[module_id].longitude != 0)
    {
      let layer = draw_point([_modules[module_id].latitude, _modules[module_id].longitude], 
                              {"module_id": module_id});
      modules_layers.push(layer);
    }
  }
}



/*** Misc ***/

function center_master() {
  center_view(master_layer._latlng.lat, master_layer._latlng.lng);
}


function center_view(latitude, longitude) {
  let zoom = 8;
  map.setView([latitude, longitude], zoom);
}


function get_min_max_date(...tab)
{
  let min, max;

  for (let i = 0; i < tab.length; i++)
  {
    for (let j = 0; j < tab[i].length; j++)
    {
      if (typeof min === 'undefined') {
        min = tab[i][j][1];
        max = tab[i][j][1];
      }

      if (min > tab[i][j][1]) min = tab[i][j][1];
      if (max < tab[i][j][1]) max = tab[i][j][1];
    }
  }

  return [min, max];
}


/*** Draw ***/


function set_master_position(latitude, longitude) {

  if (master_layer == null) {
    master_layer = draw_point([latitude, longitude], {}, 4, "#0000FF");
  }
  else {
    master_layer.setLatLng([latitude, longitude])

  }
}

//Draw a point
function draw_point(coordPoint, data = {}, taille = 4, couleur = "#000000")
{
  let layer = L.circleMarker(coordPoint, {
      data: data, radius: taille, stroke:true, 
      color: couleur, weight:1, fill: true, 
      fillColor: couleur, fillOpacity: 1}).addTo(map).on('click', on_click_module);
  
  return layer;
}


function add_tooltip(layer, label, timeout=0) {
  
  layer.bindTooltip(label.toString(), {permanent:true, opacity: 0.8, className: 'tooltip'}).openTooltip();

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


//Draw heatmap using _detections array.
function draw_heatmap(_detections)
{
  let data = [];

  for (let i = 0; i < _detections.length; i++)
  {
    if (!is_undefined(_detections[i][4]) && !is_undefined(_detections[i][5]) && 
      _detections[i][4] != 0 && _detections[i][5] != 0 &&
      _detections[i][1] >= carto_start_range && _detections[i][1] <= carto_end_range)
    {
      data.push({'latitude':_detections[i][4], 'longitude':_detections[i][5]});
    }
  }
  //max = 2;
  max = detections.length;

  heatmapLayer.setData({ max: max, data: data });
}



/*** Map management ***/


function on_click_module(e) {
    let module_id = e.target.options.data.module_id;
    let module_layer = get_module_layer(module_id);

    //three last detections
    sorted_detections = detections.filter((row) => row[0] == module_id);
    sorted_detections = sorted_detections.sort((a,b) => (b[1] - a[1]));

    let array_frq = [];
    for (let i = 0; i < sorted_detections.length && array_frq.length < 3; i++) {
        if (!(detections[i][2] in array_frq))
          array_frq.push(pretty_frq(detections[i][2]));
    }

    let label = "C" + module_id.toString() + "<br>" + array_frq.join("<br>");
    add_tooltip(module_layer, label, 5);

    //three more recurrent frq
}


function ChangerTypeCoord(mgrs)
{
  typeCoord = (mgrs) ? 'mgrs' : 'latlong';
}

function find_bounds(points)
{
    let N = -99999, S = 99999, E = -99999, W = 99999;

    for (let i = 0; i < points.length; i++)
    {
        if (points[i].latitude == -99999 || points[i].longitude == -99999) continue;
        if (N < points[i].latitude) N = points[i].latitude;
        if (S > points[i].latitude) S = points[i].latitude;
        
        if (E < points[i].longitude) E = points[i].longitude;
        if (W > points[i].longitude) W = points[i].longitude;
    }

    if ([N,S,E,W].includes(99999) || [N,S,E,W].includes(-99999)) return [[0,0], [0,0]];
    return [[N, W], [S, E]];
}


function center_map_view(points)
{
    let b = find_bounds(points);
    map.fitBounds(b, { maxZoom:12 });
}

