const socket = io();
let update_module_position = false;
//helpers

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
  //timestamp = timestamp * 1000;
  return new Date(timestamp).toLocaleString();
}

function pretty_frq(frq) {

  frq = (frq / 1000).toString();
  tab = frq.split('.');
  left = tab[0].padStart(3, '0');
  right = (tab.length == 1) ? "000" : tab[1].substring(0,3).padEnd(3, '0');
  return left + '.' + right + 'M';
}

//helpers

let carto_min_date = 0, carto_max_date = 0;
let carto_start_range = 0, carto_end_range = 0;

let default_frq_start = 400;
let default_frq_end = 420;
let default_threshold = -10;


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
    add_detection_dom(_detections[i][0], readable_dt, _detections[i][2], _detections[i][3]);
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
      'lat': _modules[i][4], 'lng': _modules[i][5], 
      'last_ping': _modules[i][6], 'config_applied': _modules[i][7] };
    
    //ajout dans le DOM
    add_module_dom(module_id);

    set_module_position(module_id, _modules[i][4], _modules[i][5]);
  }

  //ajout des points dans la carto
  carto_import_modules(modules);
}


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




function download_csv() {
  location.href = '/download';
}

function reset_db() {
  if (confirm('Remettre à zéro la base de données ?')) {
    send_reset_db();
    setTimeout(function () { location.reload(); }, 750);
  }
}


//sockets

function send_reset_db() {
  show_loader(0.5);
  socket.emit("reset_db", {});
}

function send_ping(id_module) {
  show_loader();
  socket.emit("ping", id_module);
}

function send_nb_module(nb_module) {
  socket.emit("set_nb_module", nb_module);
}

