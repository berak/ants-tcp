function Smoothie( id, upd )
{
  this.crt = new SmoothieChart();
  this.tl = [];        
  this.crt.streamTo(document.getElementById(id), upd);
};

Smoothie.prototype.add = function( ts, col,lw )
{
  var t = new TimeSeries();
  this.tl.push(t);
  this.crt.addTimeSeries(t, { fps: 0.3, strokeStyle: 'rgba('+col+',1)', fillStyle: 'rgba('+col+',.22)', lineWidth: lw });
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
  //~ url = "http://localhost:2080/stats";
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
     txt="" 
      //~ var txt = "<table>" 
      //~ for ( var i=0; i<p.length-2; i++ ) {
          //~ if ( i%6 == 0 ) {
            //~ if ( i > 0 ) {
              //~ txt += "</tr>"
            //~ }
            //~ txt += "<tr>"
          //~ }
          //~ elm = p[i+2]
          //~ txt += "<td>" + elm + "</td>"
      //~ }
      //~ txt += "</tr></table>"
      //~ document.getElementById("players").innerHTML = txt
     // document.getElementById("dg").innerHTML = t1 + " : " + t2 + " : " + t;
     // document.getElementById("dg").innerHTML = t1 + " : " + t2 + " : " + t;
    }
  }
}

function loadTabs()
{
  machine1 = new Smoothie("chart", 3000);
  machine1.add( "Players", '255, 0, 0', 4 );
  machine1.add( "Games",   '0, 255, 0', 3 );
  setInterval(function() {
   updateTimeLine();
  }, 3000);        
}
