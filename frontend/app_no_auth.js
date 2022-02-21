const express = require('express');
const path = require('path');

const app = express();

app.use(express.static(__dirname + 'dist'));

app.get('/data-steward/css/:name', function (req, res) {
  var name = req.params.name;
  res.sendFile(path.join(__dirname, 'dist/css/', name));
});
app.get('/data-steward/js/:name', function (req, res) {
  var name = req.params.name;
  res.sendFile(path.join(__dirname, 'dist/js/', name));
});
app.get('/data-steward/img/:name', function (req, res) {
  var name = req.params.name;
  res.sendFile(path.join(__dirname, 'dist/img/', name));
});


app.get('/data-steward/fonts/:name', function (req, res) {
  var name = req.params.name;
  res.sendFile(path.join(__dirname, 'dist/fonts/', name));
});

app.get('/data-steward', function (req, res) {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    return;
    
});


app.get("/data-steward/swagger",function(req, res) {
  res.sendFile(path.join(__dirname, 'dist', 'swagger.html'));
  return;
});

app.get('/data-steward/*', function(req, res) {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    return;
});






console.log("Starting data-steward frontend on Port 5000...")
app.listen(5000);
