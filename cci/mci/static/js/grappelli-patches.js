jQuery(document).ready(function ($) {
    var inline_rows = $(".grp-module.grp-tbody,.grp-module.collapse");
    inline_rows.each(function() {
        var marked_for_deletion = $(this).find('input[name*="DELETE"][value="on"]').get();
        if (marked_for_deletion.length) {
            $(this).addClass('grp-predelete');
        }
    });
});

