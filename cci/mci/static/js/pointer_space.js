function bind_pointer_space(canvas, socket, ctid, sid, task_type, threshold,
                            positionCursorCallback, removeCursorCallback) {

    var DEBUG = false;

    // Putting the 'track own cursor' logic in an anonymous fn call just to make
    // clear that it's separate from the event listener logic below.
    (function trackOwnCursor() {

        var lastTriggeredX = 0;
        var lastTriggeredY = 0;
        var threshold_time = new Date();

        function triggerIfAppropriate(x, y) {

            if (DEBUG) console.log("x: " + x + " .  y: " + y);

            var current_time = new Date();

            function shouldTrigger() {
                var st = false;
                if (current_time > threshold_time) {
                    if (Math.abs(x - lastTriggeredX) > threshold) {
                        st = true;
                    } else if (Math.abs(y - lastTriggeredY) > threshold) {
                        st = true;
                    }
                }
                return st;
            }

            if (shouldTrigger()) {

                lastTriggeredX = x;
                lastTriggeredY = y;

                threshold_time = current_time;
                threshold_time.setMilliseconds(threshold_time.getMilliseconds() + 250);

                positionCursorCallback(x, y);
            }
        }

        canvas.mousemove(function (e) {
            if (DEBUG) console.log("canvas.mousemove in Subject " + sid +
                                   "'s browser.");
            var x = Math.floor(e.clientX - canvas.offset().left
                                         + $(window).scrollLeft());
            var y = Math.floor(e.clientY - canvas.offset().top
                                         + $(window).scrollTop());
            triggerIfAppropriate(x, y);
        });
    
        canvas.mouseleave(function (e) {
            lastTriggeredX = lastTriggeredY = 0;
            removeCursorCallback();
        });  
    })();


    function cursorElementId(sid) {
        return 'cursor_' + sid;
    }

    /*  Render another Subject's cursor.
            @data: a dictionary with keys:
                #sid:  a CCI Subject ID.
                #x:     an integer.
                #y:     an integer.     */
    socket.on('cursor', function (data) {

        if (data.clicks) {
            var container = $("#avatar-" + data.sid);
            container.find(".clicks").text("Clicks: " + data.clicks);
        }

        if (sid != data.sid && data.y != -1 && data.x != -1) {
            if (DEBUG) console.log("positionOtherCursor called in Subject " + sid +
                                   "'s browser.");

            // Find or create the element representing the Subject's cursor.
    		    var cursor = $('#' + cursorElementId(data.sid));
            if (cursor.length == 0) {
                try {
                    var emblem = '<img src="' + avatars[data.sid]['flag_url'] + '"/>';
                    cursor = $(
                        '<div class="cursor">' +
                            '<div class="pointer">' +
                                '<img src="/static/img/pointer.png" />' +
                            '</div>' +
                            '<div class="emblem-and-label">' +
                                emblem + 
                                '<span class="label">' + avatars[data.sid]['display_name'] + '</span>' +
                            '</div>' +
                        '</div>'
                    );
                    cursor.attr('id', cursorElementId(data.sid));
                    cursor.css('position', 'absolute');
                    canvas.append(cursor);
                } catch (e) {
                    console.log("Error building cursor element for sid " + data.sid);
                }
            }

            // Position cursor, offsetting to account for the canvas' own position.

            cursor.animate({
                left : Number(data.x) + canvas.offset().left,
                top  : Number(data.y) + canvas.offset().top
            }, 100);
        }
    });
	
    /*  Removes the DOM element representing another Subject's cursor.  Params:
            @data: a dictionary with keys:
                #sid: a CCI Subject id.  */
    socket.on('removeCursor', function (data) {
        if (sid != data.sid) {
            if (DEBUG) console.log("removeOtherCursor called in Subject " + sid +
                                   "'s browser.");
		        var cursor = $('#' + cursorElementId(data.sid));
            if (cursor) {
                cursor.remove();
            }
        }
    });	
}
