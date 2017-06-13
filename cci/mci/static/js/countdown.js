var javascript_countdown = function() {

    var hrs_orig, min_orig, sec_orig;


    // Number of seconds from which to count
    var seconds_remaining = 10; 
    var output_element_id = 'javascript_countdown_time';
    var keep_counting = 1;
    var suffix_text = 'minutes remaining';
    var seconds_text = 'seconds remaining';

    var tick_timeout;
    var begin_timeout;

    function countdown() {
        if (seconds_remaining < 2) {
            keep_counting = 0;
        }
        seconds_remaining = seconds_remaining - 1;
    }
 
    function format_substring(is_leader, digits, val) {
        if (!is_leader) {
            digits = 2;
        }
        var val_string = '';
          if (val > 0) {
              val_string = val.toString();
        }
        while (val_string.length < digits) {
            var zero = is_leader ? '<span class="zero">0</span>' : '0';
            val_string = zero + val_string;
        }
        return val_string;
    }

    function sec_from_sec(seconds) {
        return Math.max(seconds_remaining % 60, 0);
    }

    function min_from_sec(seconds) {
        return Math.max(Math.floor(seconds_remaining / 60) % 60, 0);
    }

    function hrs_from_sec(seconds) {
        return Math.max(Math.floor(seconds_remaining / 3600), 0);
    }

    function output() {

        var hrs = format_substring(true,         hrs_orig.length, hrs_from_sec(seconds_remaining));
        var min = format_substring(!hrs,         min_orig.length, min_from_sec(seconds_remaining));
        var sec = format_substring(!(hrs + min), sec_orig.length, sec_from_sec(seconds_remaining));
        var remaining_text = suffix_text;

        if (seconds_remaining < 60) {
            remaining_text = seconds_text;
        }

        return  "<div class='minutes-value'>" +
                    hrs + (hrs ? ':' : '') + min + (min ? ':' : '') + sec +
                "</div>" +
                " <div class='minutes-label'>" +
                    remaining_text +
                "</div>";
    }
 
    function render_time_remaining() {
        if (document.getElementById(output_element_id) != undefined) {
            document.getElementById(output_element_id).innerHTML = output();
        }
    }


    /* Exported functions */

    function count() {
        countdown();
        render_time_remaining();
    }

    function timer(begin_after) {

        // Show the initial time, whether or not we are going to start
        // counting down right away.
        count();

        function _count() {
            count();
            if (keep_counting) {
              tick_timeout = setTimeout(_count, 1000);
            }
        }

        begin_timeout = setTimeout(_count, begin_after * 1000);
    }
 
    function init(begin_after, count_from, element_id, suffix) {
        hrs_orig = format_substring(true,                   0, hrs_from_sec(count_from));
        min_orig = format_substring(!hrs_orig,              1, min_from_sec(count_from));
        sec_orig = format_substring(!(hrs_orig + min_orig), 2, sec_from_sec(count_from));
        
        seconds_remaining = count_from;
        keep_counting = 1;
        output_element_id = element_id;
        suffix_text = suffix;

        timer(begin_after);
    }

    function stop() {
        clearTimeout(tick_timeout);
        clearTimeout(begin_timeout);
        keep_counting = 0;
    }

    function start(begin_after, count_from) {
        stop();
        seconds_remaining = count_from;
        keep_counting = 1;
        timer(begin_after);
    }

    return {
        count: count,
        timer: timer,
        init: init,
        stop: stop,
        start: start
    };
};
