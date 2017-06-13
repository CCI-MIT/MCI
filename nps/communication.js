(function() {

    module.exports.init = function(app, cnf, env, winston) {

        var io = require('socket.io').listen(app);
        io.set('log level', 0);  

        var redis = require("redis").createClient();
        redis.on('error', function (e) {
            winston.info("Redis Client Error: " + JSON.stringify(e, null, 4));
        });

        function log_users(level, msg) {
        //      winston.log(level, "USERS." + msg);
        }
        var users = require('./cursormgr')(redis, log_users);
        
        function log_cards(level, msg) {
              winston.log(level, "CARDS." + msg);
        }
        var cards = require('./cardmgr')(redis, log_cards, cnf, env);

        io.sockets.on('connection', function (socket) {

            socket.on('sb-registration-ping', function(data) {
                winston.info("communication >> Received 'sb-registration-ping'" +
                                   " from SubjectIdentity with ID " + data.siid +
                                              " in SessionBuilder " + data.sbid
                );
                redis.set("sbregping_" + data.siid, new Date().getTime());
                socket.emit('sb-registration-pingback', { hello: "world" });
            });


            /*  @data -- A dictionary with keys:
                    #ctid -- A CCI CompletedTask ID. 
                    #sid -- A CCI Subject ID.  */
            socket.on('allState', function(data) {

                winston.info("communication >> Received 'allState'" +
                                                      " from User " + data.sid +
                                              " in Completed Task " + data.ctid
                );

                socket.join(data.ctid);
                socket.set('ctid', data.ctid);
                socket.set('sid', data.sid);

                // Cleanup.  Hide the cursors of any Subjects in room 'data.ctid'
                // who have somehow disconnected without having 'removeCursor'
                // called for their cursors.
                users.eachUser(
                    data.ctid, 
                    function(sid, user, applyCont) {
                        var connected = false;
                        io.sockets.clients(data.ctid).forEach(function(sckt, i) {
                            sckt.get('sid', function(err, sid_sckt) {
                                if (sid_sckt == sid) {
                                    connected = true;
                                }
                            });
                        });
                        if (!connected) {
                            users.removeCursor(data, removeCursor);
                        }
                        applyCont();
                    }
                );

                // Send the Subject the coordinates of all present
                // Subjects' cursors.
                users.eachUser(
                    data.ctid, 
                    function(sid, user, applyCont) {
                        winston.info('communication >> Sending x, y ' +
                                                       ' of Subject ' + sid +
                                                       ' to Subject ' + data.sid +
                                                ' in Completed Task ' + data.ctid
                        );
                        user.sid = sid;
                        socket.emit('cursor', user);
                        applyCont();
                    }
                );

                function boardState() {
                    cards.eachCardInCurrentRound(
                        data.ctid, 
                        function(index, card, applyCont) {
                            var details;
                            switch (data.task_type) {
                              case 'C': 
                                details = "\n  (State: " + card.state + ")";
                                break;
                              case 'I':
                                details = "\n  (In Pattern: " + card.in_selection + ")"
                                        + "\n  (In Selection: " + card.in_selection + ")";
                                break;
                              default:
                                details = "";
                            }
                            winston.info( "communication >> Sending Card " + index
                                        + " to Subject " + data.sid
                                        + " in Completed Task " + data.ctid
                            );
                            socket.emit('card', { index: index, card: card });
                            applyCont();
                        }, 
                        function() {
                            if (data.task_type == 'S') {
                                socket.emit('cardsSent');
                            }
                        }
                    );

                    cards.pointsGlobal(data, function(score) {
                        winston.info("communication >> Sending Score (" + score + ")" +
                                                       " to Subject " + data.sid +
                                                " in Completed Task " + data.ctid
                        );
                        io.sockets.to(data.ctid).emit('score', score);
                    });

                    cards.displaySubmitButtonIfAppropriate(data, function() {
                        winston.debug( "communication >> Sending "
                                     + "'displaySubmitButton' to Subject " + data.sid
                                     + " in CT " + data.ctid + "."
                                     );                      
                        socket.emit('displaySubmitButton');
                    });

                }

                if (data.task_type == 'I') {
                    cards.scheduleRoundStartIfAppropriate(
                        data,
                        function() {
                            io.sockets.to(data.ctid).emit('roundPreview');
                        },
                        function() {
                            io.sockets.to(data.ctid).emit('roundStart');
                        },
                        boardState);
                } else {
                    boardState();
                }
            });

            /*  @data -- A dictionary with keys:
                    #ctid       -- A CCI CompletedTask ID.
                    #sid       -- A CCI Subject ID.  */ 
            socket.on('submitClick', function(data) {
                winston.info("communication >> Received 'submitClick' " +
                                                       " from Subject " + data.sid +
                                                  " in Completed Task " + data.ctid
                );
                cards.submitClick(
                    data,
                    // callback 'emitSubmit'
                    function() {
                        // NOTE that we're emitting the user's sid, might be useful
                        winston.info("communication >> Broadcasting 'submitClick'" +
                                            " in Completed Task " + data.ctid
                        );
                        io.sockets.to(data.ctid).emit('submitClick', data);
                    },
                    // callback 'emitRoundEnd'
                    function(outcomeData) {
                        winston.info( "communication >> Broadcasting "
                                    + "'roundEnd' for CT " + data.ctid + "."
                                    );                      
                        io.sockets.to(data.ctid).emit('roundEnd', outcomeData);
                    },
                    // callback 'emitRoundPreview'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'roundPreview' for CT " + data.ctid + "."
                                    );                      
                        io.sockets.to(data.ctid).emit('roundPreview');
                    },
                    // callback 'emitRoundStart'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'roundStart' for CT " + data.ctid + "."
                                    );                      
                        io.sockets.to(data.ctid).emit('roundStart');
                    },
                    // callback 'emitError'
                    function() {
                        winston.info("communication >> Broadcasting 'submitError'" +
                                            " in Completed Task " + data.ctid
                        );
                        io.sockets.to(data.ctid).emit('submitError');
                    },
                    // registerSubmitClick
                    function(outcomeDict, rndIndex) {
                        users.tilesSubmitClick(
                            data.ctid,
                            data.sid,
                            rndIndex,
                            outcomeDict
                        ); 
                    }
                );
            });
                        
            /*  @data -- A dictionary with keys:
                    #ctid       -- A CCI CompletedTask ID.
                    #sid       -- A CCI Subject ID.
                    #card_index -- The index of a card in the 'Concentration'-
                                  type Completed Task whose ID is #ctid.  */ 
            socket.on('click', function(data) {

                winston.info("communication >> Received 'click' " +
                                                 " from Subject " + data.sid +
                                            " in Completed Task " + data.ctid
                );

                var registerClick;
                if (data.task_type == 'C') {
                    registerClick = function(outcome) {
                        users.concentrationCardClick(
                            data.ctid,
                            data.sid,
                            data.card_index,
                            outcome,
                            function(user) {
                                io.sockets.to(data.ctid).emit('click', user);
                            }
                        ); 
                    };
                } else if (data.task_type == 'I') {
                    registerClick = function(outcomeDict) {
                        users.tilesCardClick(
                            data.ctid,
                            data.sid,
                            data.card_index,
                            outcomeDict,
                            function(user) {
                                io.sockets.to(data.ctid).emit('click', user);
                            }
                        ); 
                    };
                }
                
                cards.click(
                    data,
                    // callback 'emitCard'
                    function(index, card) {
                        winston.info("communication >> " +
                                     " Broadcasting Card " + index + 
                                                      " (" + card.state + ")" +
                                     " in Completed Task " + data.ctid
                        );
                        var emitdict = { index : index, card : card };
                        io.sockets.to(data.ctid).emit('card', emitdict);
                    },
                    // callback 'registerClick'
                    registerClick,
                    // callback 'emitRoundEnd'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundEnd' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundEnd');
                    },
                    // callback 'emitRoundStart'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundStart' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundStart');
                    },
                    // callback 'emitScore'
                    function(score) {
                        io.sockets.to(data.ctid).emit('score', score);
                    }
                );
            });

            /*  @data -- A dictionary with keys:
                    #ctid    -- A CCI CompletedTask ID.
                    #sid     -- A CCI Subject ID.
                    #pieceId -- The pk of a Django SquaresPiece object.  */ 
            socket.on('squaresMousedown', function(data) {
                winston.info( "communication >> Received 'squaresMousedown' " 
                            + " from Subject " + data.sid 
                            + " in Completed Task " + data.ctid
                            );
                cards.squaresMousedown(
                    data
                  , // callback 'forceMouseup'
                    function(pieceId, resumeMousedown) {
                        var modifiedData = { ctid: data.ctid
                                           , sid: data.sid
                                           , pieceId: pieceId
                                           };
                        cards.squaresMouseup(
                            modifiedData
                          , // callback 'registerRelease'
                            function(releaseData, card) {
                                users.squaresRelease(
                                    releaseData, 
                                    // callback 'emitRelease'
                                    function(rd) {
                                        io.sockets.to(data.ctid).emit('squaresRelease', rd);
                                        if (resumeMousedown) {
                                            resumeMousedown();
                                        }
                                    },
                                    // callback 'emitScore'
                                    function(teamScore) {
                                        io.sockets.to(data.ctid).emit('score', teamScore);
                                    }
                                ); 
                            }
                          , // callback 'emitRoundEnd'
                            function() {
                                winston.info( "communication >> Broadcasting "
                                            + "'emitRoundEnd' for CT " + data.ctid + "."
                                            );
                                io.sockets.to(data.ctid).emit('roundEnd');
                            }
                          , // callback 'emitRoundStart'
                            function() {
                                winston.info( "communication >> Broadcasting "
                                            + "'emitRoundStart' for CT " + data.ctid + "."
                                            );
                                io.sockets.to(data.ctid).emit('roundStart');
                            }
                          , // callback 'emitCard' (for use when cards other than the 
                            // dragged card need to be repositioned as a result of this 
                            // move)
                            function(index, card) {
                                var d = { index: index
                                        , card: card 
                                        };
                                io.sockets.to(data.ctid).emit('card', d);
                            }
                        );
                    }
                  , // callback 'callback'
                    function(pickupData) {
                        users.squaresPickup(
                            data, 
                            pickupData,
                            // callback 'callback'
                            function(pData) {
                                io.sockets.to(data.ctid).emit('squaresPickup', pData);
                            }
                        ); 
                    }
                );
            });

            socket.on('squaresMousemove', function(data) {
                winston.debug( "communication >> Received 'squaresMousemove'" 
                             + " from Subject " + data.sid 
                             + " in Completed Task " + data.ctid
                             + " (piece ID: " + data.pieceId + ")"
                             );
                cards.squaresMousemove(
                    data,
                    // callback 'registerDrag'
                    function(dragData) {
                        users.squaresDrag(
                            dragData, 
                            // callback 'emitDrag'
                            function(dData) {
                                io.sockets.to(data.ctid).emit('squaresDrag', dData);
                            }
                        ); 
                    },
                    // callback 'forceMousedown'
                    function(resumeMousemove) {
                        cards.squaresMousedown(
                            data
                            // callback 'forceMouseup'
                          , function(pieceId, resumeMousedown) {
                                var modifiedData = { ctid: data.ctid
                                                   , sid: data.sid
                                                   , pieceId: pieceId
                                                   };
                                cards.squaresMouseup(
                                    modifiedData
                                  , // callback 'registerRelease'
                                    function(releaseData, card) {
                                        users.squaresRelease(
                                            releaseData, 
                                            // callback 'emitRelease'
                                            function(rd) {
                                                io.sockets.to(data.ctid).emit('squaresRelease', rd);
                                                if (resumeMousedown) {
                                                    resumeMousedown();
                                                }
                                            },
                                            // callback 'emitScore'
                                            function(teamScore) {
                                                io.sockets.to(data.ctid).emit('score', teamScore);
                                            }
                                        ); 
                                    }
                                  , // callback 'emitRoundEnd'
                                    function() {
                                        winston.info( "communication >> Broadcasting "
                                                    + "'emitRoundEnd' for CT " + data.ctid + "."
                                                    );
                                        io.sockets.to(data.ctid).emit('roundEnd');
                                    }
                                  , // callback 'emitRoundStart'
                                    function() {
                                        winston.info( "communication >> Broadcasting "
                                                    + "'emitRoundStart' for CT " + data.ctid + "."
                                                    );
                                        io.sockets.to(data.ctid).emit('roundStart');
                                    }
                                  , // callback 'emitCard' (for use when cards other than the 
                                    // dragged card need to be repositioned as a result of this 
                                    // move)
                                    function(index, card) {
                                        var d = { index: index
                                                , card: card 
                                                };
                                        io.sockets.to(data.ctid).emit('card', d);
                                    }
                                );
                            }
                          , // callback 'callback'
                            function(pickupData) {
                                users.squaresPickup(
                                    data, 
                                    pickupData,
                                    // callback 'callback'
                                    function(pData) {
                                        io.sockets.to(data.ctid).emit('squaresPickup', pData);
                                        if (resumeMousemove) {
                                            resumeMousemove();
                                        }
                                    }
                                ); 
                            }
                        );
                    }
                );
            });

            /*  @data -- A dictionary with keys:
                    #ctid    -- A CCI CompletedTask ID.
                    #sid     -- A CCI Subject ID.
                    #pieceId -- The pk of a Django SquaresPiece object.  */ 
            socket.on('squaresMouseup', function(data) {
                winston.info( "communication >> Received 'squaresMouseup' " 
                            + " from Subject " + data.sid 
                            + " in Completed Task " + data.ctid
                            );
                cards.squaresMouseup(
                    data
                  , // callback 'registerRelease'
                    function(releaseData, card) {
                        users.squaresRelease(
                            releaseData, 
                            // callback 'emitRelease'
                            function(rd) {
                                io.sockets.to(data.ctid).emit('squaresRelease', rd);
                            },
                            // callback 'emitScore'
                            function(teamScore) {
                                io.sockets.to(data.ctid).emit('score', teamScore);
                            }
                        ); 
                    }
                  , // callback 'emitRoundEnd'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundEnd' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundEnd');
                    }
                  , // callback 'emitRoundStart'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundStart' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundStart');
                    }
                  , // callback 'emitCard' (for use when cards other than the 
                    // dragged card need to be repositioned as a result of this 
                    // move)
                    function(index, card) {
                        var d = { index: index
                                , card: card 
                                };
                        io.sockets.to(data.ctid).emit('card', d);
                    }
                );
            });

            /*  @data -- A dictionary with keys:
                    #ctid -- A CCI CompletedTask ID.
                    #sid -- A CCI Subject ID.
                    #x    -- An integer.
                    #y    -- An integer.  */
            socket.on('positionCursor', function(data) {
//                winston.debug("communication >> Received 'positionCursor'" +
//                                                  " from Subject " + data.sid +
//                              " (" + data.x + ", " + data.y + ") " +
//                                             " in Completed Task " + data.ctid
//                );
                users.positionCursor(data, function(user) {
                    socket.broadcast.to(data.ctid).emit('cursor', user);
                });
            });

            /*  @ctid -- A CCI CompletedTask ID.
                @sid -- A CCI Subject ID.  */
            function removeCursor(ctid, sid) {
                socket.broadcast.to(ctid).emit('removeCursor', { sid: sid });
            }

            /*  @data -- A dictionary with keys:
                    #ctid -- A CCI CompletedTask ID.
                    #sid -- A CCI Subject ID.  */
            socket.on('removeCursor', function(data) {
                winston.info("communication >> Received 'removeCursor' " +
                                                        " from Subject " + data.sid +
                                                   " in Completed Task " + data.ctid
                );
                users.removeCursor(data, removeCursor);
                cards.squaresDisconnect(
                    data.ctid, 
                    data.sid,
                    // callback 'registerRelease'
                    function(releaseData) {
                        users.squaresRelease(
                            releaseData, 
                            // callback 'emitRelease'
                            function(rd) {
                                io.sockets.to(data.ctid).emit('squaresRelease', rd);
                            },
                            // callback 'emitScore'
                            function(teamScore) {
                                io.sockets.to(data.ctid).emit('score', teamScore);
                            }
                        ); 
                    },
                    // callback 'emitRoundEnd'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundEnd' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundEnd');
                    },
                    // callback 'emitRoundStart'
                    function() {
                        winston.info( "communication >> Broadcasting "
                                    + "'emitRoundStart' for CT " + data.ctid + "."
                                    );
                        io.sockets.to(data.ctid).emit('roundStart');
                    },
                    // callback 'emitCard' (for use when cards other than the 
                    // dragged card need to be repositioned as a result of this 
                    // move)
                    function(index, card) {
                        var d = { index: index
                                , card: card 
                                };
                        io.sockets.to(data.ctid).emit('card', d);
                    }
                );
            });

            socket.on('disconnect', function() {
                users.disconnect(socket, function(ctid, sid) {
                    winston.info("communication >> Received 'disconnect' " +
                                                          " from Subject " + sid +
                                                     " in Completed Task " + ctid
                    );
                    removeCursor(ctid, sid);
                    cards.squaresDisconnect(
                        ctid, 
                        sid,
                        // callback 'registerRelease'
                        function(releaseData) {
                            users.squaresRelease(
                                releaseData, 
                                // callback 'emitRelease'
                                function(rd) {
                                    io.sockets.to(ctid).emit('squaresRelease', rd);
                                },
                                // callback 'emitScore'
                                function(teamScore) {
                                    io.sockets.to(data.ctid).emit('score', teamScore);
                                }                                
                            ); 
                        },
                        // callback 'emitRoundEnd'
                        function() {
                            winston.info( "communication >> Broadcasting "
                                        + "'emitRoundEnd' for CT " + ctid + "."
                                        );
                            io.sockets.to(ctid).emit('roundEnd');
                        },
                        // callback 'emitRoundStart'
                        function() {
                            winston.info( "communication >> Broadcasting "
                                        + "'emitRoundStart' for CT " + ctid + "."
                                        );
                            io.sockets.to(ctid).emit('roundStart');
                        }
                    );
                });
            });
  
        });
    };
}());
