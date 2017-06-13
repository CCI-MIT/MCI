/*  SOME NOTES:
      - Legal card 'state' values:
          'facedown', 'faceup', 'nomatch', 'matched', 'finalmatch'
        TODO: 'nomatch' and 'finalmatch' aren't really states.  I should be
              using explicit event signals instead of abusing my state change
              signal.
        TODO: is the above doco even current anymore?
*/

module.exports = function(redis, log, cnf, env) {
    var http = require("http");
    var keynames = require('./keynames')(log);
    var ehk = require('./eachHashKey')(log);
    var dateFromString = require('./date_from_string');
    var _ = require('underscore');

    function hashnameRoundCards(ctid, callback) {
        var hncr = keynames.currentRound(ctid);
        redis.get(hncr, function(err, round) {
            if (err) { exitWithError(err); }
            var rnd_index;
            if (round) {
                rnd_index = round;
            } else {
                redis.set(hncr, 0);
                rnd_index = 0;
            }
            callback(keynames.roundCards(ctid, rnd_index), rnd_index);
        });
    }

    function exitWithError(err) {
        log('error', "click >> ERROR: " + err);
        process.exit(1);
    }

    function incrementGlobalScore(ctid, callback) {
        var kn_pts_global = keynames.pointsGlobal(ctid);
        redis.get(kn_pts_global, function(err, score) {
            if (err) { exitWithError(err); }
            var score_new = Number(score) + 1;  
            redis.set(kn_pts_global, score_new, function() {
                callback(score_new);
            });
        });
    }

    function incrementConcentrationRound(ctid, ctvs, emitRoundEnd, emitRoundStart) {
        function increment() {
            var hncr = keynames.currentRound(ctid);
            redis.get(hncr, function(err, round) {
                if (err) { exitWithError(err); }
                redis.set(hncr, Number(round) + 1, emitRoundStart);
            });
        }
        emitRoundEnd();
        setTimeout(increment, Number(ctvs.seconds_between_rounds) * 1000);
    }

    function incrementSquaresRound(ctid, ctvs, emitRoundEnd, emitRoundStart) {
        function increment() {
            var hncr = keynames.currentRound(ctid);
            redis.get(hncr, function(err, round) {
                if (err) { exitWithError(err); }
                redis.set(hncr, Number(round) + 1, emitRoundStart);
            });
        }
        emitRoundEnd();
        setTimeout(increment, Number(ctvs.seconds_between_rounds) * 1000);
    }    

    /*  @ctid -- A CCI Completed Task ID.
        @apply -- A function expecting parameters:
                      @card_index -- The index of a card in the 'Concentration'-
                                     type Completed Task whose ID is @ctid.
                      @card       -- A dictionary with keys:
                                         #url   -- The URL of a card image.
                                         #state -- A card state string.
        @continuation -- A function expecting no parameters. 

        This function maps over the cards in the 'Concentration'-type
        Completed Task whose ID is ctid, calling 'apply' for each one.
        After the final call to 'apply', we call 'continuation'.       */
    this.eachCardInCurrentRound = function(ctid, apply, continuation) {
        hashnameRoundCards(ctid, function(hashname) {
            ehk(redis, hashname, apply, continuation);
        });
    }

    function storeCard(ctid, index, card, callback) {
        hashnameRoundCards(ctid, function(hn) {
            redis.hset(hn, index, JSON.stringify(card, null, 4), callback);
        });
    }

    // Designed to be called *by* a timeout -- in other words, knows nothing
    // about when a CT's first round's preview should begin.
    this.tilesPreview = function(data, emitRoundPreview, emitRoundStart,
                            previewTime, timeTilPreviewStart, currentTime) {

        // Set current round's preview_end_time, for use in filering click events.
        var timeTilPreviewEnd = timeTilPreviewStart + previewTime,
            hncr = keynames.currentRound(data.ctid);
        redis.get(hncr, function(err, round) {
            if (err) { exitWithError(err); }
            var hnrv = keynames.roundVars(data.ctid, round);
//            log("info", "currentTime: " + (currentTime));
//            log("info", "timeTilPreviewEnd: " + (timeTilPreviewEnd));
//            log("info", "preview end time as we're about to store it: " +
//                  (currentTime - (0 - timeTilPreviewEnd)));
            redis.hset(hnrv, 'preview_end_time',
                       currentTime - (0 - timeTilPreviewEnd));
        });

        if (timeTilPreviewEnd > 0) {
            hashnameRoundCards(data.ctid, function(hnc) {
                // Schedule the preview.
                function matchPattern(i) {
                    if (!i) i = 0;
                    redis.hget(hnc, i, function(err, cj) {
                        if (err) { exitWithError(err); }
                        if (cj) {
                            var newCard = JSON.parse(cj);
                            newCard.in_selection = newCard.in_pattern;
                            redis.hset(hnc, i, JSON.stringify(newCard, null, 4),
                                       function() {
                                matchPattern(i + 1);
                            });
                        } else {
                            emitRoundPreview();
                        }
                    });
                }
                setTimeout(matchPattern, timeTilPreviewStart);
                // Schedule the preview's end.
                function deselect(i) {
                    if (!i) i = 0;
                    redis.hget(hnc, i, function(err, cj) {
                        if (err) { exitWithError(err); }
                        if (cj) {
                            var newCard = JSON.parse(cj);
                            newCard.in_selection = 'off';
                            var ncJson = JSON.stringify(newCard, null, 4);
                            redis.hset(hnc, i, ncJson, function() {
                                deselect(i + 1);
                            });
                        } else {
                            emitRoundStart();
                        }
                    });
                }                      
                setTimeout(deselect, timeTilPreviewEnd);
            });
        }
    }

    this.submitClick = function(data, emitSubmit, emitRoundEnd, emitRoundPreview,
                                emitRoundStart, emitError, registerSubmitClick) { 
        emitSubmit();
        var hncr = keynames.currentRound(data.ctid);
        redis.get(hncr, function(err, round) {
            if (err) { exitWithError(err); }
            // First we need to compute the current round's outcome, since
            // that needs to be saved before we do the req to the Django app.
            var allCorrect = true
              , selection = []
              , pattern = []
              , pointsInRound = 0
              , tilesInRound = 0
              ;
            this.eachCardInCurrentRound(
                data.ctid,
                function(i, c, applyCont) {
                    tilesInRound++;
                    if (c.in_selection == 'on') {
                        selection.push({ index: i, card: c });
                    }
                    if (c.in_pattern == 'on') {
                        pattern.push({ index: i, card: c });
                    }
                    if (c.in_pattern == 'on') {
                        pointsInRound++;
                    }
                    if (c.in_selection != c.in_pattern) {
                        allCorrect = false;
                    }
                    applyCont();
                }, function() {
                    var outcome = allCorrect ? 'success' : 'failure';
                    var hn_rv = keynames.roundVars(data.ctid, round);
                    redis.hset(hn_rv, 'outcome', outcome, function() {
                        // TODO: compile from a *shared* conf file if possible,
                        // so that this URL is guaranteed correct
                        http.get({
                            host: 'localhost',
                            port: cnf.get(env + ':djangoport'),
                            path: '/mci/session/task/' + data.ctid +
                                  '/configureNextRound'
                        }, function(res) {
                            res.on("data", function(chunk) {
                                var chunkObj = JSON.parse(chunk);
                                if (chunkObj.error) {
                                    emitError();
                                } else {
                                    var teamScoreChange = allCorrect ?
                                                          pointsInRound : 0;
                                    var knpg = keynames.pointsGlobal(data.ctid);
                                    redis.get(knpg, function(err, oldTeamScore) {
                                        if (err) { exitWithError(err); }
                                        var newTeamScore = Number(oldTeamScore)
                                                         + teamScoreChange;
                                        redis.set(keynames.pointsGlobal(data.ctid),
                                                  newTeamScore, function() {
                                            var outcomeData =
                                                { selection: selection
                                                , pattern: pattern
                                                , outcome: outcome
                                                , teamScoreChange: teamScoreChange
                                                , teamScore: newTeamScore
                                                , round: round
                                                , tileCount: tilesInRound
                                                }
                                            registerSubmitClick(
                                                outcomeData, round);
                                            var knCtvs = keynames.ctVars(data.ctid);
                                            redis.get(knCtvs, function(err, ctvsJson) {
                                                if (err) { exitWithError(err); }
                                                var ctvs = JSON.parse(ctvsJson);
                                                var btwnRnds = ctvs.seconds_between_rounds;
                                                emitRoundEnd(outcomeData);
                                                setTimeout(function() {
                                                    var newRnd = Number(round) + 1;
                                                    redis.set(hncr, newRnd, function() {
                                                        var tps = ctvs.tiles_preview_seconds;
                                                        this.tilesPreview(
                                                            data,
                                                            emitRoundPreview,
                                                            emitRoundStart,
                                                            Number(tps) * 1000,
                                                            0,
                                                            new Date()
                                                        );
                                                    });
                                                    // NOTE: 3 accomodates the
                                                    // 'board strip' effect.
                                                }, (Number(btwnRnds)+3)*1000);
                                            });
                                        });
                                    });
                                }
                            });
                        }).on('error', function(e) {
                            log('info', 'ERROR: ' + e.message);
                            emitError();
                        });
                    });
            });
        }); 
    } 

    this.scheduleRoundStartIfAppropriate = function(data, emitRoundPreview, 
                                                    emitRoundStart, continuation) {
        var knCtvs = keynames.ctVars(data.ctid);
        redis.get(knCtvs, function(err, ctvsJson) {
            if (err) { exitWithError(err); }
            var ctvs = JSON.parse(ctvsJson);
            if (!ctvs.first_round_preview_scheduled) {
                ctvs.first_round_preview_scheduled = true;
                redis.set(knCtvs, JSON.stringify(ctvs, null, 4), function() {
                    var pst = ctvs.play_start_time,
                        tps = ctvs.tiles_preview_seconds;
                    var currentTime         = new Date(),
                        previewStartTime    = dateFromString(pst),
                        previewDuration     = Number(tps) * 1000,
                        previewEndTime      = previewStartTime + previewDuration,
                        timeTilPreviewEnd   = previewEndTime - currentTime,
                        timeTilPreviewStart = previewStartTime - currentTime;
                    this.tilesPreview(data, emitRoundPreview, emitRoundStart,
                                      previewDuration, timeTilPreviewStart,
                                      currentTime
                    );
                    if (continuation) { continuation(); }
                });
            } else {
                if (continuation) { continuation(); }
            }
        });
    }

    function ptBoardAreaSid(board_areas, point) {
        for (var sid in board_areas) {
            var ba = board_areas[sid];
            if ( ba.tl.x <  point.x
              && ba.tl.y <  point.y
              && ba.br.x >= point.x
              && ba.br.y >= point.y
               ) { return sid; }
        }
        var pointStr = JSON.stringify(point);
        var basStr = JSON.stringify(board_areas, null, 4);
        // TODO: handle the exceptional case where we haven't returned yet.
    }
    function ptBoardAreaTopLeft(board_areas, point) {
        for (var sid in board_areas) {
            var ba = board_areas[sid];
            if ( ba.tl.x <  point.x
              && ba.tl.y <  point.y
              && ba.br.x >= point.x
              && ba.br.y >= point.y
               ) { return ba.tl; }
        }
        // TODO: handle the exceptional case where we haven't returned yet.
    }

    this.displaySubmitButtonIfAppropriate = function(data, emitDisplay) {

        var timeoutMs = 1000;

        var timestamp = JSON.stringify(new Date());
        var hnFlags = keynames.tilesDsbiaFlags(data.ctid);
        var sid = data.sid;
        var knCtvs = keynames.ctVars(data.ctid);
 
        function carryTheBall() {
            //  - If we're past the CT's endtime:
            //      - Return.  I.e. no timeout/recurse.
            //  - Else:
            //      - If whether we're before CT's start time:
            //          - Recurse on timeout.
            //      - Else:
            //          - If we're before current rnd's preview end time:
            //              - Recurse on timeout. 
            //          - Else:
            //              - Emit the msg.
            //              - Recurse on timeout.
            var currentDate = new Date();
            redis.get(knCtvs, function(err, ctvsJson) {
                if (err) { exitWithError(err); }
                var ctvs = JSON.parse(ctvsJson);
                var endDate = dateFromString(ctvs.play_end_time);
                if (currentDate > endDate) { 
                    return;
                } else {
                    var startDate = dateFromString(ctvs.play_start_time);
                    if (currentDate >= startDate) {
                        var hncr = keynames.currentRound(data.ctid);
                        redis.get(hncr, function(err, round) {
                            if (err) { exitWithError(err); }
                            var hnrv = keynames.roundVars(data.ctid, round);
                            function petCallback(err, previewEnd) {
                                if (err) { exitWithError(err); }
                                if (!previewEnd) { return }
                                var previewEndDate = new Date(Number(previewEnd));
                                if (currentDate >= previewEndDate) {
                                    emitDisplay();
                                }
                            }
                            redis.hget(hnrv, 'preview_end_time', petCallback);
                        });
                    }
                    setTimeout(
                        dsbia,
                        // This timeout interval must be less than time_between_rounds
                        // + preview_time; otherwise the timeout's payload might
                        // recurse at the beginning of the next round -- which means it
                        // would be duplicated, since at the beginning of the next
                        // round allState is sent.  OR -- maybe the timeout payload
                        // should close over a 'round' parameter, which would be
                        // compared with currentRound when it fires, to ensure that it
                        // only recurses if we're still in the current round.
                        timeoutMs
                    );
                }
            });
        }

        function dsbia() {
            //  - If the flag is set:
            //      - If our timestamp is its key:
            //          - Carry the ball.
            //      - Else:
            //          - Return.  I.e. don't set anothing timeout to recurse.
            //  - Else:
            //      - Set the flag, with our timestamp as its key.
            //      - Carry the ball.
            redis.hget(hnFlags, sid, function(err, flag) {
                function setFlagAndCarryTheBall() {
                    redis.hset(hnFlags, sid, timestamp, function(err) {
                        if (err) { exitWithError(err); }
                        carryTheBall();
                    });
                }
                if (err) { exitWithError(err); }
                if (flag) {
                    if (flag == timestamp) {
                        carryTheBall();
                    } else {
                        var flagDate = new Date(JSON.parse(flag));
                        var flagDateMs = flagDate.getMilliseconds();
                        flagDate.setMilliseconds(flagDateMs + timeoutMs);
                        if (new Date() > flagDate) {
                            setFlagAndCarryTheBall();
                        }
                    }
                } else {
                    setFlagAndCarryTheBall();
                }
            });
        }
        dsbia();
    };

    function roundEvent(d, dkey, processEvent) {
        var currentDate = new Date();
        var knCtvs = keynames.ctVars(d.ctid);
        redis.get(knCtvs, function(err, ctvsJson) {
            if (err) { exitWithError(err); }
            var ctvs = JSON.parse(ctvsJson);
            var startDate = dateFromString(ctvs.play_start_time);
            var endDate = dateFromString(ctvs.play_end_time);
            if (currentDate < startDate || currentDate > endDate) { return }
            hashnameRoundCards(d.ctid, function(hashname, rnd_index) {
                redis.hget(hashname, d[dkey], function(err, card_json) {
                    if (err) { exitWithError(err); }
                    var card = JSON.parse(card_json);
                    if (card) {
                        processEvent(currentDate, ctvs, startDate, endDate, card);
                    } else {
                        log( 'info'
                           , "roundEvent >> CT " + d.ctid + " Rnd " + rnd_index
                           + " has no card at index " + dkey + "."
                           );
                    }
                });
            });
        });
    }

    this.squaresMousedown = function(data, forceMouseup, callback) {
        roundEvent(data, 'pieceId', 
                   function(currentDate, ctvs, startDate, endDate, card) {
            var hncr = keynames.currentRound(data.ctid);
            redis.get(hncr, function(err, round) {
                if (err) { exitWithError(err); }
                    
                log( 'info', "squaresMousedown >> Subject " + data.sid 
                   + " mousedown on piece " + data.pieceId + "."
                   );
                var bas = JSON.parse(ctvs.board_areas);
                var av = card.avg_vertex;
                var point = { x: card.position.x + av.x
                            , y: card.position.y + av.y
                            }
                var owner_sid = ptBoardAreaSid(bas, point);
                // CASE:  Card is outside subject's board area.
                //        Ignore the mousedown.
                if (owner_sid != data.sid) {
                    log( 'debug', "squaresMousedown >> Subject " 
                       + data.sid + " doesn't own piece " 
                       + data.pieceId + ".  (We're going to force a mouseup "
                       + "on it.)"
                       );
                    forceMouseup(data.pieceId);
                }
                // CASE:  Card is in subject's board area.
                else {
                    // CASE:  Card was already in 'drag_mode'.
                    //        Log an error and do nothing else.
                    if (card.drag_mode) {
                        log( 'error', "squaresMousedown >> Piece " 
                           + data.pieceId + " "
                           + "was already in drag mode!  It " 
                           + "should not be possible for the " 
                           + "piece to be in drag mode at the " 
                           + "moment when its owner mouses " 
                           + "down on it."
                           );
                    }
                    // CASE:  The card isn't already in drag mode.
                    else {
                        log( 'debug', "squaresMousedown >> Subject "
                           + data.sid + " is now dragging piece "
                           + data.pieceId + "."
                           );
                    }
                    card.dragger = data.sid;
                    card.drag_mode = true;
                    var current_dragged = [];
                    //  Keep state clean by forcing Mouseup on any currently
                    //  dragged pieces.
                    eachCardInCurrentRound(
                        data.ctid, 
                        function(i, p, applyCont) {
                            if (p.drag_mode && p.dragger == data.sid) {
                                forceMouseup(p.piece_id, applyCont);
                            } else {
                                applyCont(); 
                            } 
                        }, 
                        function() {
                            storeCard(data.ctid, data.pieceId, card, function() {
                                var pieces = []; 
                                eachCardInCurrentRound(
                                    data.ctid, 
                                    function(i, p, applyCont) { 
                                        pieces.push(p);
                                        applyCont(); 
                                    }, 
                                    function() { 
                                        callback({ pieces: pieces }); 
                                    }
                                );
                            });
                        }
                    ); 
                }
            }); 
        });        
    }

    function avgVx(pos, card) {
        var av = card.avg_vertex;
        return { x: pos.x + av.x
               , y: pos.y + av.y
               }
    }

    function currentAvgVx(card) {
        return avgVx(card.position, card);
    }
    function returnAvgVx(card) {
        return avgVx(card.return_position, card);
    }

    function boardAreaSetmates(bas, pieces, piece) {
        var pieceAv = currentAvgVx(piece);
        var pieceBoardArea = ptBoardAreaSid(bas, pieceAv);
        var ps = [];
        for (var i = 0; i < pieces.length; i++) {
            var p = pieces[i];
            var pAv = currentAvgVx(p);
            var pBoardArea = ptBoardAreaSid(bas, pAv);
            if ( p.piece_id != piece.piece_id
              && p.set_id == piece.set_id
              && pBoardArea == pieceBoardArea ) {
                ps.push(p);
            }
        }
        return ps;
    }

    var matchDistance = cnf.get("matchDistance");
    function alignedSetmates(pieces, piece) {
        var ps = [];
        for (var i = 0; i < pieces.length; i++) {
            var p = pieces[i];
            if (p.piece_id != piece.piece_id && p.set_id == piece.set_id) {
                var distX = Math.abs(p.position.x - piece.position.x);
                var distY = Math.abs(p.position.y - piece.position.y);
                var dist = Math.sqrt(Math.pow(distX, 2) + Math.pow(distY, 2))
                if (dist < matchDistance) {
                    ps.push(p);
                }
            }
        }
        return ps;
    }

    var overlapDistance = cnf.get("overlapDistance");
    function overlappingPieces(pieces, piece) {
        var ps = [];
        for (var i = 0; i < pieces.length; i++) {
            var p = pieces[i];
            if (p.piece_id != piece.piece_id) {
                var avgVx1 = currentAvgVx(p);
                var avgVx2 = currentAvgVx(piece);
                var distX = Math.abs(avgVx1.x - avgVx2.x);
                var distY = Math.abs(avgVx1.y - avgVx2.y);
                var dist = Math.sqrt(Math.pow(distX, 2) + Math.pow(distY, 2))
                if (dist < overlapDistance) {
                    ps.push(p);
                }
            }
        }
        return ps;
    }    

    this.squaresMousemove = function(d, registerDrag, forceMousedown) {
        roundEvent(d, 'pieceId', 
                   function(currentDate, ctvs, startDate, endDate, card) {
            // CASE:  Subject wasn't dragging the piece in the
            //        first place.

            function doTheMove() {

                card.position = { x: d.mousePosition.x - card.avg_vertex.x
                                , y: d.mousePosition.y - card.avg_vertex.y
                                };
                var bas = JSON.parse(ctvs.board_areas);
                var _avc = currentAvgVx(card);
                var dest_sid = ptBoardAreaSid(bas, _avc);

                var bc;
                // CASE:  We're in the same board area.
                var pieces = [];
                this.eachCardInCurrentRound(
                    d.ctid, 
                    function(i, p, applyCont) { 
                        pieces.push(p);
                        applyCont();
                    }, 
                    // continuation
                    function() {
                        var in_board_area = 0;
                        for (var i=0; i < pieces.length; i++) {
                            var p = pieces[i];
                            var avc = currentAvgVx(p);
                            var avr = returnAvgVx(p);
                            if (p.piece_id != d.pieceId && 
                               (ptBoardAreaSid(bas, avc) == dest_sid || 
                                ptBoardAreaSid(bas, avr) == dest_sid)) {
                                in_board_area += 1;
                            }
                        }
                        var aligned_setmates = alignedSetmates(pieces, card);
                        var alignedSetmatesObj = {};
                        if (alignedSetmates) {
                            for (var i=0; i < aligned_setmates.length; i++) {
                                var p = aligned_setmates[i];
                                alignedSetmatesObj[p.piece_id] = p;
                            }
                        }
                        storeCard(d.ctid, d.pieceId, card, function() {
                            var dragData = { ctid: d.ctid
                                           , setId: card.set_id
                                           , pieceId: card.piece_id
                                           , sid: d.sid
                                           , borderCrossing: bc
                                           , alignedSetmates: alignedSetmatesObj
                                           , position: card.position
                                           };
                            registerDrag(dragData);
                        }); 
                    }
                );
            }

            if (card.dragger == d.sid) 
            // CASE:  Subject *was already* dragging the piece.
            {
                doTheMove(d);
            } else
            //  CASE: Subject *wasn't already* dragging the piece.
            {
                log( 'error', "squaresMousemove >> Subject " + d.sid + " "
                   + "wasn't known to be dragging piece " + card.piece_id 
                   + ".  We're going to try forcing a mousedown event."
                   );
                forceMousedown(function() {
                    roundEvent(d, 'pieceId', 
                               function(_currentDate, ctvs, _startDate, _endDate, card) {
                        if (card.dragger == d.sid) 
                        // CASE: Subject *is now* dragging the piece.
                        {
                            log( 'error', "squaresMousemove >> A call to forceMousedown "
                               + "straightened things out for Subject " + d.sid + " "
                               + "and their mousemove!"
                               );
                            doTheMove();
                        }
                        else
                        // CASE: Subject *still isn't* dragging the piece.
                        {
                            log( 'error', "squaresMousemove >> Even after "
                               + " call to forceMousedown, Subject " + d.sid
                               + "wasn't dragging piece " + card.piece_id 
                               + ".  Ignoring this event."
                               );
                        } 
                    });
                });
            }
        });
    }    

    this.squaresMouseup = function(d, registerRelease, emitRoundEnd,
                                   emitRoundStart, emitCard) {
        roundEvent(d, 'pieceId',
                   function(currentDate, ctvs, startDate, endDate, card) {
            log( 'info', "squaresMouseup >> Subject " + d.sid
               + ", piece " + d.pieceId + "."
               );                        
            // CASE:  Subject wasn't dragging the piece in the
            //        first place.
            if (card.dragger != d.sid) {
                log( 'error', "squaresMouseup >> Subject " + d.sid + " "
                   + "wasn't dragging piece " + d.pieceId + ".  (We're going "
                   + "to emit the squaresMouseup message just in case any "
                   + "client has the idea that this subject is dragging this "
                   + "piece.)"
                   );
                card.position = card.return_position;
                storeCard(d.ctid, d.pieceId, card, function() {
                    var rrData = { ctid: d.ctid
                                 , setId: card.set_id
                                 , pieceId: card.piece_id
                                 , giverSid: d.sid
                                 , outcome: ( "doing this because subject seemed "
                                            + "to think it was dragging this piece"
                                            )
                                 , position: card.return_position
                                 };
                    registerRelease(rrData, card);
                });
            }
            // CASE:  Subject was dragging the piece.  We'll count
            //        it as released.
            else {
                card.dragger = undefined;
                card.drag_mode = false;

                var bas = JSON.parse(ctvs.board_areas);
                var avc = currentAvgVx(card);
                var dest_sid = ptBoardAreaSid(bas, avc);

                // CASE:  The piece was dropped outside any board area,
                //        as e.g. when there are 5 players and thus a sixth
                //        of the board isn't part of an area.
                if (!dest_sid) {
                    log( 'info', "squaresMouseup >> Subject " + d.sid + " "
                       + "dropped piece " + d.pieceId + " outside any "
                       + "board area."
                       );
                    card.position = card.return_position;
                    storeCard(d.ctid, d.pieceId, card, function() {
                        var rrData = { ctid: d.ctid
                                     , setId: card.set_id
                                     , pieceId: card.piece_id
                                     , giverSid: d.sid
                                     , outcome: "failed (outside board)"
                                     , position: card.position
                                     };
                        registerRelease(rrData, card);
                    });
                }
                // CASE:  The piece was dropped inside a board area.
                else {
                    log( 'info', "squaresMouseup >> Subject " + d.sid
                       + " dropped piece " + d.pieceId + " in board area "
                       + dest_sid + "."
                       );
                    var pieces = [];
                    this.eachCardInCurrentRound(
                        d.ctid, 
                        function(i, p, applyCont) {
                            pieces.push(p);
                            applyCont();
                        }, 
                        // continuation
                        function() {
                            var in_board_area = 0;
                            for (var i=0; i < pieces.length; i++) {
                                var p = pieces[i];
                                var _avc = currentAvgVx(p);
                                var _avr = currentAvgVx(p);
                                if (p.piece_id != d.pieceId && 
                                   (ptBoardAreaSid(bas, _avc) == dest_sid || 
                                    ptBoardAreaSid(bas, _avr) == dest_sid)) {
                                    in_board_area += 1;
                                }
                            }
                            var outcome
                              , baSetmates
                              , aligned_setmates
                              ;
                            // CASE:  The board area where the piece is being
                            //        released is full.  Set 'position' 
                            //        equal to 'return_position'.
                            if (in_board_area >= 5) {
                                card.position = card.return_position;
                                outcome = "destination area full";
                            }
                            // CASE:  The board area is not full.
                            else {

                                var tl = ptBoardAreaTopLeft(bas, avc),
                                    baw = ctvs.board_area_width,
                                    bah = ctvs.board_area_height,
                                    br = { x: tl.x + baw
                                         , y: tl.y + bah
                                         },
                                    ssw = ctvs.squares_set_width,
                                    ssh = ctvs.squares_set_height;

                                // CASE: Giver is not Receiver.
                                if (dest_sid != d.sid) {
                                    // Randomize the 'release' position.
                                    var av = card.avg_vertex;
                                    for (var i = 0; i < 250; i++) {
                                        var xRand = Math.random() * baw;
                                        var yRand = Math.random() * bah;
                                        card.position = { x: xRand + tl.x - av.x
                                                        , y: yRand + tl.y - av.y
                                                        };
                                        ops = overlappingPieces(pieces, card);
                                        if (ops.length == 0) {
                                            break;
                                        }
                                    }
                                } 
                                aligned_setmates = alignedSetmates(pieces, card);
                                baSetmates = boardAreaSetmates(bas, pieces, card);
                                if (baSetmates.length > 2) {
                                    var basJson = JSON.stringify(baSetmates, null, 4);
                                    log('error', 'baSetmates: ' + basJson);
                                    exitWithError("# setmates > 2");
                                }
                                // CASE:  The piece is aligned with a setmate.
                                if (aligned_setmates.length) {
                                    // If any of the square's corners falls outside 
                                    // the board area, move all these
                                    // aligned_setmates so they're inside.
                                    var squareTL = aligned_setmates[0].position;
                                    var squareBR = { x: squareTL.x + ssw
                                                   , y: squareTL.y + ssh
                                                   };
                                    if (squareTL.x <= tl.x) {
                                        squareTL.x = tl.x;
                                    } else if (squareBR.x > br.x) {
                                        squareTL.x = br.x - ssw;
                                    }
                                    if (squareTL.y <= tl.y) {
                                        squareTL.y = tl.y;
                                    } else if (squareBR.y > br.y) {
                                        squareTL.y = br.y - ssh;
                                    }
                                    for (var i=0; i < aligned_setmates.length; i++) {
                                        var _as = aligned_setmates[i];
                                        _as.position = squareTL;
                                        storeCard(d.ctid, _as.piece_id, _as, function() {
                                            emitCard(_as.piece_id, _as);
                                        });
                                    }
                                    card.position = squareTL;
                                    outcome = "aligned";
                                }
                                // CASE:  Piece is not aligned.
                                else {
                                    switch (baSetmates.length) {
                                        case 0: outcome = "no match";       break;
                                        case 1: outcome = "partial match";  break;
                                        case 2: outcome = "complete match"; break;
                                    }
                                }
                                card.return_position = card.position;
                            }
                            storeCard(d.ctid, d.pieceId, card, function() {
                                var pbaSids = [];
                                this.eachCardInCurrentRound(
                                    d.ctid, 
                                    function(i, p, applyCont) {
                                        var _avc = currentAvgVx(p);
                                        var pieceBoardAreaSid = ptBoardAreaSid(bas, _avc);
                                        pbaSids.push(pieceBoardAreaSid);
                                        applyCont();
                                    }, 
                                    function() {
                                        var boardAreaSids = _.keys(bas);
                                        var piecesPerBa = _.map(
                                            boardAreaSids, 
                                            function(baSid) {
                                                var piecesInBoardArea = _.filter(
                                                    pbaSids, 
                                                    function(s) { return s == baSid; }
                                                );
                                                return piecesInBoardArea.length;
                                            }
                                        );
                                        var basByPieceCt = _.object(
                                            boardAreaSids, 
                                            piecesPerBa);
                                        var alignedSetmatesObj = {};
                                        if (aligned_setmates) {
                                            for (var i=0; i < aligned_setmates.length; i++) {
                                                var p = aligned_setmates[i];
                                                alignedSetmatesObj[p.piece_id] = p;
                                            }
                                        }
                                        registerRelease({ ctid: d.ctid
                                                        , setId: card.set_id
                                                        , pieceId: card.piece_id
                                                        , giverSid: d.sid
                                                        , receiverSid: dest_sid
                                                        , outcome: outcome
                                                        , position: card.position
                                                        , setmates: baSetmates
                                                        , alignedSetmates: alignedSetmatesObj
                                                        , subjectsByPieceCt: basByPieceCt
                                                        , piece: card
                                                        }, card);
                                        var sets = _.reduce(pieces, function(ss, p) {
                                            if (!ss[p.set_id]) {
                                                ss[p.set_id] = [];
                                            }
                                            ss[p.set_id].push(p);
                                            return ss;
                                        }, {});
                                        // CASE:  All sets are fully matched.  End the
                                        //        round, schedule the start of the next.
                                        // TODO:  Make this prettier.  Really ugly.
                                        if (_.every(_.values(sets), function(ps) {
                                            var xs = _.map(ps, function (p) {
                                                if (p.piece_id == card.piece_id) {
                                                    return card.position.x;
                                                }
                                                return p.position.x; });
                                            var ys = _.map(ps, function (p) {
                                                if (p.piece_id == card.piece_id) {
                                                    return card.position.y;
                                                }
                                                return p.position.y; });
                                            var ux =  _.uniq(xs);
                                            var uy =  _.uniq(ys);
                                            return 1 == ux.length == uy.length;
                                        })) {
                                            setTimeout(function() {
                                                incrementSquaresRound(d.ctid, ctvs, 
                                                    emitRoundEnd, emitRoundStart);
                                            }, 1000);
                                        }
                                    }
                                );
                            }
                        ); 
                    });
                }
                                           
            }
        });
    }

    this.squaresDisconnect = function(ctid, sid, registerRelease, emitRoundEnd,
                                   emitRoundStart, emitCard) {
        var piece;
        this.eachCardInCurrentRound(
            ctid, 
            function(i, p, applyCont) {
                if (p.dragger == sid) { 
                    piece = p; 
                }
                applyCont();
            },
            function() {
                if (piece) {
                    var data = { ctid: ctid
                               , sid: sid
                               , pieceId: piece.piece_id
                               };
                    this.squaresMouseup(data, registerRelease, emitRoundEnd,
                                        emitRoundStart, emitCard);
                }
            }
        );
    }    
    
    this.click = function(data, emitCard, registerClick, emitRoundEnd,
                          emitRoundStart, emitScore) {
        roundEvent(data, 'card_index',
                   function(currentDate, ctvs, startDate, endDate, card) {
            switch (data.task_type) {
                case 'C':
                    concentrationCardClick(data, ctvs, emitCard, registerClick,
                        emitRoundEnd, emitRoundStart, emitScore, card);
                    break;
                case 'I':
                    tilesCardClick(data, emitCard, registerClick, card, currentDate);
                    break;
                default:
                    exitWithError("Click message has invalid 'task_type'.");
                    
            }
        });
    }

    function tilesCardClick(data, emitCard, registerClick, card, currentTime) {

        var hncr = keynames.currentRound(data.ctid);
        redis.get(hncr, function(err, round) {
            if (err) { exitWithError(err); }
            var hnrv = keynames.roundVars(data.ctid, round);
            redis.hget(hnrv, 'preview_end_time', function(err, previewEnd) {
                if (err) { exitWithError(err); }

                // If there's no preview end time set yet, discard this click.
                if (!previewEnd) { return }
                // If the preview's still going, discard this click.
                var previewEndTime = new Date(Number(previewEnd));
                if (currentTime < previewEndTime) { return }
                
                function storeSelection(status_in_selection) {
                    card.in_selection = status_in_selection;
                    card.last_clicker_sid = data.sid;
                    storeCard(data.ctid, data.card_index, card, function() {
                        emitCard(data.card_index, card);
                    }); 
                }
                switch (card.in_selection) {
                    case 'off':
                        log('info', "Tiles >> tile click >> selected");
                        registerClick({ correct: card.in_pattern == 'on'
                                      , in_pattern: card.in_pattern
                                      , in_selection: 'on'
                                      , correctedSid: card.last_clicker_sid
                                      }
                        );
                        storeSelection('on');
                        break;
                    case 'on':
                        log('info', "Tiles >> tile click >> deselected");
                        registerClick({ correct: card.in_pattern == 'off'
                                      , in_pattern: card.in_pattern
                                      , in_selection: 'off'
                                      , correctedSid: card.last_clicker_sid
                                      }
                        );
                        storeSelection('off');
                        break;
                    default:
                        exitWithError("Tile has invalid status in Selection: " +
                                      card.in_selection);
                }
            });
        });
    }

    function concentrationCardClick(data, ctvs, emitCard, registerClick, emitRoundEnd,
                                    emitRoundStart, emitScore, card) {

        function match(setup_card, count_unmatched) {
            log('info', "Concentration >> card click >> The two faceup cards match!");
            registerClick('match');
            // Store the clicked card's state.
            card.state = 'matched';
            storeCard(data.ctid, data.card_index, card, function() {
                // Emit the clicked card's state.
                emitCard(data.card_index, card);
                // Store the setup card's state.
                setup_card.card.state = 'matched';
                storeCard(data.ctid, setup_card.index, setup_card.card, function() {
                    // Emit the setup card's state.
                    emitCard(setup_card.index, setup_card.card);
                    incrementGlobalScore(data.ctid, emitScore);
                    // If this round is done, emit that.
                    if (count_unmatched - 2 == 0) {
                        incrementConcentrationRound(data.ctid, ctvs, emitRoundEnd, 
                                                    emitRoundStart);
                    }
                });
            }); 
        }
 
        function nomatch(setup_card) {
            log('info', "Concentration >> card click >> Cards don't match.");
            registerClick('nomatch');
            // Store the clicked card's state.
            card.state = 'nomatch';
            storeCard(data.ctid, data.card_index, card, function() {
                // Emit the clicked card's state.
                emitCard(data.card_index, card);
                // Store the setup card's state.
                setup_card.card.state = 'nomatch';
                storeCard(data.ctid, setup_card.index, setup_card.card, function() {
                    // Emit the setup card's state.
                    emitCard(setup_card.index, setup_card.card);
                    // Schedule the reset of both cards.
                    var seconds = ctvs.seconds_unmatched_faceup;
                    setTimeout(function() {
                        // Store the clicked card's state.
                        card.state = 'facedown';
                        storeCard(data.ctid, data.card_index, card, function() {
                            // Emit the clicked card's state.
                            emitCard(data.card_index, card);
                            // Store the setup card's state.
                            setup_card.card.state = 'facedown';
                            storeCard(data.ctid, setup_card.index, setup_card.card,
                                      function() {
                                // Emit the setup card's state.
                                emitCard(setup_card.index, setup_card.card);
                            });
                        });
                    }, Number(seconds) * 1000);
                });
            });
        }

        if (card.state == 'facedown') {
            log('info', "click >> Clicked card was facedown.");
            // We're going to iterate over our cards.  Some variables
            // we'll use while iterating:
            var unmatched_faceup = [];
            var count_unmatched = 0;
            // Get a list of cards in this round that currently
            // have state faceup.  List should have length 1 or 0.
            // We check this first, before doing anything with the newly-
            // clicked card, because we want to verify that we're in a
            // legal game state.
            // TODO: really this check should happen even before we
            // retrieve the clicked card from storage.
            this.eachCardInCurrentRound(
                data.ctid, 
                function(i, c, applyCont) {
                    if (c.state != 'matched') {
                        count_unmatched += 1;
                    }
                    if (c.state == 'faceup' || c.state == 'nomatch') {
                        unmatched_faceup.push({ index: i, card: c });
                    }
                    applyCont();
                }, 
                function() {
                    // Branch based on the length of the list.
                    if (unmatched_faceup.length == 0) {
                        log('info', "click >> No other cards were faceup.");
                        registerClick('setup');
                        // Store the updated state of the clicked card.
                        card.state = 'faceup';
                        storeCard(data.ctid, data.card_index, card, function() {
                            emitCard(data.card_index, card, false);
                        });
                    } else if (unmatched_faceup.length == 1) {
                        // The first and only card in the list must be the
                        // 'setup card', the one that was already turned
                        // faceup and which the newly-clicked card may
                        // or may not match (we'll find that out in a minute).
                        var setup_card = unmatched_faceup[0];
                        log('info',
                            "click >> Card " + setup_card.index +
                            " was already faceup.");
                        // Now branch based on whether the two faceup
                        // cards match.
                        if (setup_card.card.url == card.url) {
                            match(setup_card, count_unmatched); 
                        } else {
                            nomatch(setup_card);
                        }
                    } else {
                        log('info', 
                            "click >> " + unmatched_faceup.length + 
                                      " cards are already faceup."
                        );
                        // Now we want to see whether both of the
                        // faceup cards have status 'faceup'.  If
                        // so, we need to select one of them 
                        // and re-call 'click' with it.  I.e. we'll
                        // ignore the card that was ACTUALLY just
                        // clicked.  And of course we need to log
                        // what we're doing, for later clarity.
                        var a = unmatched_faceup[0];
                        var b = unmatched_faceup[1];
                        if (a.card.state == 'faceup' && b.card.state == 'faceup') {
                            a.card.state = 'facedown';
                            storeCard(data.ctid, a.index, a.card, function() {
                                // Make it seem as though it was 'a' that was just clicked.
                                data.card_index = a.index;
                                this.click(data, emitCard, registerClick,
                                    emitRoundEnd, emitRoundStart, emitScore);
                            });
                        }
                    }
                }
            );
        } 
    }

    this.pointsGlobal = function(data, emitScore) {
        var kn_pts_global = keynames.pointsGlobal(data.ctid);
        redis.get(kn_pts_global, function(err, score) {
            if (err) { exitWithError(err); }
            emitScore(score);
        });
    }

    return this;    
};

