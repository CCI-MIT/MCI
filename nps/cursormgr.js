module.exports = function(redis, log) {

    var ehk = require('./eachHashKey')(log);
    var keynames = require('./keynames')(log);
    var _ = require('underscore');

    function exitWithError(err) {
        log('error', "cursor >> ERROR: " + err);
        process.exit(1);
    }

    function error(caller, ctid, sid, err) {
        log('error',
            "cursor >> "  + caller + "\n" +
            "    ctid: "  + ctid   + "\n" +
            "    sid: "   + sid    + "\n" +
            "    ERROR: " + err    + "\n");
        return;
    }

    /*  PARAMETERS:
            @ctid -- A CCI Completed Task ID.
            @apply -- A function expecting parameters:
                          @sid -- A CCI Subject ID.
                          @user -- A dictionary with keys:
                              #x:   an integer.
                              #y:   an integer.
            @continuation -- Either a function expecting no parameters,
                             or undefined.

        CONTRACT:
            This function maps over the users in the 'Concentration'-type
            Completed Task whose ID is ctid, calling 'apply' for each one.
            After the final call to 'apply', we call 'continuation'.  */
    this.eachUser = function(ctid, apply, continuation) {
        ehk(redis, keynames.subjects(ctid), apply, continuation);
    }
 
    /*  @socket -- A socket.io socket.
        @data   -- A dictionary with keys:
            #ctid -- A CCI Completed Task ID.
            #sid -- A CCI Subject ID.
            #x    -- An integer.
            #y    -- An integer.  */
    this.positionCursor = function(data, callback) {
        log('debug',
            'positionCursor >> Storing x, y for Subject ' + data.sid +
                                    ' in Completed Task ' + data.ctid);
        var hnss = keynames.subjects(data.ctid);
        redis.hget(hnss, data.sid, function(err, user_old_json) {
            if (err) {
                var caller = "positionCursor, retrieving user from Redis";
                return error(caller, data.ctid, data.sid, err);
            }
            var user_new = JSON.parse(user_old_json);
            if (!user_new) {
                var caller = "positionCursor";
                return error(caller, data.ctid, data.sid, "Could not deserialize user");
            } else {
                user_new.y = data.y;
                user_new.x = data.x;
                redis.hset(hnss, data.sid, JSON.stringify(user_new, null, 4));
                user_new.sid = data.sid;
                callback(user_new);
            }
        });
    }
  
    /*  @data   -- A dictionary with keys:
            #ctid -- A CCI Completed Task ID.
            #sid -- A CCI Subject ID.
        @callback -- A function expecting parameters:
                         @ctid -- A CCI Completed Task ID.
                         @sid -- A CCI Subject ID. */
    this.removeCursor = function(data, callback) {
        log('info',
            'removeCursor >> Storing x, y as -1, -1 for Subject ' + data.sid +
                                            ' in Completed Task ' + data.ctid);

        var hnss = keynames.subjects(data.ctid); 
        redis.hget(hnss, data.sid, function(err, user_old_json) {
            if (err) {
                var caller = "removeCursor, retrieving user from Redis";
                return error(caller, data.ctid, data.sid, err);
            }
            var user_new = JSON.parse(user_old_json);
            if (!user_new) {
                var caller = "removeCursor";
                return error(caller, data.ctid, data.sid, "Could not deserialize user");
            } else {
                user_new.x = user_new.y = -1;
                redis.hset(hnss, data.sid, JSON.stringify(user_new, null, 4));
                callback(data.ctid, data.sid);
            }
        });
    }

    this.squaresPickup = function(data, pickupData, callback) {
        var kncr = keynames.currentRound(data.ctid);
        var hnss = keynames.subjects(data.ctid);
        redis.get(kncr, function(err, round) {

            var emitData = { timestamp: new Date().getTime()
                           , round: round
                           , sid: data.sid
                           , pieceId: data.pieceId 
                           , pieces: pickupData.pieces
                           };
//            redis.rpush(keynames.squaresPickups(data.ctid),
//                        JSON.stringify(emitData, null, 4),
//                        function() {
//                redis.hget(hnss, data.sid, function(err, subject_json_pre) {
//                    var s = JSON.parse(subject_json_pre);
//                    s.pickups = Number(s.pickups) + 1;
//                    var subNewJson = JSON.stringify(s, null, 4);
//                    redis.hset(hnss, data.sid, subNewJson, function() {
//                        if (true /* TODO what actual checks should we do? */) {
                            callback(emitData);
//                        }
//                    });
//                });
//            });
        });
    }

    this.squaresDrag = function(data, emitDrag) {
        var kncr = keynames.currentRound(data.ctid);
        var hnss = keynames.subjects(data.ctid);
        redis.get(kncr, function(err, round) {
            var emitData = { timestamp: new Date().getTime()
                           , round: round
                           , setId: data.setId
                           , pieceId: data.pieceId 
                           , sid: data.giverSid
                           , alignedSetmates: data.alignedSetmates
                           , position: data.position
                           };
            emitDrag(emitData);
        });
    }

    this.squaresRelease = function(data, emitRelease, emitScore) {
        var kncr = keynames.currentRound(data.ctid);
        var hnss = keynames.subjects(data.ctid);
        var hnsm = keynames.squaresMoves(data.ctid);
        var knpg = keynames.pointsGlobal(data.ctid);
        redis.get(kncr, function(err, round) {
            var emitData = { timestamp: new Date().getTime()
                           , round: round
                           , setId: data.setId
                           , pieceId: data.pieceId 
                           , piece: data.piece
                           , sid: data.giverSid
                           , giverSid: data.giverSid
                           , receiverSid: data.receiverSid
                           , outcome: data.outcome
                           , position: data.position
                           , piecesPerSubject: data.subjectsByPieceCt
                           , alignedSetmates: data.alignedSetmates
                           };
            var edj = JSON.stringify(emitData, null, 4);

            var moveOutcomes = [ "partial match"
                               , "complete match"
                               , "no match"
                               ];
            function isOutcome(mo) {
                  var retval = data.outcome == mo;
                  return retval;
            }

            // CASE:  We need to report this move.
            if (data.giverSid != data.receiverSid && _.some(moveOutcomes, isOutcome)) {
                redis.rpush(hnsm, edj, function() {
                    redis.hget(hnss, data.giverSid, function(err, subject_json_pre) {
                        if (err) { exitWithError(err); } 
                        var giver = JSON.parse(subject_json_pre);
                        var rSid = data.receiverSid;
                        if (!giver.moves) { giver.moves = 0; }
                        giver.moves = Number(giver.moves) + 1;
                        if (!giver.interactions) { giver.interactions = {}; }
                        if (!giver.interactions[rSid]) { giver.interactions[rSid] = 0; }
                        giver.interactions[rSid] = Number(giver.interactions[rSid]) + 1;
                        if (data.outcome == "partial match") {
                            if (!giver.partialMatches) { giver.partialMatches = 0; }
                            giver.partialMatches = Number(giver.partialMatches) + 1;
                        } else if (data.outcome == "complete match") {
                            if (!giver.completeMatches) { giver.completeMatches = 0; }
                            giver.completeMatches = Number(giver.completeMatches) + 1;
                        }
                        var giverNewJson = JSON.stringify(giver, null, 4);
                        redis.hset(hnss, data.giverSid, giverNewJson, function() {
                            emitRelease(emitData);
                            redis.get(knpg, function(err, teamScore) {
                                if (data.outcome == "complete match") {
                                    var tsNew = Number(teamScore) + 1;
                                    redis.set(knpg, tsNew, function() {
                                        emitScore(tsNew);
                                    });
                                }
                            });
                        });
                    });
                });
            }
            // CASE:  We don't need to report this move.
            else {
                emitRelease(emitData);
            }

        });
    }

    function recordCardClick(ctid, sid, index, cardClickData, round) {
        var clickJson = JSON.stringify({ timestamp: new Date().getTime()
                                       , round: round
                                       , sid: sid
                                       , index: index 
                                       // Only used for Concentration...
                                       , outcome: cardClickData.outcome
                                       // Only used for Tiles...
                                       , correct: cardClickData.correct
                                       , selection: cardClickData.in_selection
                                       , pattern: cardClickData.in_pattern
                                       , corrected: cardClickData.correctedSid
                                       }, null, 4)
        redis.rpush(keynames.clicks(ctid), clickJson);
    }        
    function recordSubmitClick(ctid, sid, rndIndex, submitClickData) {
        var submitClickJson = JSON.stringify(
            { timestamp: new Date().getTime()
            , round: submitClickData.round
            , sid: sid
            , outcome: submitClickData.outcome
            , teamScoreChange: submitClickData.teamScoreChange
            , newTeamScore: submitClickData.teamScore
            , tiles: submitClickData.tileCount
            }, null, 4)
        redis.rpush(keynames.submitClicks(ctid), submitClickJson);
    }

    this.tilesSubmitClick = function(ctid, clicker_sid, rndIndex, submitClickData) {

        var hnss = keynames.subjects(ctid);
        recordSubmitClick(ctid, clicker_sid, rndIndex, submitClickData); 

        redis.hget(hnss, clicker_sid, function(err, clicker_json_pre) {

            var clicker = JSON.parse(clicker_json_pre);

            if (submitClickData.outcome == 'success') {
                clicker.correctSubmitClicks =
                    Number(clicker.correctSubmitClicks) + 1;
            } else if (submitClickData.outcome == 'failure') {
                clicker.incorrectSubmitClicks =
                    Number(clicker.incorrectSubmitClicks) + 1;
            } else {
                var scdJson = JSON.stringify(submitClickData, null, 4);
                exitWithError("Illegal round outcome upon submitClick.  Data: " +
                              scdJson);
            }
            redis.hset(hnss, clicker_sid, JSON.stringify(clicker, null, 4));
        });
    }

    this.tilesCardClick = function(ctid, clicker_sid, cardIndex, cardClickData, emitClick) {
        var kncr = keynames.currentRound(ctid);
        var hnss = keynames.subjects(ctid);

        redis.get(kncr, function(err, round) {

            recordCardClick(ctid, clicker_sid, cardIndex, cardClickData, round); 
    
            redis.hget(hnss, clicker_sid, function(err, clicker_json_pre) {
    
                var clicker = JSON.parse(clicker_json_pre);
     
                clicker.clicks = Number(clicker.clicks) + 1;
                if (cardClickData.correct) {
                    if (!clicker.uniqueTilesCorrectlyClicked[round]) {
                        clicker.uniqueTilesCorrectlyClicked[round] = {};
                    }
                    clicker.uniqueTilesCorrectlyClicked[round][cardIndex] = true;
                    clicker.netScore = Number(clicker.netScore) + 1;
                } else {
                    if (!clicker.uniqueTilesIncorrectlyClicked[round]) {
                        clicker.uniqueTilesIncorrectlyClicked[round] = {};
                    }
                    clicker.uniqueTilesIncorrectlyClicked[round][cardIndex] = true;
                    clicker.netScore = Number(clicker.netScore) - 1;
                }
                if (cardClickData.correctedSid &&
                    cardClickData.correctedSid != clicker_sid) {
    
                    // Mutate 'clicker', as well as our stored data about the corrected Subject. 
                    redis.hget(hnss, cardClickData.correctedSid,
                               function(err, corrected_json_pre) {
                        var corrected = JSON.parse(corrected_json_pre);
                        if (cardClickData.correct) {
                            corrected.timesCorrectlyCorrected = 
                                Number(corrected.timesCorrectlyCorrected) + 1;
                            clicker.correctCorrections        = 
                                Number(clicker.correctCorrections) + 1;
                        } else {
                            corrected.timesIncorrectlyCorrected = 
                                Number(corrected.timesIncorrectlyCorrected) + 1;
                            clicker.incorrectCorrections        = 
                                Number(clicker.incorrectCorrections) + 1;
                        }
                        var newCorrected = JSON.stringify(corrected, null, 4);
                        redis.hset(hnss, cardClickData.correctedSid,
                                   newCorrected, function() {
                            redis.hset(hnss, clicker_sid,
                                       JSON.stringify(clicker, null, 4),
                                       function() { emitClick(clicker); });
                        });
                    });
                } else {
                    redis.hset(hnss, clicker_sid,
                               JSON.stringify(clicker, null, 4),
                               function() { emitClick(clicker); });
                }
            });
        });
    }


    this.concentrationCardClick = function(ctid, clicker_sid, index, outcome, emitClick) {
        var hnss = keynames.subjects(ctid);

        var finish_up = function(clicker) {
            var clicker_json_post = JSON.stringify(clicker, null, 4);
            redis.hset(hnss, clicker_sid, clicker_json_post, function() {
                emitClick(clicker);
            });
        }

        redis.get(keynames.currentRound(ctid), function(err, round) {
            recordCardClick(ctid, clicker_sid, index, { outcome: outcome }, round); 
            redis.hget(hnss, clicker_sid, function(err, clicker_json_pre) {
                var clicker = JSON.parse(clicker_json_pre);
                // TODO:  Should this next line be necessary?  Can't we just store
                //        the sid from the word go?
                clicker.sid = clicker_sid;
                if (!clicker.clicks) {
                    clicker.clicks = 1;
                } else {
                    clicker.clicks = Number(clicker.clicks) + 1;
                }
                if (outcome == 'setup') {
                    redis.set(keynames.currentAssister(ctid), clicker_sid, function() {
                        finish_up(clicker);
                    });
                } else if (outcome == 'match') {
                    if (!clicker.score) {
                        clicker.score = 0.5;
                    } else {
                        clicker.score = Number(clicker.score) + 0.5;
                    }
                    var clicker_json_post = JSON.stringify(clicker, null, 4);
                    redis.hset(hnss, clicker_sid, clicker_json_post, function() {
                        redis.get(keynames.currentAssister(ctid), function(err, assister_sid) {
                            redis.hget(hnss, assister_sid, function(err, assister_json_pre) {
                                var assister = JSON.parse(assister_json_pre);
                                if (!assister.score) {
                                    assister.score = 0.5;
                                } else {
                                    assister.score = Number(assister.score) + 0.5;
                                }
                                var assister_json_post = JSON.stringify(assister, null, 4);
                                redis.hset(hnss, assister_sid, assister_json_post, function() {
                                    emitClick(clicker);
                                });
                            });
                        });
                    });
                } else {
                    finish_up(clicker);
                }
            });
        });
    }

    this.disconnect = function(socket, callback) {
        socket.get('ctid', function(err, ctid) {
            if (err) {
                var caller = "disconnect, retrieving ctid from socket object";
                return error(caller, "(unknown)", "(unknown)", err);
            }
            var hnss = keynames.subjects(ctid);
            socket.get('sid', function(err, sid) {
                if (err) {
                    var caller = "disconnect, retrieving sid from socket object";
                    return error(caller, ctid, "(unknown)", err);
                }
                redis.hget(hnss, sid, function(err, user_old_json) {
                    if (err) {
                        var caller = "disconnect, retrieving user from Redis";
                        return error(caller, ctid, sid, err);
                    }
                    var user_new = JSON.parse(user_old_json);
                    if (!user_new) {
                        var caller = "disconnect";
                        return error(caller, ctid, sid, "Could not deserialize user");
                    } else {
                        user_new.x = user_new.y = -1;
                        redis.hset(hnss, sid, JSON.stringify(user_new, null, 4));
                        callback(ctid, sid);
                    }
                });
            });
        });

    }

    return this;    
};
