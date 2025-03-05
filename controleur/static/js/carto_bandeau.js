function FiltrePeriode(data)
{
  let filtered_data = [];

  for (let i = 0; i < data.length; i++)
    if (data[i].dt >= carto_start_range && data[i].dt <= carto_end_range)
      filtered_data.push(data[i]);

  return filtered_data;
}


function update_slider_range()
{
  const [from, to] = getParsed(fromSlider, toSlider);
  let diff = carto_max_date - carto_min_date;
  
  carto_start_range = Math.round(carto_min_date + from * diff / 100);
  carto_end_range = Math.round(carto_min_date + to * diff / 100);

  document.getElementById('fromSliderTooltip').innerText = DateLisible(new Date(carto_start_range));
  document.getElementById('toSliderTooltip').innerText = DateLisible(new Date(carto_end_range));
}

function bandeau_init(points)
{
  bandeau_empty();
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  c.width = get_windows_width();

  let diff = carto_max_date - carto_min_date;
  //(diff * 0.02);

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

function bandeau_empty()
{
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  ctx.clearRect(0,0,c.width,c.height);
}
