//const socket = io();

//helpers

function date_fr() {
  let dateObj = new Date();
  dateObj.toLocaleDateString('fr-fr') + ' ' + dateObj.toTimeString().substring(0,8);   
}

function date_standard() {
  let dateObj = new Date();
  dateObj.toISOString().replace('T',' ').substring(0,19);
}

function is_undefined(some_var) {
  return (typeof some_var === 'undefined');
}

function pretty_gdh(timestamp) {
  return new Date(timestamp).toLocaleString();
}

function pretty_frq(frq) {

  x = (frq / 1000000).toString();
  tab = x.split('.');
  left = tab[0].padStart(3, '0');
  right = (tab.length == 1) ? "000" : tab[1].substring(0,3).padEnd(3, '0');
  return left + '.' + right + 'M';
}

//helpers


let default_frq_start = 400;
let default_frq_end = 420;
let default_threshold = 420;


let test_modules = {
  '1': {'lat':48.88888, 'lng': 7.90017, 'frq_start': default_frq_start, 'frq_end': default_frq_end, 'threshold': default_threshold, 'last_ping': 0, 'config_applied': true},
  '2': {'lat':48.89113, 'lng': 7.96126, 'frq_start': default_frq_start, 'frq_end': default_frq_end, 'threshold': default_threshold, 'last_ping': 0, 'config_applied': true},
  '3': {'lat':48.88594, 'lng': 7.99696, 'frq_start': default_frq_start, 'frq_end': default_frq_end, 'threshold': default_threshold, 'last_ping': 0, 'config_applied': true}


};

let test_detections = [
  {'module_id': '1', 'frq': 400.500, 'pwr': -15, 'dt': 1739557211000 },
  {'module_id': '2', 'frq': 410.250, 'pwr': -7, 'dt': 1739557222000 },
  {'module_id': '3', 'frq': 405.800, 'pwr': -10, 'dt': 1739557233000 },
  {'module_id': '2', 'frq': 412.100, 'pwr': -18, 'dt': 1739557242000 },
  {'module_id': '2', 'frq': 405.500, 'pwr': -16, 'dt': 1739557244000 },
  {'module_id': '2', 'frq': 407.500, 'pwr': -22, 'dt': 1739557246000 },
  {'module_id': '2', 'frq': 402.350, 'pwr': -30, 'dt': 1739557248000 },
  {'module_id': '1', 'frq': 415.500, 'pwr': -20, 'dt': 1739557255000 }
];


function import_detections(detections) {
  let data = [];

  for (let i = 0; i < detections.length; i++) {
    //module_id, dt, frq, pwr
    let dt = new Date(detections[i]['dt']);
    dt = dt.toISOString().replace('T',' ').substring(0,19);
    data.push([detections[i]['module_id'], dt, detections[i]['frq'], detections[i]['pwr']])

    add_detection_dom(detections[i]['module_id'], dt, detections[i]['frq'], detections[i]['pwr']);
  }
  
  datatable_import(data);
}


//réception/découverte d'un nouveau module pendant le fonctionnement de l'app
function add_module(lat, lng, frq_start, frq_end, threshold, last_ping, config_applied) {

  modules[modules.length] = {'lat': lat, 'lng': lng, 'frq_start': frq_start, 'frq_end': frq_end, 
                              'threshold': threshold, 'last_ping': last_ping, 'config_applied': config_applied };
  add_module_dom(modules.length);
}


//initialize
(function() {

  main_init();
  datatable_init();
  carto_init();

  //données de test
  modules = test_modules;

  //import des modules via template
  carto_import_modules(test_modules);

  //données de test
  detections = test_detections;
  import_detections(detections);

})();

function main_init() {

  for (var i = 0; i < detections.length; i++) {
    //module_id, dt, frq, pwr
    add_detection_dom(detections[i][0], detections[i][1], detections[i][2], detections[i][3]);
  }

  if (modules.length == 0) {
    document.getElementById('config_nb_module').style = 'display: block';
  }
  else {
    for (var i = 0; i < modules.length; i++) {
      add_module_dom(i+1);
    }
  }
  
  //mets les valeurs par défaut dans les champs
  close_config_module();
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


//sockets
/*
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
  threshold = threshold * 10;
  socket.emit("config", {'module_id': module_id, 'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold});
}

/*
socket.on("connect", () => {
  update_etat(true);
  socket.emit("set_time", Date.now());
});

socket.on("disconnect", () => {
  update_etat(false);
});

socket.on("got_config_ack", function(module_id) {
  modules[module_id]['applied'] = true;
  pop_error("C" + module_id + " configuré");
});

socket.on("got_pong", function(module_id) {
  pop_error("C" + module_id + " répond");
});

socket.on("got_frq", function(params) {
  module_id = params['module_id'];
  current_dt = params['current_dt']; //seconds
  frq = params['frq'];

  import_detections([params["module_id"], params["dt"], params["frq"], params["pwr"]])
  add_detection_dom(module_id, current_dt, frq);
  pop_error("C" + module_id + " - " + pretty_frq(frq));
});


*/

// interface

function add_detection_dom(module_id, dt, frq, pwr) {
  let log_detections = document.getElementById('log_detections');

  const tpl = document.createElement('template');
  log_row = pretty_gdh(dt) + " - C" + module_id + " - " + pretty_frq(frq);
  tpl.innerHTML = '<span class="log_row">'+ log_row +'</span>'

  log_detections.appendChild(tpl.content.firstChild);
  log_detections.scrollTop = log_detections.scrollHeight;
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

  for (let i = 1; i < nb_module + 1; i++) {
    modules[i] = {'frq_start': default_frq_start, 'frq_end': default_frq_end, 'threshold': default_frq_threshold, 'applied': true};

    add_module_dom(i);
  }

  document.getElementById('config_nb_module').style = 'display: none';
}

function add_module_dom(id)
{
  const tpl = document.createElement('template');
  tpl.innerHTML = get_tpl(id);

  let container = document.getElementById('tab_modules');
  container.appendChild(tpl.content.firstChild);
}

function get_tpl(id)
{
  return '<div class="line">' +
        '<span id="name-'+ id +'">Capteur '+ id +'</span>' +

        '<span class="buttons">' +
          '<button onclick="send_ping(\''+ id +'\');" style="margin-right: 20px">Ping</buton>' +
          '<button onclick="show_config_module(\''+ id +'\');">Config</buton>' +
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
