function cardFunctions(DEBUG, canvas, socket, ctid, sid, task_type) {

    var cardIndex = function(card) {
        return card.attr('id').replace('card_', '');
    }

    var cardId = function(card_index) {
        return 'card_' + card_index;
    }

    var cardClasses = function(card_index) {
        var cs = 'card';
        if (task_type == 'C' && card_index % 8 == 0) {
            cs += ' clear';
        }
        return cs;
    }

    var cardsContainer = $("#cards-container");

    return {
        // Find or create (and insert) the jQuery object representing the card
        // whose index is @card_index.
        card: function (data) {
            if (DEBUG) console.log("Card " + data.index);
        		var card = $('#' + cardId(data.index));
            if (card.length == 0) {
                if (DEBUG) console.log("Card " + data.index + " didn't exist");
                var card_html = data.card.url ? '<img src="' + data.card.url + '"/>' : '';
                card = $('<div>' + card_html + '</div>')
                         .attr('id', cardId(data.index))
                         .attr('class', cardClasses(data.index))
                         .click(function (e) {
                              if (DEBUG) console.log("card " + " clicked by Subject " + sid);
                              socket.emit('click', { ctid: ctid
                                                   , sid: sid
                                                   , card_index: cardIndex($(this))
                                                   , task_type: task_type
                                                   });
                          });
                if (DEBUG) console.log("Card " + data.index + ": ");
                if (DEBUG) console.log(card);
                // If we're index 0 -- or the first to be appended -- just
                // prepend us to the cardsContainer.
                if (data.index == 0 || cardsContainer.children(".card").length == 0) {
                    cardsContainer.prepend(card);
                // Else find (my algorithm is terrible, linear-time, I know) our
                // nearest predecessor among the cardsContainer' existing children and
                // insert us after it.
                } else {
                    for (var i = data.index; i >= 0; i--) {
                        var predecessor = $('#' + cardId(i));
                        if (predecessor.length > 0) {
                            card.insertAfter(predecessor);
                            break;
                        } else if (i == 0) {
                            cardsContainer.prepend(card);
                        }
                    }
                }
            }
            return card;
        }
    }
}
