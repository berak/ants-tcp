function Smoothie( id, delay )
{
  this.crt = new SmoothieChart();
  this.tl = [];        
  this.crt.streamTo(document.getElementById(id), delay);
};

Smoothie.prototype.add = function( ts, col,lw )
{
  var t = new TimeSeries();
  this.tl.push(t);
  this.crt.addTimeSeries(t, { fps: 0.03, strokeStyle: 'rgba('+col+',1)', fillStyle: 'rgba('+col+',.22)', lineWidth: lw });
};

Smoothie.prototype.update = function( sarr )
{
  var d = new Date().getTime();
  for ( var i=0; i<this.tl.length; i++ )
    this.tl[i].append(d, sarr[i]);
};

function updateTimeLine()
{     
  //~ get("http://b2.ants--game.appspot.com/stats/s");
  url = "/stats";
  
  var http =  ( window.XMLHttpRequest 
      ? new XMLHttpRequest()
      : new ActiveXObject("Microsoft.XMLHTTP")
      );				

  http.open( "GET", url, true );
  http.setRequestHeader( "Content-Type", "text/plain" ); 
  http.send(null);
  http.onreadystatechange = function()
  {
    if ( (http.readyState == 4) && (http.status < 400) )
    {
      var s = http.responseText;
      var p = s.split(" ");
      machine1.update( [p[0],p[1]] );        
      machine2.update( [p[2],p[3],p[4],p[5],p[6]] );        
    }
  }
}

function loadTabs()
{
  machine1 = new Smoothie("chart", 0);
  machine1.add( "Players", '255, 0, 0', 4 );
  machine1.add( "Games",   '0, 255, 0', 3 );
  machine2 = new Smoothie("gstat", 0);
  machine2.add( "Survived",   '0, 255, 0', 3 );
  machine2.add( "Eliminated", '255, 0, 0', 4 );
  machine2.add( "Timeout", '0, 0, 255', 4 );
  machine2.add( "Crashed", '0, 255, 255', 4 );
  machine2.add( "Draw", '255,0, 255', 4 );
  setInterval(function() {
   updateTimeLine();
  }, 2500);        
}
