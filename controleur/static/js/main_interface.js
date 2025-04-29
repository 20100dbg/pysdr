
//Add a detection line in "historique" tab
function add_detection_dom(module_id, dt, frq, pwr) {

  let log_detections = document.getElementById('log_detections');
  let small_date = get_small_date(dt);

  const tpl = document.createElement('template');
  log_row = small_date + " / C" + module_id + " / " + pretty_frq(frq) + " / " + pwr;
  tpl.innerHTML = '<span class="log_row">'+ log_row +'</span>'

  log_detections.insertBefore(tpl.content.firstChild, log_detections.firstChild);
}


//Show a loading animation
function show_loader(duree = 1) {
    document.getElementById('etat').classList.add('loader');
    document.getElementById('etat').style.animationDuration = duree + 's';
    document.getElementById('etat').style.WebkitAnimationDuration = duree + 's';

    setTimeout(function () {
      document.getElementById('etat').classList.remove('loader');
    }, duree * 1000);
}


//toggle between tabs
function toggle_tab(tabname)
{
  let tabs = ['viewer', 'history', 'modules', 'config'];

  for (let i = 0; i < tabs.length; i++) {
    let div = document.getElementById('tab_' + tabs[i]);

    if (tabs[i] == tabname) div.style.display = 'block';
    else div.style.display = 'none';
  }
}


//Show/hide connection status
function update_etat(etat)
{
  let div_etat = document.getElementById('etat');

  if (etat) div_etat.style.display = 'none';
  else div_etat.style.display = 'block';
}



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
  div.innerText =  round(latitude, 5) + "/" + round(longitude, 5);
}

function updaate_module_conf(module_id, status)
{
  let div = document.getElementById("conf-" + module_id);
  div.innerText = status;
}

function update_module_activity(module_id)
{
  modules[module_id].last_activity = Date.now();
  let div = document.getElementById("activity-" + module_id);
  div.innerText = modules[module_id].last_activity;
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
        '<span id="name-'+ module_id +'">C'+ module_id +'</span> - ' +
        '<span id="position-'+ module_id +'">NL</span> - ' +

        '<span id="conf-'+ module_id +'">initial</span> - ' +
        '<span id="activity-'+ module_id +'"></span> - ' +

        '<span class="buttons">' +

          '<button onclick="request_gps(\''+ module_id +'\');" style="margin-right: 20px">GPS</buton>' +
          '<button onclick="request_conf(\''+ module_id +'\');" style="margin-right: 20px">Conf</buton>' +
          
          '<button onclick="send_ping(\''+ module_id +'\');" style="margin-right: 20px">Ping</buton>' +
          '<button onclick="show_config_module(\''+ module_id +'\');">Config</buton>' +
        '</span>' +
      '</div>';
}


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
