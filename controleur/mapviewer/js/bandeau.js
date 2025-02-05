function FiltrePeriode(data)
{
  var dataFiltree = [];

  for (var i = 0; i < data.length; i++)
    if (data[i].gdh >= startSpan && data[i].gdh <= endSpan)
      dataFiltree.push(data[i]);

  return dataFiltree;
}


function MajPeriode()
{
  const [from, to] = getParsed(fromSlider, toSlider);

  var diff = endDate - startDate;
  startSpan = Math.round(startDate + from * diff / 100);
  endSpan = Math.round(startDate + to * diff / 100);

  MajTooltip();
}


function MajTooltip()
{
  var fromTooltip = document.getElementById('fromSliderTooltip')
  fromTooltip.innerText = DateLisible(new Date(startSpan));
  
  var toTooltip = document.getElementById('toSliderTooltip');
  toTooltip.innerText = DateLisible(new Date(endSpan));
}


function GetSpanLisible(val)
{
  var sec = Math.floor(val % 60); val = val / 60;
  var min = Math.floor(val % 60); val = val / 60;
  var heures = Math.floor(val % 24); val = val / 24;
  var jours = Math.floor(val % 30);
  return jours + "j " + heures + "h " + min + "m " + sec + "s";
}


function CreerBandeau(largeur)
{
  ViderBandeau();
  var c = document.getElementById("bandeau");
  var ctx = c.getContext("2d");
  c.width = largeur;

  var diff = endDate - startDate;

  for (var i = 0; i < tabCouchesDessin.length; i++)
  {
    var madate = diff - (endDate - tabCouchesDessin[i].gdh);
    var x = madate * largeur / diff;

    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, 20);
    ctx.stroke();
  }
}

function ViderBandeau()
{
  var c = document.getElementById("bandeau");
  var ctx = c.getContext("2d");
  ctx.clearRect(0,0,c.width,c.height);
}
