

//global vars
let carto_min_date = 0, carto_max_date = 0;
let carto_start_range = 0, carto_end_range = 0;

let default_frq_start = 400;
let default_frq_end = 420;
let default_threshold = -10;

/*
Structure dict modules

modules[module_id].latitude = params["latitude"];
modules[module_id].longitude = params["longitude"];  
modules[module_id].frq_start = params["frq_start"];
modules[module_id].frq_end = params["frq_end"];
modules[module_id].threshold = params["threshold"];
modules[module_id].applied = true;
modules[module_id].last_activity = true;
*/



//initialize
(function() {

  datatable_init();
  carto_init();

  import_detections(init_detections);
  import_modules(init_modules);

  if (Object.keys(modules).length == 0) {
    document.getElementById('config_nb_module').style = 'display: block';
  }  
  //mets les valeurs par défaut dans les champs
  close_config_module();

})();


//helpers

function DateLisible(dateObj)
{
  return dateObj.toLocaleDateString('fr-fr') + ' ' +
        dateObj.toTimeString().substring(0,8);
}

function round(x, nb) {
  return Number.parseFloat(x).toFixed(nb);
}

function date_fr() {
  let dateObj = new Date();
  dateObj.toLocaleDateString('fr-fr') + ' ' + dateObj.toTimeString().substring(0,8);   
}

function date_utc() {
  let dateObj = new Date();
  dateObj.toISOString().replace('T',' ').substring(0,19);
}

function is_undefined(some_var) {
  return (typeof some_var === 'undefined');
}

function pretty_dt(timestamp) {
  return new Date(timestamp).toLocaleString();
}

function get_small_date(timestamp) {

  let str = new Date(timestamp).toLocaleString();
  return str.substring(0,5) + str.substring(10);
}

function pretty_frq(frq) {

  frq = (frq / 1000).toString();
  tab = frq.split('.');
  left = tab[0].padStart(3, '0');
  right = (tab.length == 1) ? "000" : tab[1].substring(0,3).padEnd(3, '0');
  return left + '.' + right + 'M';
}

//end helpers



function import_detections(_detections) {
  
  let data = [];

  //extraction des dates de début/fin
  [min, max] = get_min_max_date(_detections);
  carto_min_date = (carto_min_date < min && carto_min_date != 0) ? carto_min_date : min;
  carto_max_date = (carto_max_date > max && carto_max_date != 0) ? carto_max_date : max;

  //maj du slider
  update_slider_range();

  //parcours des detections
  //module_id, dt, frq, pwr, latitude, longitude
  for (let i = 0; i < _detections.length; i++) {
    let readable_dt = pretty_dt(_detections[i][1]);
    
    //preparation datatable
    data.push([_detections[i][0], readable_dt, _detections[i][2] / 1000, _detections[i][3]])

    //DOM
    add_detection_dom(_detections[i][0], _detections[i][1], _detections[i][2], _detections[i][3]);
  }
  
  //datatable
  datatable_import(data);

  detections = detections.concat(_detections);  
  draw_heatmap(detections);
  bandeau_init(detections);
}



function import_modules(_modules)
{
  //on parcourt les modules insérés dans le template
  for (let i = 0; i < _modules.length; i++)
  {
    //ajout dans l'objet global modules
    let module_id = _modules[i][0];
    let threshold = _modules[i][3];

    if (threshold > 0) threshold = threshold * -1;

    modules[module_id] = {
      'frq_start': _modules[i][1], 'frq_end': _modules[i][2], 'threshold': threshold,
      'latitude': _modules[i][4], 'longitude': _modules[i][5], 
      'last_activity': _modules[i][6], 'config_applied': _modules[i][7]};
    
    //ajout dans le DOM
    add_module_dom(module_id);

    set_module_position(module_id, _modules[i][4], _modules[i][5]);
  }

  //ajout des points dans la carto
  carto_import_modules(modules);
}

function download_csv() {
  location.href = '/download';
}

function reset_db() {
  if (confirm('Remettre à zéro la base de données ?')) {
    send_reset_db();
    setTimeout(function () { location.reload(); }, 750);
  }
}
