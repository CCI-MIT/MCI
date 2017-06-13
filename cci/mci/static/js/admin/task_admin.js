jQuery(document).ready(function ($) {
    var selectorsTilesFields = [ ".starting_width"
                               , ".starting_height"
                               , ".pct_tiles_on"
                               , ".tiles_preview_seconds"
                               ];
    defineDependency(".grp-row.task_type", activeDropdown(["I"]), selectorsTilesFields);

    var selectorsDependentOnConc = [ "#taskconcentrationroundtemplateindex_set-group"
                                   , ".time_unmatched_pairs_remain_faceup"
                                   , ".pairs_in_generated_round"
                                   ];
    defineDependency(".grp-row.task_type", activeDropdown(["C"]), selectorsDependentOnConc);

    var selectorsDependentOnSquares = [ "#squares_round_template_indices-group" ];
    defineDependency(".grp-row.task_type", activeDropdown(["S"]), selectorsDependentOnSquares);

    var taskTypesEL = ["T", "G"];
    defineDependency(".grp-row.task_type", activeDropdown(taskTypesEL), [ ".chat_enabled"
                                                                        , ".scribe"
                                                                        ]);

    var taskTypesRTG = ["C", "I", "S"];
    var selectorsRTGFields = [ ".time_before_play"
                             , ".time_between_rounds"
                             , ".preplay_countdown_sublabel"
                             ];
    defineDependency(".grp-row.task_type", activeDropdown(taskTypesRTG), selectorsRTGFields);
    var selectorsDependentOnGrid = [ "#taskgriditem_set-group"
                                   , ".fieldset-grid-workspace"
                                   ];
    defineDependency(".grp-row.task_type", activeDropdown(['G']), selectorsDependentOnGrid);
});
