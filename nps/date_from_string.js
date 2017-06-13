module.exports = function dateFromString(time_string) {
    var time_string_parts = time_string.split("-");
    return new Date(
        time_string_parts[0],     // years
        time_string_parts[1] - 1, // months
        time_string_parts[2],     // days
        time_string_parts[3],     // hours
        time_string_parts[4],     // minutes
        time_string_parts[5]      // seconds
    );
}
