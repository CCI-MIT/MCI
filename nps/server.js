var express = require("express");
var app = express.createServer();
var communication = require('./communication');

var hostname = require("os").hostname();
var env;
switch (hostname) {
    case 'www.mit.edu':
        env = 'prod';
        break;
    case 'test.mit.edu':
        env = 'test';
        break;
    default:
        env = 'dev';
}
var confPath = require('path').resolve(__dirname, 'conf.json');
var cnf      = require('nconf').file({ file: confPath });
var logLevel    = cnf.get(env + ':loglevel');
console.log("level: " + logLevel);

if (env != 'prod') {
    require('longjohn');
}

var winston = require('winston');
// Necessary unless we want winston's wacky default levels
winston.setLevels(winston.config.syslog.levels);
winston.remove(winston.transports.Console);
winston.add(winston.transports.Console, {
    timestamp: true,
    level: logLevel
});

communication.init(app, cnf, env, winston);
app.listen(10000, '0.0.0.0');
