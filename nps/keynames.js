module.exports = function() {

    return {
        ctVars: function(ctid) {
            return 'ct_' + ctid + '_vars';
        }
    ,   roundVars: function(ctid, roundIndex) {
            return 'ct_' + ctid + '_vars_round_' + roundIndex;
        }
    ,   subjects: function(ctid) {
            return 'ct_' + ctid + '_users';
        }
    ,   // TODO this use of a single global is pretty ugly and dangerous.
        currentAssister: function(ctid) {
            return 'ct_' + ctid + '_assister_sid';
        }
    ,   currentRound: function(ctid) {
            return 'ct_' + ctid + '_current_round';
        }
    ,   roundCards: function(ctid, roundIndex) {
            return 'ct_' + ctid + '_cards_round_' + roundIndex;
        }
    ,   pointsGlobal: function(ctid) {
            return 'ct_' + ctid + '_points_global';
        }
    ,   clicks: function(ctid) {
            return 'ct_' + ctid + '_card_clicks';
        }
    ,   submitClicks: function(ctid) {
            return 'ct_' + ctid + '_submit_clicks';
        }
    ,   squaresPickups: function(ctid) {
            return 'ct_' + ctid + '_squares_pickups';
        }
    ,   squaresMoves: function(ctid) {
            return 'ct_' + ctid + '_squares_moves';
        }
    ,   tilesDsbiaFlags: function(ctid) {
            return 'ct_' + ctid + '_tiles_dsbia_flags';
        }
    }
};

