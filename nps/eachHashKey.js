//  @log      -- A socket.io logger.
module.exports = function(log) {

    /*  PARAMETERS:
            @redis    -- A node-redis client.
            @hashname -- A string identifying a Redis hash.
            @apply    -- A function expecting parameters:
                             @key -- A string.
                             @val -- (User-defined).
                             @callback -- a nullary function.
        CONTRACT:
            This function consumes a list of the keys in the hash named 
            'hashname'.  For each, it calls 'apply'.  After the last one,
            it calls 'continuation'. 
    */
    return function(redis, hashname, apply, continuation) {
        redis.hkeys(hashname, function (err, keys) {
            if (err) { 
                log('error', " >> eachHashKey error: " + err); 
            } else {
                keys.sort(function(a, b) {
                    var numA = Number(a);
                    var numB = Number(b);
                    if (numA < numB) { return -1 }
                    if (numA > numB) { return 1 }
                    return 0
                });
                function applyToEachKeyThenContinue(_keys) { 
                    if (_keys.length == 0) {
                        if (continuation) { continuation(); }
                    } else {
                        var key = _keys[0];
                        redis.hget(hashname, key, function(err, val_json) {
                            var val = JSON.parse(val_json);
                            if (err) {
                                log('error', "eachHashKey >> ERROR: " + err);
                                process.exit(1);
                            }
                            apply(key, val, function() {
                                var _newKeys = _keys;
                                _newKeys.shift();
                                applyToEachKeyThenContinue(_newKeys);
                            });
                        });
                    }
                }
                applyToEachKeyThenContinue(keys);
            }
        });
    }
};
