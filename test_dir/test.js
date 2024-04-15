var express = require('express');
var cookieParser = require('cookie-parser');
var bodyParser = require('body-parser');

var hbs = require('hbs');
var session = require('express-session');

var index = require('./routes/index');

var jwt = require('express-jwt');


var app = express();



app.get('/protected', jwt({ secret: 'shhhhhhared-secret' }), function(req, res) {
    if (!req.user.admin) return res.sendStatus(401);
    res.sendStatus(200);
});

module.exports = app;

