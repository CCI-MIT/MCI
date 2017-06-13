function configureGameBoard(DEBUG, canvas, socket, ctid, sid, task_type,
                            bindPointerSpace) {

    /* @psX, psY: The (x,y) location of the cursor relative to the origin
                  of the pointer space's canvas element (i.e.
                  #task-workspace-cards). */
    bindPointerSpace(
        3,
        // positionCursorCallback
        function(psX, psY) {
            socket.emit('positionCursor', { ctid : ctid,
                                            sid  : sid,
                                            x    : psX,
                                            y    : psY });
        }, 
        // removeCursorCallback
        function() {
            socket.emit('removeCursor', { ctid: ctid, sid: sid });        
        }
    );

    var cardFuncs = cardFunctions(
        DEBUG,
        canvas,
        socket,
        ctid,
        sid,
        task_type
    );

    //  Server updates the state of one card.
    socket.on('card', function (data) {
        if (DEBUG) console.log("'card' called in Subject " + sid + "'s browser.");
        if (DEBUG) console.log("        State is " + data.card.state);

        switch (data.card.state) {
            case 'facedown':
                cardFuncs.card(data).children('img').hide();
                break;
            case 'faceup':
                cardFuncs.card(data).children('img').show();
                break;
            case 'matched':
                cardFuncs.card(data).children('img').show();
                cardFuncs.card(data)
                    .animate({top: "-=10px" }, 50, function() {
                        $(this).animate({top: "+=20px" }, 120, function() {
                            $(this).animate({top: "-=20px" }, 50, function() {
                                $(this).animate({top: "+=10px" }, 100);
                            });
                        });
                    });
                break;
            case 'nomatch':
                cardFuncs.card(data).children('img').show();
                cardFuncs.card(data)
                    .animate({left: "+=15px" }, 75, function() {
                        $(this).animate({left: "-=30px" }, 150, function() {
                            $(this).animate({left: "+=15px" }, 75);
                        });
                    });
                break;
            default:
                if (DEBUG) console.log("  Illegal card state.");
        }
    });

    socket.on('click', function(user) {
        var container = $("#avatar-" + user.sid);
        container.find(".clicks").text("Clicks: " + user.clicks);
    });

    socket.on('roundEnd', function() {
        if (DEBUG) console.log("roundEnd");
        canvas.find(".card").each(function() {
            $(this).remove();
        });
        canvas.append('<div id="next-round">Next Round!</div>');     
    });

    socket.on('roundStart', function() {
        if (DEBUG) console.log("roundStart");
        canvas.children('#next-round').remove();
        socket.emit('allState', { ctid: ctid, sid: sid });      
    });

    socket.on('score', function (count) {
        $("#score").text(count);
    });
}
