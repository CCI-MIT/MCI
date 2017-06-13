jQuery(document).ready(function ($) {
    defineDependency(".grp-row.display_name_page", activeCheckbox, [".display_name_time"]);
    defineDependency(".grp-row.roster_page", activeCheckbox, [".roster_time"]);
    defineDependency(".grp-row.subjects_disguised", activeCheckbox, ["#disguise_selections-group"]);
    defineDependency(".grp-row.group_creation_method", activeDropdown(["X"]), [".grp-row.group_creation_matrix"]);

    $("#id_task_groups").multiSelect();
    $("#id_usergroups").multiSelect();
});
