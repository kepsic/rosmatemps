var xData = []
var yData = []
var sensors = []
var data = []
var colors = []
var lineSize = []
var labels = []
var gauges = [['Label', 'Value']]


function random_rgba() {
    var o = Math.round, r = Math.random, s = 255;
    return 'rgba(' + o(r()*s) + ',' + o(r()*s) + ',' + o(r()*s) + ',' + r().toFixed(1) + ')';
}


const loadData = (update) => {

  fetch('http://kontor.rosmakool.ee:3000/api/v1/temps')
    .then( response => {
      if (response.status !== 200) {
        console.log(response);
      }
      return response;
    })
    .then(response => response.json())
    .then(parsedResponse => {
      const unpackData = (arr, key) => {
        return arr.map(obj => obj[key])
      }

    fetch('http://kontor.rosmakool.ee:3000/api/v1/labels')
    .then(res => res.json())
    .then((out) => {
      for ( var i = 0 ; i < parsedResponse.length ; i++ ) {
          var sensor = parsedResponse[i]['sensor'];
          if (sensors.indexOf(sensor) < 0 ) {
              sensors.push(sensor);
              labels.push(out[sensor]);
          }
      }

      for ( var i = 0 ; i < sensors.length ; i++ ) {
           var sensor = sensors[i];
           var xValues = [];
           var yValues = [];
           colors.push(random_rgba());
           lineSize.push(Math.floor(Math.random() * 2) + 1);
           for ( var j = 0 ; j < parsedResponse.length ; j++ ) {
               var jsensor = parsedResponse[j]['sensor'];
            if (sensor.localeCompare(jsensor) == 0) {
              xValues.push(parsedResponse[j]['time'])
              yValues.push(parsedResponse[j]['value'])
            }
           }
           xData.push(xValues);
           yData.push(yValues);
      }

      })

      
      .then( fillData => {

        for ( var i = 0 ; i < xData.length ; i++ ) {
          
          var result = {
            x: xData[i],
            y: yData[i],
            type: 'scatter',
            mode: 'lines',
            name: labels[i],
            line: {
              color: colors[i],
              width: lineSize[i]
            }
          };
          data.push(result);
        }
    
        var layout = {
          showlegend: false,
          height: 1024,
        //  width: 1280,
          xaxis: {
            showline: true,
            showgrid: true,
            showticklabels: false,
            linecolor: 'rgb(204,204,204)',
            linewidth: 2,
            autotick: false,
            ticks: 'outside',
            tickcolor: 'rgb(204,204,204)',
            tickwidth: 2,
            ticklen: 5,
            tickfont: {
              family: 'Arial',
              size: 12,
              color: 'rgb(82, 82, 82)'
            }
          },
          yaxis: {
            showgrid: false,
            zeroline: false,
            showline: false,
            showticklabels: false
          },
          autosize: true,
          margin: {
            autoexpand: true,
            l: 100,
            r: 20,
            t: 100
          },
          annotations: [
            {
              xref: 'paper',
              yref: 'paper',
              x: 0.0,
              y: 1.05,
              xanchor: 'center',
              yanchor: 'bottom',
              text: '',
              font:{
                family: 'Arial',
                size: 30,
                color: 'rgb(37,37,37)'
              },
              showarrow: false
            },
            {
              xref: 'paper',
              yref: 'paper',
              x: 0.5,
              y: -0.1,
              xanchor: 'center',
              yanchor: 'top',
              text: ' ',
              showarrow: false,
              font: {
                family: 'Arial',
                size: 12,
                color: 'rgb(150,150,150)'
              }
            }
          ]
        };
        
        for( var i = 0 ; i < xData.length ; i++ ) {
          var result = {
            xref: 'paper',
            x: 0.05,
            y: yData[i][0],
            xanchor: 'right',
            yanchor: 'middle',
            text: labels[i],
            showarrow: false,
            font: {
              family: 'Arial',
              size: 16,
              color: 'black'
            }
          };
          var result2 = {
            xref: 'paper',
            x: 0.95,
            y: yData[i][11],
            xanchor: 'left',
            yanchor: 'middle',
            text: yData[i][11],
            font: {
              family: 'Arial',
              size: 16,
              color: 'black'
            },
            showarrow: false
          };
        
          layout.annotations.push(result, result2);
        }

         for ( var i = 0 ; i < data.length ; i++ ) {
             var name = data[i]['name']
             var value = data[i]['y'][0]
             gauges.push([name,value])
          }


      google.charts.load('current', {'packages':['gauge']});
      google.charts.setOnLoadCallback(drawChart);
      function drawChart() {
        var gauge_data = google.visualization.arrayToDataTable(gauges);

        var options = {
          width: 1400, height: 480,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('chart_div'));

        chart.draw(gauge_data, options);

      }

      return Plotly.newPlot('graphs-container', data, layout);
    })
    })
    .catch( error => {
        var myDiv = document.getElementById("graphs-container");
        myDiv.innerHTML = "Uups: " + error;
        console.log(error);
}
);
}


document.addEventListener('DOMContentLoaded', function() {
   loadData(false);
}, false);
