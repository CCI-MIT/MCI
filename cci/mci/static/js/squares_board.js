var testObject = {};

function configureGameBoard(DEBUG, canvas, socket, ctid, sid, task_type,
                            bindPointerSpace) {

    testObject.mousemoveWithoutMousedown = function() {
        var pieces = $(".piece");
        var piece_index = Math.floor((Math.random(1) * pieces.length));
        var piece_htmlId = $(pieces[piece_index]).attr("id");
        var piece_gameId = piece_htmlId.replace("piece_", "");
        socket.emit('squaresMousemove', { ctid: ctid
                                        , sid: sid
                                        , pieceId: piece_gameId
                                        , mousePosition: { x: 100, y: 100 }
                                        }
        );
    };

    /*******
     HELPERS
     *******/

    var pieceIndex = function(piece) {
        return piece.attr('id').replace('piece_', '');
    }

    var pieceHtmlElemId = function(pieceId) {
        return 'piece_' + pieceId;
    }

    var pieceClasses = function(data) {
        var cs = 'piece piece-' + data.card.piece_id + ' set-' + data.card.set_id;
        return cs;
    }

    var setColors = [ '#7F7FFF'
                      , '#7FFF7F'
                      , '#BF00FF'
                      , '#FF00BF'
                      , '#FF7F00'
                      , '#BFFFFF'
                      ];

    function pieceColor(setId) {
        // In DEBUG mode, color-code the pieces by set.
//        if (DEBUG) { 
//            return setColors[Number(setId) % setColors.length];
//        } else {
            return '#595959'; 
//        }
    }

    var dragColor = '#FFFFFF';
    var alignedPieceBorderColor = '#F6CE4B';

    var $gameboard = $("#gameboard");
    var catchLayer = $("#catch-layer");

    // We'll update this every time this subject picks up or releases a piece.
    var dragged_piece_id;

    /* @psX, psY: The (x,y) location of the cursor relative to the origin
                  of the pointer space's canvas element (i.e.
                  #task-workspace-cards). */
    bindPointerSpace(3, function(psX, psY) {

//        if (DEBUG) console.log("'track' in Subject " + sid +
//                               "'s browser.");

        socket.emit('positionCursor', { ctid : ctid,
                                        sid  : sid,
                                        x    : psX,
                                        y    : psY });

        if (dragged_piece_id) {
            var twcOff = $("#task-workspace-cards").offset();
            var gbOff = $gameboard.offset();
            var pos = { x: psX - (gbOff.left - twcOff.left)
                      , y: psY - (gbOff.top - twcOff.top)
                      };

//            if (DEBUG) console.log( "Mousemove with piece " + dragged_piece_id
//                                  + " by Subject " + sid
//                                  + " at " + JSON.stringify(pos,null,0)
//                                  );

            socket.emit('squaresMousemove', { ctid: ctid
                                            , sid: sid
                                            , pieceId: dragged_piece_id
                                            , mousePosition: pos
                                            }
            );
        }        
    }, function() {
        socket.emit('removeCursor', { ctid: ctid, sid: sid });        
    });

    function pnpoly(nvert, vertx, verty, testx, testy) {
        var i, j, c = false;
        for (i = 0, j = nvert-1; i < nvert; j = i++) {
            if ((( verty[i] > testy) != (verty[j] > testy)) &&
                (testx < (vertx[j] - vertx[i]) * (testy - verty[i]) /
                (verty[j] - verty[i]) + vertx[i])) {
                    c = !c;
            }
        }
        return c;
    }

    function canvasContextForPiece(piece, vertices, cls) {
        var canv = $(document.createElement('canvas')).addClass(cls);
        piece.append(canv);
        if (typeof(G_vmlCanvasManager) !== 'undefined') {
            G_vmlCanvasManager.initElement(canv[0]);
        }
        // Draw the polygon
        var canvContext = canv[0].getContext('2d');
        canvContext.beginPath();
        for (var i = 0; i < vertices.length; i++) {
            var v = vertices[i];
            if (i == 0) {
                canvContext.moveTo(v.x, v.y);
            } else {
                canvContext.lineTo(v.x, v.y);
                // If this is the last vertex, draw an edge to the first.
                if (i == vertices.length - 1) {
                    var v0 = vertices[0];
                    canvContext.lineTo(v0.x, v0.y);
                }
            }
        }
        canvContext.closePath();
        return canvContext;
    }

    // Find or create (and insert) the jQuery object representing the piece
    // whose Django Piece pk is @data.card.piece_id.
    function piece(data) {

        if (DEBUG) console.log("Piece data:");
        if (DEBUG) console.log(data);

        var pid = data.card.piece_id;
        var piece = $('#' + pieceHtmlElemId(pid));

        if (piece.length == 0) {

            if (DEBUG) console.log("Piece " + pid + " didn't exist");

            piece = $('<div id="' + pieceHtmlElemId(pid) + '" ' +
                           'class="' + pieceClasses(data) +'">' +
                          '<div class="avg-vertex"></div>' +
                      '</div>')
                .css('left', data.card.position.x + 'px')
                .css('top', data.card.position.y + 'px');
            piece.data('piece', data.card);

            if (DEBUG) console.log(piece);
            // In debug mode, let a dot indicate the average vertex
            if (DEBUG) {
                piece.find(".avg-vertex").css('left', data.card.avg_vertex.x + "px")
                                         .css('top', data.card.avg_vertex.y + "px");
            }

            $gameboard.append(piece);

            var cc = canvasContextForPiece(piece, data.card.vertices, "fill");
            cc.fillStyle = pieceColor(data.card.set_id);
            cc.fill();
        }
        return piece;
    }

    /********
     HANDLERS
     ********/

    //  Server updates the state of one piece.
    socket.on('card', function (data) {
        if (DEBUG) console.log("'card' called in Subject " +
                                  sid + "'s browser.");
        if (DEBUG) console.log(data.card);
        // for some reason this next line needs to be here -- why?
        var c = piece(data);
        if (Number(data.card.dragger) == sid) {
            dragged_piece_id = data.card.piece_id;
        }
        positionSquare(data.card);
    });

    catchLayer.mousedown(function (e) {
        var hitPieces = $gameboard.children(".piece").filter(function(i) {
            var vs = $(this).data('piece').vertices;
            var xs = _.map(vs, function(v) { return v.x; });
            var ys = _.map(vs, function(v) { return v.y; });
            var off = $(this).offset();
            var relX = e.pageX - off.left;
            var relY = e.pageY - off.top;
            return pnpoly(vs.length, xs, ys, relX, relY);
        });
        if (hitPieces.length == 0) {
            return;
        } else if (hitPieces.length > 1) {
            hitPieces = _.sortBy(hitPieces, function(el) {
                return Number($(el).css('z-index'));
            }).reverse();
        }
        var piece = $(hitPieces[0]);
        var pid = piece.data('piece').piece_id;
        if (DEBUG) console.log("Mousedown on piece " + pid
                              + " by Subject " + sid
                              );
        socket.emit('squaresMousedown', { ctid: ctid
                                        , sid: sid
                                        , pieceId: pid
                                        }
        );
        // NOTE:  We assign this here so that mousemove events can be emitted 
        //        before the mousedown event has been ratified and broadcast.
        //        This way, the first mousemove event (server-side, I'm talking
        //        about) forces a mousedown event, which would get ratified here
        //        shortly afterward.
        //dragged_piece_id = pid;
    });
    
    socket.on('squaresPickup', function(pickupData) {
        if (DEBUG) console.log("Received 'squaresPickup'.  data:");
        if (DEBUG) console.log(pickupData);
        if (sid == Number(pickupData.sid)) {
            if (DEBUG) console.log("Setting dragged_piece_id");
            dragged_piece_id = pickupData.pieceId;
        }
        //  Clear the perimeter highlighting on aligned setmates.
        var p = $gameboard.find('#' + pieceHtmlElemId(pickupData.pieceId));
        var aligned_setmate_elems = alignedSetmateElems(p.data("piece"));
        _.each(aligned_setmate_elems, function(ase) {
            ase.find("canvas.stroke").remove();
        });
        //  Make sure each currently-dragged piece has a higher z-index than
        //  any non-dragged piece.  Among dragged pieces the order can be
        //  unspecified.
        for (var i=0; i < pickupData.pieces.length; i++) {
            var p = pickupData.pieces[i];
            var pEl = $gameboard.find('#' + pieceHtmlElemId(p.piece_id));
            pEl.css('z-index', (!(p.dragger) ? 1 : 2));
        }
    });

    function positionSquare(dragData) {
        var key = dragData.pieceId ? dragData.pieceId : dragData.piece_id;
        var p = $gameboard.find('#' + pieceHtmlElemId(key));
        if (!p) { return; }
        p.animate( { left : dragData.position.x
                   , top  : dragData.position.y
                   }
                 , 100
                 );
        if (!p.data("piece")) { return; }
        p.data("piece").position = dragData.position;
        var aligned_setmate_elems = alignedSetmateElems(p.data("piece"));
        _.each(aligned_setmate_elems, function(ase) {
            ase.find("canvas.stroke").remove();
        });
    }
 
    socket.on('squaresDrag', positionSquare);


    catchLayer.mouseup(function () {
        if (DEBUG) console.log("Mouseup.  dragged_piece_id: " + dragged_piece_id);
        if (dragged_piece_id) {
            socket.emit('squaresMouseup', { ctid: ctid
                                          , sid: sid
                                          , pieceId: dragged_piece_id
                                          }
            );
        }
    });

    socket.on('squaresRelease', function(releaseData) {
        if (DEBUG) console.log("squaresRelease >> releaseData:");
        if (DEBUG) console.log(releaseData);
        if (releaseData.pieceId == dragged_piece_id && 
            Number(releaseData.giverSid) == sid) {
            dragged_piece_id = undefined;
        }
        var p = $gameboard.find('#' + pieceHtmlElemId(releaseData.pieceId));
        p.animate( { left : releaseData.position.x
                   , top  : releaseData.position.y
                   }
                 , 100
                 );
        p.data("piece").position = releaseData.position;
        $gameboard.find('canvas.stroke').each(function(i) {
              $(this).remove();
        });
        drawSetPerimetersAndUpdateScore();
    });

    socket.on('cardsSent', function() {
        drawSetPerimetersAndUpdateScore();
    });

    function alignedSetmateElems(piece) {
        var pieceElems = $gameboard.find(".piece");
        var aligned_setmates = [];
        for (var i = 0; i < pieceElems.length; i++) {
            var pe = $(pieceElems[i]);
            var p = pe.data("piece")
            if (p.set_id == piece.set_id) {
                if (p.position.x == piece.position.x && p.position.y == piece.position.y) {
                    aligned_setmates.push(pe);
                }
            }
        }
        return aligned_setmates;
    }

    function drawSetPerimetersAndUpdateScore() {
        var completeSets = [];
        $gameboard.find('.piece').each(function(i) {
            var piece = $(this).data('piece');
            var aligned_setmate_elems = alignedSetmateElems(piece);
            if (aligned_setmate_elems.length == 3) { 
                if (_.indexOf(completeSets, piece.set_id) == -1) {
                    completeSets.push(piece.set_id);
                }
                var canv = $(document.createElement('canvas')).addClass("stroke");
                var vertices = $(this).data("piece").vertices;
                $(this).append(canv);
                if (typeof(G_vmlCanvasManager) !== 'undefined') {
                    G_vmlCanvasManager.initElement(canv[0]);
                }
                // Draw the polygon
                var canvContext = canv[0].getContext('2d');
                canvContext.lineWidth = 5;
                // For each edge in this piece:
                for (var i = 0; i < vertices.length; i++) {
                    canvContext.beginPath();
                    var vFst = i == 0 ? vertices[vertices.length - 1] : vertices[i - 1];
                    var vSnd = vertices[i];
                    // TODO use a variable "squares set height/width" instead of the hard-coded 72.
                    var isPerimeterEdge = (vFst.x == 0  && vSnd.x == 0)
                                       || (vFst.x == 72 && vSnd.x == 72)
                                       || (vFst.y == 0  && vSnd.y == 0)
                                       || (vFst.y == 72 && vSnd.y == 72);
                    if (isPerimeterEdge) {
                        canvContext.moveTo(vFst.x, vFst.y);
                        canvContext.lineTo(vSnd.x, vSnd.y);
                        canvContext.strokeStyle = alignedPieceBorderColor;
                        canvContext.stroke();
                    }
                }
            }
        });
    }

    socket.on('roundEnd', function() {
        if (DEBUG) console.log("roundEnd");
        canvas.find(".piece").each(function() {
            $(this).remove();
        });
        canvas.append('<div id="next-round">Next Round!</div>');     
    });

    socket.on('roundStart', function() {
        if (DEBUG) console.log("roundStart");
        canvas.children('#next-round').remove();
        socket.emit('allState', { ctid: ctid, sid: sid });      
    });

    socket.on('disconnect', function() {
        if (DEBUG) console.log("Disconnected from game server.");
    });
}
