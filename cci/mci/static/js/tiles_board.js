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
        false,
        // DEBUG,
        canvas,
        socket,
        ctid,
        sid,
        task_type
    );

    var submitPopTimeout;
    var cardsContainer = $("#cards-container");

    function hideSubmit() {
        $("#submit-button .button").hide();
        $("#submit-button").css('background-color', 'transparent');
    }
    function showSubmit() {
        $("#submit-button .button").show();
        $("#submit-button").css('background-color', 'gray');
    }

    //  Server updates the state of one card.
    socket.on('card', function (data) {
        if (DEBUG) console.log("'card' called in Subject " +
                                  sid + "'s browser.");
        if (DEBUG) console.log("        Status in Selection is " +
                                  data.card.in_selection);
        if (DEBUG) console.log(data.card);
        var c = cardFuncs.card(data);
        if (data.card.clear_left) {
            c.addClass('clear');
        }
        var temp = new Date();
        var dateStr = [ temp.getSeconds().toString()
                      , temp.getMilliseconds().toString()
                      ].join('-');
        
        c.addClass(dateStr);

        cardsContainer.centerToParent();

        switch (data.card.in_selection) {
            case 'on':
                c.css('background-color', 'red');
                break;
            case 'off':
                c.css('background-color', 'gray');
                break;
            default:
                if (DEBUG) console.log("  Illegal card state.");
        }

    });

    $("#submit-button .button").click(function() {
        socket.emit('submitClick', { ctid: ctid, sid: sid });
    });

    socket.on('displaySubmitButton', showSubmit);

    socket.on('click', function(user) {
        var container = $("#avatar-" + user.sid);
        container.find(".clicks").text("Clicks: " + user.clicks);

        clearTimeout(submitPopTimeout);
        submitPopTimeout = setTimeout(function() {
            $("#submit-button").animate({transform: "scale(1.3, 1.3)" }, 150, function() {
                $("#submit-button").animate({transform: "scale(1.0, 1.0)" }, 150);
            });
        }, 3000);
        
    });

    socket.on('submitClick', function() {
        canvas.find("#tiles-message").remove();
        canvas.prepend('<div id="tiles-message">Round complete!</div>');
        hideSubmit();
    });

    socket.on('roundEnd', function(data) {
        if (DEBUG) console.log("roundEnd >> data: ");
        if (DEBUG) console.log(data);
        if (data.outcome == 'success') {
            $("#score").text(data.teamScore);
            $("#score").animate({transform: "scale(1.8, 1.8)" }, 200, function() {
                $("#score").animate({transform: "scale(1.0, 1.0)" }, 200);
            });
        }
        canvas.find(".card").each(function(i) {
            
            function ofIndexI(tile) {
                return tile.index == i;
            }
            var in_pattern = _.some(data.pattern, ofIndexI);
            var in_selection = _.some(data.selection, ofIndexI);
            if (in_pattern && !in_selection) {
                $(this).flip({
                    direction: 'rl',
                    color: 'red',
                    speed: 200
                });
            } else if (in_pattern && in_selection) {
                if (data.outcome == 'success') {
                    $(this).animate({transform: "scale(1.3, 1.3)" }, 200, function() {
                        $(this).animate({transform: "scale(1.0, 1.0)" }, 200);
                    });
                }
            } else if (!in_pattern && in_selection) {
                $(this).html("<img class='incorrect-tile' src='/static/img/x.png' />");
                $(this).css('background-color', 'gray');
            }
        });
        setTimeout(function() {
            canvas.find(".card").each(function() { $(this).remove(); });
            canvas.find("#tiles-message").remove();
            canvas.append('<div id="next-round">Next Round!</div>');
        }, 3000);
    });

    socket.on('roundPreview', function() {
        if (DEBUG) console.log("roundPreview");
        canvas.find(".card").each(function() { $(this).remove(); });
        canvas.find('#next-round').remove();
        // Cause each card's color to reflect its pattern status.  To do this,
        // clear them all and call 'allState'.
        socket.emit('allState', { ctid: ctid, sid: sid, task_type: 'I' });
        canvas.prepend('<div id="tiles-message">Memorize this pattern...</div>');        
        hideSubmit();
    });
    
    socket.on('roundStart', function() {
        if (DEBUG) console.log("roundStart");
        canvas.find("#tiles-message").remove();
        // Cause each card's color to reflect its selection status (i.e.
        // 'off').  To do this, clear them all and call 'allState'.
        canvas.find(".card").each(function() { $(this).remove(); });
        socket.emit('allState', { ctid: ctid, sid: sid, task_type: 'I' });
        canvas.prepend('<div id="tiles-message">Now recreate it!</div>');        
        setTimeout(function() {
            canvas.find("#tiles-message").remove();
        }, 1500);
        showSubmit();
    });
}
