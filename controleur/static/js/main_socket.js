const socket = io();

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


function request_gps(id_module) {
  socket.emit("request_gps", id_module);
}


socket.on("response_gps", function(params) {
  console.log(params);
  let module_id = params["module_id"];

  update_module_activity(module_id);
});


socket.on("response_conf", function(params) {
  console.log(params);
  let module_id = params["module_id"];

  update_module_activity(module_id);
});


function request_conf(id_module) {
  socket.emit("request_conf", id_module);
}


function send_config_module(module_id, frq_start, frq_end, threshold) {
  show_loader();
  socket.emit("config", {'module_id': module_id, 'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold});
  updaate_module_conf(module_id, "att resp");
}


socket.on("connect", () => {
  update_etat(true);
  //socket.emit("set_time", Date.now());
});


socket.on("disconnect", () => {
  update_etat(false);
});


socket.on("got_config_ack", function(params) {
  let module_id = params["module_id"];
  let success = params["success"];
  
  modules[module_id]['applied'] = success;
  update_module_activity(module_id);
  updaate_module_conf(module_id, "resp ok");

  pop_error("C" + module_id + " configuré");
});


socket.on("set_master_position", function(params) {
  set_master_position(params["latitude"], params["longitude"]);
});


socket.on("got_pong", function(params) {

  //update capteur
  let module_id = params["module_id"];
  modules[module_id].latitude = params["latitude"];
  modules[module_id].longitude = params["longitude"];  
  modules[module_id].frq_start = params["frq_start"];
  modules[module_id].frq_end = params["frq_end"];
  modules[module_id].threshold = params["threshold"];
  modules[module_id].applied = true;
  
  update_module_activity(module_id);

  //update detections position
  if (modules[module_id].latitude != 0 && modules[module_id].longitude != 0) {
    for (let i = 0; i < detections.length; i++) {
      detections[i][4] = modules[module_id].latitude;
      detections[i][5] = modules[module_id].longitude;
    }
    draw_heatmap(detections);
  }

  //update capteur position
  let layer = get_module_layer(module_id);

  if (layer != null) {

    //delete layer from map
    layer.remove();

    //delete layer from array
    let idx = modules_layers.indexOf(layer);
    modules_layers.splice(idx, 1);
  }

  carto_import_modules(modules);
  set_module_position(module_id, params["latitude"], params["longitude"]);

  pop_error("C" + module_id + " répond");
});


socket.on("got_frq", function(params) {

  let frq = pretty_frq(params['frq']);
  let module_id = params["module_id"];

  //si on reçoit une détection avant même avoir définit le nombre de modules (et donc l'objet)
  if (!(module_id in modules))
  {
    latitude = 0;
    longitude = 0;
  }
  else {
    latitude = modules[module_id].latitude;
    longitude = modules[module_id].longitude;
    update_module_activity(module_id);
  }

  import_detections([[module_id,params['dt'],params['frq'],params['pwr'], latitude, longitude]]);

  let module_layer = get_module_layer(module_id);

  if (module_layer != null) {
    let label = "C" + module_id.toString() + " : " + frq;
    add_tooltip(module_layer, label, 5);
  }

  pop_error("C" + module_id + " - " + frq + " / " + params["pwr"]);
});