const express = require('express');
const path = require('path');

const app = express();
var cookieParser = require('cookie-parser')
const axios = require("axios");


const host = "dzne";



if (host.includes("localhost")) {
  authAddress = "http://localhost:8000/clinical-backend/is-logged-in/";
  loginAdress = "http://localhost:8000/clinical-backend/login/";
} else {
  address = "https://idsn.dzne.de/clinical-backend/is-logged-in/";
	
  loginAdress = "https://idsn.dzne.de/clinical-backend/login/";
}

/*
The following lines are a good example of a very lazy workaround.
@author Philipp Wegner
*/

// method for authorization
const redirect = async (req,res) => {
  const fullUrl = req.protocol + '://' + req.get('host') + req.originalUrl;
  if(!Object.keys(req.cookies).includes('idsn_access_token')){
    res.redirect(loginAdress + "?next=" + fullUrl);
    return;
  }
  const authCookie = req.cookies['idsn_access_token'];
  const response = await axios.get(authAddress + "?token=" + authCookie);
  const isAuthorized = response.data['message'];
  console.log(isAuthorized);
  

  if(isAuthorized == "authorized"){
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    return;
  }
  else{
    res.redirect(loginAdress + "?next=" + fullUrl);
    return;
  }
}







app.use(express.static(__dirname + 'dist'));
app.use(cookieParser());
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
  redirect(req,res);
    
});

app.get('/data-steward/*', function(req, res) {
  redirect(req,res);
  
});




console.log("Starting data-steward frontend on Port 5000...")
app.listen(5000);
