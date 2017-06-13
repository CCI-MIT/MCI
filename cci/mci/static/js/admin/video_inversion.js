jQuery(document).ready(function ($) {

    var video_enabled = $(".grp-row.video_enabled");
    var ve_input = video_enabled.find("input");

    var disable_video = video_enabled.clone(false);
    disable_video.attr("id", "disable-video");
    disable_video.removeClass("video_enabled");
    var dv_input = disable_video.find("input");
    dv_input.attr("name", "");
    dv_input.attr("id", "");
    var dv_label = disable_video.find(".vCheckboxLabel");
    dv_label.text("Disable Video");
    dv_label.attr("for", "");
    dv_input.prop("checked", !(ve_input.prop("checked")));
    dv_input.change(function() {
        ve_input.prop("checked", !(dv_input.prop("checked")))
    });

    video_enabled.hide();
    disable_video.insertAfter(video_enabled);

    var subjects_disguised = $(".grp-row.subjects_disguised");
    var sd_input = subjects_disguised.find("input");

    var accomodate_sd_change = function() {
        if (sd_input.prop("checked")) {
            dv_input.prop("checked", true);
            ve_input.prop("checked", false);
            dv_input.attr("disabled", true);
        } else {
            dv_input.attr("disabled", false);
        }
    }
    sd_input.change(accomodate_sd_change);
    accomodate_sd_change();
});