function send_config_module(module_id, frq_start, frq_end, threshold) {
  show_loader();
  socket.emit("config", {'module_id': module_id, 'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold});
}


socket.on("connect", () => {
  //update_etat(true);
  socket.emit("set_time", Date.now());
});

/*
socket.on("disconnect", () => {
  update_etat(false);
});
*/

socket.on("got_config_ack", function(module_id) {
  modules[module_id]['applied'] = true;
  pop_error("C" + module_id + " configuré");
});

socket.on("got_pong", function(params) {

  let module_id = params["module_id"];
  modules[module_id].lat = params["lat"];
  modules[module_id].lng = params["lng"];
  
  modules[module_id].frq_start = params["frq_start"];
  modules[module_id].frq_end = params["frq_end"];
  modules[module_id].threshold = params["threshold"];
  modules[module_id]['applied'] = true;

  let layer = get_module_layer(module_id);

  if (layer != null && update_module_position) {

    //delete layer from map
    layer.remove();

    //delete layer from array
    let idx = modules_layers.indexOf(layer);
    modules_layers.splice(idx, 1);

    carto_import_modules(modules);
    set_module_position(module_id, params["lat"], params["lng"]);

  }
  else if (layer == null) {
    carto_import_modules(modules);
    set_module_position(module_id, params["lat"], params["lng"]);
  }

  pop_error("C" + module_id + " répond");
});

socket.on("got_frq", function(params) {

  let frq = pretty_frq(params['frq']);
  let module_id = params["module_id"];
  
  if (!(module_id in modules)){
    lat = 0;
    lng = 0;
  }
  else {
    lat = modules[module_id].lat;
    lng = modules[module_id].lng;
  }


  import_detections([[module_id,params['dt'],params['frq'],params['pwr'], lat, lng]]);

  let module_layer = get_module_layer(module_id);

  if (module_layer != null) {
    add_tooltip(module_id.toString() + " : " + module_layer, frq, 5);
  }

  pop_error("C" + module_id + " - " + frq + " / " + params["pwr"]);
});




// interface

function add_detection_dom(module_id, readable_dt, frq, pwr) {

  let log_detections = document.getElementById('log_detections');

  const tpl = document.createElement('template');
  log_row = readable_dt + " - Capteur " + module_id + " - " + pretty_frq(frq) + " - " + pwr;
  tpl.innerHTML = '<span class="log_row">'+ log_row +'</span>'

  log_detections.insertBefore(tpl.content.firstChild, log_detections.firstChild);

  //log_detections.appendChild(tpl.content.firstChild);
  //log_detections.scrollTop = log_detections.scrollHeight;
}



function show_loader(duree = 1) {
    document.getElementById('etat').classList.add('loader');
    document.getElementById('etat').style.animationDuration = duree + 's';
    document.getElementById('etat').style.WebkitAnimationDuration = duree + 's';

    setTimeout(function () {
      document.getElementById('etat').classList.remove('loader');
    }, duree * 1000);
}

function toggle_tab(tabname)
{
  let tabs = ['viewer', 'history', 'modules', 'config'];

  for (let i = 0; i < tabs.length; i++) {
    let div = document.getElementById('tab_' + tabs[i]);

    if (tabs[i] == tabname) div.style.display = 'block';
    else div.style.display = 'none';
  }
}

function update_etat(etat)
{
  let div_etat = document.getElementById('etat');

  if (etat)
  {
    div_etat.classList.remove('red');
    div_etat.classList.add('green');
    div_etat.innerText = "Wifi connecté"
  }
  else
  {
    div_etat.classList.remove('green');
    div_etat.classList.add('red');
    div_etat.innerText = "! Wifi déconnecté !"
  }
}

//gestion module

function set_nb_module()
{
  let nb_module = parseInt(document.getElementById('nb_module').value);
  send_nb_module(nb_module);

  document.getElementById('tab_modules').innerHTML = '';

  for (let module_id = 1; module_id <= nb_module; module_id++) {
    modules[module_id] = {'frq_start': default_frq_start, 'frq_end': default_frq_end, 
                  'latitude': 0, 'longitude': 0,
                  'threshold': default_threshold, 'applied': true};

    add_module_dom(module_id);
  }

  document.getElementById('config_nb_module').style = 'display: none';
}

function set_module_position(module_id, latitude, longitude)
{
  let div = document.getElementById("position-" + module_id);
  div.innerText =  round(latitude, 2) + "/" + round(longitude, 2);
}

function add_module_dom(module_id)
{
  const tpl = document.createElement('template');
  tpl.innerHTML = get_tpl(module_id);

  let container = document.getElementById('tab_modules');
  container.appendChild(tpl.content.firstChild);
}

function get_tpl(module_id)
{
  return '<div class="line">' +
        '<span id="name-'+ module_id +'">Capteur '+ module_id +'</span> - ' +
        '<span id="position-'+ module_id +'">NL</span>' +

        '<span class="buttons">' +
          '<button onclick="send_ping(\''+ module_id +'\');" style="margin-right: 20px">Ping</buton>' +
          '<button onclick="show_config_module(\''+ module_id +'\');">Config</buton>' +
        '</span>' +
      '</div>';
}

//

//config

function show_config_module(module_id) {
  document.getElementById('module_id').value = module_id;
  document.getElementById('config_module').style = 'display: block';

  document.getElementById('frq_start').value = modules[module_id]['frq_start'];
  document.getElementById('frq_end').value = modules[module_id]['frq_end'];
  document.getElementById('threshold').value = modules[module_id]['threshold'];
  document.getElementById('applied').checked = modules[module_id]['applied']; 
}

function save_config_module() {
  let module_id = document.getElementById('module_id').value;
  let frq_start = document.getElementById('frq_start').value;
  let frq_end = document.getElementById('frq_end').value;
  let threshold = document.getElementById('threshold').value;

  modules[module_id]['frq_start'] = frq_start;
  modules[module_id]['frq_end'] = frq_end;
  modules[module_id]['threshold'] = threshold;
  modules[module_id]['applied'] = false;

  send_config_module(module_id, frq_start, frq_end, threshold); 
  close_config_module();
}

function close_config_module() {
  document.getElementById('config_module').style = 'display: none';
}

function pop_error(value) {
  document.getElementById('alert').style = 'display: block';
  document.getElementById('alert').innerText = value;

  setTimeout(function () {
    document.getElementById('alert').style = 'display: none';
  }, 4000);
}
