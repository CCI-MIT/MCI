function load_test(canvas, socket, ctid, sid, mm_interval, task_type) {

    var canvas_width = canvas.width();
    var canvas_height = canvas.height();

    var margin_x = canvas_width / 12;
    var margin_y = canvas_height / 8;

    var x = Math.floor(
          (Math.random() * (canvas.width() - (2 * margin_x)))
        + margin_x 
    );
    var y = Math.floor(
          (Math.random() * (canvas.height() - (2 * margin_y)))
        + margin_y 
    );

    var rightward = true;
    var downward = true;

    function positionCursor() {

        if      (x <= margin_x) {                rightward = true;  }
        else if (x >= canvas_width - margin_x) { rightward = false; }

        if      (y <= margin_y) {                 downward = true;  }
        else if (y >= canvas_height - margin_y) { downward = false; }

        x = rightward ? x + 14 : x - 15;
        y = downward  ? y + 14 : y - 15;

        socket.emit('positionCursor', {
            ctid : ctid,
            sid  : sid,
            x    : x,
            y    : y
        });

        setTimeout(positionCursor, mm_interval);
    }

    function cardClickConcentration() {

        var cards = $("#gameboard").find(".card");
        var facedown_indices = _.reduce(cards, function(indices, val, index) {
            if ($(val).children('img').is(":hidden")) {
                indices.push(index);
            }
            return indices;
        }, []);
        if (facedown_indices.length) {
            var index_of_index = Math.floor(Math.random() * facedown_indices.length);
            var card_index = facedown_indices[index_of_index];
            cards[card_index].click();
//            socket.emit('click', {
//                ctid       : ctid,
//                sid        : sid,
//                card_index : card_index
//            });
        }
        setTimeout(cardClickConcentration, 4000);
    }

    function cardClickTiles() {
        var cards = $("#gameboard").find(".card");
//        console.log("cardClickTiles >> cards:");
//        console.log(cards);
        var card_index = Math.floor(Math.random() * cards.length);
        var card = cards[card_index];
//        console.log("cardClickTiles >> card:");
//        console.log(card);
        if (card) {
            card.click();
        }
        setTimeout(cardClickTiles, 4000);
    }

    var submitClickMgr = function() {
        var timeout;
        function submitClick() {
            var submitBtn = $("#submit-button .button");
            if (submitBtn) {
                submitBtn.click();
            }
            this.reset();
        }
        this.reset = function() {
            clearTimeout(timeout);
            timeout = setTimeout(submitClick, 20 * 1000);
        };
        return this;
    }();

    positionCursor();

    switch (task_type) {
        case "C": 
            cardClickConcentration(); 
            break;
        case "I":
            cardClickTiles();
            submitClickMgr.reset();
            break;
    }
    socket.on('roundEnd', function() {
        if (task_type == "I") {
            submitClickMgr.reset();
        }
    });
}
