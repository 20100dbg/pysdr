const socket = io();
let dict_module = {};

//initialize
(function() {

  let detections = {{detections}};
  for (var i = 0; i < detections.length; i++) {
    //module_id, dt, frq
    add_detection(detections[i][0], detections[i][1], detections[i][2]);
  }

  let modules = {{modules}};
  if (modules.length == 0) {
    document.getElementById('config_nb_module').style = 'display: block';
  }
  else
  {
    for (var i = 0; i < modules.length; i++) {
      threshold = modules[0][3] / 10;
      dict_module[i+1] = {'frq_start': modules[0][1], 'frq_end': modules[0][2], 'threshold': threshold, 'applied': modules[0][4]};
      add_dom_module(i+1);
    }
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
  threshold = threshold * 10;
  socket.emit("config", {'module_id': module_id, 'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold});
}

socket.on("connect", () => {
  update_etat(true);
  socket.emit("set_time", Date.now());
});

socket.on("disconnect", () => {
  update_etat(false);
});

socket.on("got_config_ack", function(module_id) {
  dict_module[module_id]['applied'] = true;
  pop_error("C" + module_id + " configuré");
});

socket.on("got_pong", function(module_id) {
  pop_error("C" + module_id + " répond");
});

socket.on("got_frq", function(params) {
  module_id = params['module_id'];
  current_dt = params['current_dt'];
  frq = params['frq'];

  add_detection(module_id, current_dt, frq);
  pop_error("C" + module_id + " - " + pretty_frq(frq));
});


// interface

function add_detection(module_id, current_dt, frq) {
  let log_detections = document.getElementById('log_detections');
  //log_detections.value += pretty_gdh(current_dt) + " - C" + module_id + " - " + pretty_frq(frq) + "\n";
  //log_detections.scrollTop = log_detections.scrollHeight;
  

  const tpl = document.createElement('template');
  log_row = pretty_gdh(current_dt) + " - C" + module_id + " - " + pretty_frq(frq);
  tpl.innerHTML = '<span class="log_row">'+ log_row +'</span>'

  log_detections.appendChild(tpl.content.firstChild);
  log_detections.scrollTop = log_detections.scrollHeight;
}

function pretty_frq(frq) {

  x = (frq / 1000000).toString();
  tab = x.split('.');
  left = tab[0].padStart(3, '0');
  right = (tab.length == 1) ? "000" : tab[1].substring(0,3).padEnd(3, '0');
  return left + '.' + right + 'M';

}

function pretty_gdh(gdh) {
  gdh = new Date(gdh * 1000);
  return gdh.toLocaleString();
}


function show_loader(duree = 1) {
    document.getElementById('etat').classList.add('loader');
    document.getElementById('etat').style.animationDuration = duree + 's';
    document.getElementById('etat').style.WebkitAnimationDuration = duree + 's';

    setTimeout(function () {
      document.getElementById('etat').classList.remove('loader');
    }, duree * 1000);
}

function toggle_tab(tab)
{
  let tab_detections = document.getElementById('tab_detections');
  let tab_modules = document.getElementById('tab_modules');
  let tab_advanced = document.getElementById('tab_advanced');
  
  tab_detections.style.display = 'none';
  tab_modules.style.display = 'none';
  tab_advanced.style.display = 'none';

  if (tab == "detections") tab_detections.style.display = 'block';
  else if (tab == "modules") tab_modules.style.display = 'block';
  else if (tab == "advanced") tab_advanced.style.display = 'block';
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
    dict_module[i] = {'frq_start': 400, 'frq_end': 420, 'threshold': 0.9, 'applied': true};

    add_dom_module(i);
  }

  document.getElementById('config_nb_module').style = 'display: none';
}

function add_dom_module(id)
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

  document.getElementById('frq_start').value = dict_module[module_id]['frq_start'];
  document.getElementById('frq_end').value = dict_module[module_id]['frq_end'];
  document.getElementById('threshold').value = dict_module[module_id]['threshold'];
  document.getElementById('applied').checked = dict_module[module_id]['applied'];
  
}

function save_config_module() {
  let module_id = document.getElementById('module_id').value;
  let frq_start = document.getElementById('frq_start').value;
  let frq_end = document.getElementById('frq_end').value;
  let threshold = document.getElementById('threshold').value;

  dict_module[module_id]['frq_start'] = frq_start;
  dict_module[module_id]['frq_end'] = frq_end;
  dict_module[module_id]['threshold'] = threshold;
  dict_module[module_id]['applied'] = false;

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
