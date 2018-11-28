const Influx = require('influx');
const express = require('express');
const path = require('path');
const os = require('os');
const bodyParser = require('body-parser');
const app = express();
const influx = new Influx.InfluxDB({
 host: 'localhost',
 database: 'temps',
 schema: [
   {
     measurement: 'rosma_temps',
     fields: {
       value: Influx.FieldType.FLOAT
     },
     tags: [
       'sensor'
     ]
   }
 ]
}
)
var cors = require('cors');
var whitelist = ['http://kontor.rosmakool.ee:8080', 'https://rosmakool.ee/temps/']
var corsOptions = {
  origin: function (origin, callback) {
    if (whitelist.indexOf(origin) !== -1) {
      callback(null, true)
    } else {
      callback(new Error('Not allowed by CORS'))
    }
  }
}

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
  extended: true
}));
app.use(express.static(path.join(__dirname, 'public')));
app.set('port', 3000);

influx.getMeasurements()
  .then(names => console.log('My measurement names are: ' + names.join(', ')))
  .then(() => {
    app.listen(app.get('port'), () => {
      console.log(`Listening on ${app.get('port')}.`);
    });
  })
  .catch(error => console.log({ error }));

app.get('/api/v1/temps',cors(corsOptions), function (request, response) {
  var id = request.query.id;
  influx.query(`
    SELECT * FROM rosma_temps
    where time > now() - 6h
    group by sensor
    order by time desc
    `)
    .then(result => response.status(200).json(result))
    .catch(error => response.status(500).json({ error }));
});

app.get('/api/v1/labels',cors(corsOptions), function (request, response) {
   var labels = require("./labels.json");
   response.send(JSON.stringify(labels));
});
