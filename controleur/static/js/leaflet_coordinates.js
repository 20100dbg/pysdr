"use strict";

/**
 * author Michal Zimmermann <zimmicz@gmail.com>
 * Displays coordinates of mouseclick.
 * @param object options:
 *        position: bottomleft, bottomright etc. (just as you are used to it with Leaflet)
 *        latitudeText: description of latitude value (defaults to lat.)
 *        longitudeText: description of latitude value (defaults to lon.)
 *        promptText: text displayed when user clicks the control
 *        precision: number of decimals to be displayed
 */
L.Control.Coordinates = L.Control.extend({
	options: {
		position: 'bottomleft',
		latitudeText: 'lat.',
		longitudeText: 'lon.',
		promptText: 'Ctrl+C pour copier les coordonnées',
		precision: 5
	},

	initialize: function(options)
	{
		L.Control.prototype.initialize.call(this, options);
	},

	onAdd: function(map)
	{
		var className = 'leaflet-control-coordinates',
			that = this,
			container = this._container = L.DomUtil.create('div', className);
		this.visible = false;

			L.DomUtil.addClass(container, 'hidden');


		L.DomEvent.disableClickPropagation(container);

		this._addText(container, map);

		L.DomEvent.addListener(container, 'click', function() {
			let latitude = L.DomUtil.get(that._lat).textContent, longitude = L.DomUtil.get(that._lng).textContent;

			if (typeCoord != 'mgrs')
			{
				latitude = latitude.substr(this.options.latitudeText.length + 1);
				longitude = longitude.substr(this.options.longitudeText.length + 1);
			}

			window.prompt(this.options.promptText, latitude + ' ' + longitude);
    	}, this);

		return container;
	},

	_addText: function(container, context)
	{
		this._lat = L.DomUtil.create('span', 'leaflet-control-coordinates-lat' , container),
		this._lng = L.DomUtil.create('span', 'leaflet-control-coordinates-lng' , container);
		this._zoom = L.DomUtil.create('span', 'leaflet-control-coordinates-zoom' , container);

		return container;
	},

	/**
	 * This method should be called when user clicks the map.
	 * @param event object
	 */
	setCoordinates: function(obj)
	{
		if (!this.visible) {
			L.DomUtil.removeClass(this._container, 'hidden');
		}

		if (obj.latlng) {
			if (carto_coord_type == 'mgrs')
			{
				L.DomUtil.get(this._lat).innerHTML = LatLongToMGRS(obj.latlng.lat, obj.latlng.lng);
				L.DomUtil.get(this._lng).innerHTML = '';
			}
			else
			{
				L.DomUtil.get(this._lat).innerHTML = '<strong>' + this.options.latitudeText + ':</strong> ' + obj.latlng.lat.toFixed(this.options.precision).toString();
				L.DomUtil.get(this._lng).innerHTML = '<strong>' + this.options.longitudeText + ':</strong> ' + obj.latlng.lng.toFixed(this.options.precision).toString();
			}
			L.DomUtil.get(this._zoom).innerHTML = ' <strong>z:</strong> ' + map._zoom.toString();
		}
	}
});





function LatLongToMGRS(Lat, Long)
{ 
  if (Lat < -80) return 'Too far South' ; if (Lat > 84) return 'Too far North' ;
  let c = 1 + Math.floor ((Long+180)/6);
  let e = c*6 - 183 ;
  let k = Lat*Math.PI/180;
  let l = Long*Math.PI/180;
  let m = e*Math.PI/180;
  let n = Math.cos (k);
  let o = 0.006739496819936062*Math.pow (n,2);
  let p = 40680631590769/(6356752.314*Math.sqrt(1 + o));
  let q = Math.tan (k);
  let r = q*q;
  let s = (r*r*r) - Math.pow (q,6);
  let t = l - m;
  let u = 1.0 - r + o;
  let v = 5.0 - r + 9*o + 4.0*(o*o);
  let w = 5.0 - 18.0*r + (r*r) + 14.0*o - 58.0*r*o;
  let x = 61.0 - 58.0*r + (r*r) + 270.0*o - 330.0*r*o;
  let y = 61.0 - 479.0*r + 179.0*(r*r) - (r*r*r);
  let z = 1385.0 - 3111.0*r + 543.0*(r*r) - (r*r*r);
  let aa = p*n*t + (p/6.0*Math.pow (n,3)*u*Math.pow (t,3)) + (p/120.0*Math.pow (n,5)*w*Math.pow (t,5)) + (p/5040.0*Math.pow (n,7)*y*Math.pow (t,7));
  let ab = 6367449.14570093*(k - (0.00251882794504*Math.sin (2*k)) + (0.00000264354112*Math.sin (4*k)) - (0.00000000345262*Math.sin (6*k)) + (0.000000000004892*Math.sin (8*k))) + (q/2.0*p*Math.pow (n,2)*Math.pow (t,2)) + (q/24.0*p*Math.pow (n,4)*v*Math.pow (t,4)) + (q/720.0*p*Math.pow (n,6)*x*Math.pow (t,6)) + (q/40320.0*p*Math.pow (n,8)*z*Math.pow (t,8));
  aa = aa*0.9996 + 500000.0;
  ab = ab*0.9996; if (ab < 0.0) ab += 10000000.0;
  let ad = 'CDEFGHJKLMNPQRSTUVWXX'.charAt (Math.floor (Lat/8 + 10));
  let ae = Math.floor (aa/100000);
  let af = ['ABCDEFGH','JKLMNPQR','STUVWXYZ'][(c-1)%3].charAt (ae-1);
  let ag = Math.floor (ab/100000)%20;
  let ah = ['ABCDEFGHJKLMNPQRSTUV','FGHJKLMNPQRSTUVABCDE'][(c-1)%2].charAt (ag);
  function pad (val) {if (val < 10) {val = '0000' + val} else if (val < 100) {val = '000' + val} else if (val < 1000) {val = '00' + val} else if (val < 10000) {val = '0' + val};return val};
  
  let precision = false;

  if (precision)
  {
    aa = Math.toFixed(aa%100000,3); 
    ab = Math.toFixed(ab%100000,3);
  }
  else
  {
    aa = Math.floor(aa%100000); 
    ab = Math.floor(ab%100000);     
  }
  
  aa = pad(aa);
  ab = pad(ab);
  
  return c + ad + af + ah + ' ' + aa + ' ' + ab;
}