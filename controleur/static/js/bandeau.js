function FiltrePeriode(data)
{
  let dataFiltree = [];

  for (let i = 0; i < data.length; i++)
    if (data[i].gdh >= startSpan && data[i].gdh <= endSpan)
      dataFiltree.push(data[i]);

  return dataFiltree;
}


function UpdateSliderSelection()
{
  const [from, to] = getParsed(fromSlider, toSlider);

  let diff = endDate - startDate;
  startSpan = Math.round(startDate + from * diff / 100);
  endSpan = Math.round(startDate + to * diff / 100);

  DessinerHeatmap(detections);

  document.getElementById('fromSliderTooltip').innerText = DateLisible(new Date(startSpan));
  document.getElementById('toSliderTooltip').innerText = DateLisible(new Date(endSpan));
}



/*
function GetSpanLisible(val)
{
  let sec = Math.floor(val % 60); val = val / 60;
  let min = Math.floor(val % 60); val = val / 60;
  let heures = Math.floor(val % 24); val = val / 24;
  let jours = Math.floor(val % 30);
  return jours + "j " + heures + "h " + min + "m " + sec + "s";
}
*/

function InitBandeau(largeur)
{
  ViderBandeau();
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  c.width = largeur;
}

function FillBandeau(points)
{
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  let diff = endDate - startDate;

  for (let i = 0; i < points.length; i++)
  {
    let x = (diff - (endDate - points[i].gdh)) * c.width / diff;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 20);
    ctx.stroke();
  }
}

function ViderBandeau()
{
  let c = document.getElementById("bandeau");
  let ctx = c.getContext("2d");
  ctx.clearRect(0,0,c.width,c.height);
}
