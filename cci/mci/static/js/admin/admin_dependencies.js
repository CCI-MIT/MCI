function activeCheckbox(inputContainer) {
    var active = inputContainer.find("input").is(":checked");
    return active;
}

function activeDropdown(activeValues) {
    return function(selectContainer) {
        return _.contains(activeValues, selectContainer.find("select").val());
    }
}

var showHideEffect = "blind";

function show(dependent_rows, immediate) {
//    console.log("show >> immediate:", immediate);
    if (immediate) {
        dependent_rows.show();
    } else {
        dependent_rows.show(showHideEffect, 1000);
    }
}

function hide(dependent_rows, immediate) {
//    console.log("hide >> immediate:", immediate);
    if (immediate) {
        dependent_rows.hide();
    } else {
        dependent_rows.hide(showHideEffect, 1000);
    }
}

function showOrHideDependentRows(immediate, active, dependent_row_selectors) {
    return function shdr() {
//        console.log("shdr >> \n\tdependent_row_selectors:", dependent_row_selectors, "\n\tthis:", this);

        function findDependentRowsInContainer(container) {
//            console.log("findDependentRowsInContainer >> container:", container.get());

            var dependent_rows_in_container = _.map(dependent_row_selectors, function(drs) {
                return container.find(drs);
            });
            var everyDRFound = _.every(dependent_rows_in_container, function(dr) {
                return dr.length > 0;
            });
            if (everyDRFound) {
//                console.log("findDependentRowsInContainer >> found all rows:", dependent_rows_in_container);
                return dependent_rows_in_container;
            } else {
                var par = container.parent();
                if (par.length) {
                    return findDependentRowsInContainer(par);
                } else {
                    var rows_not_found = _.filter(dependent_rows_in_container, function(dr) {
                        return dr.length == 0;
                    });
                    console.error("Searched document, didn't find these dependent rows:", rows_not_found);
                }
            }
        }

        var dependent_rows = findDependentRowsInContainer($(this));

        if (active($(this))) {
            _.each(dependent_rows, function(dr) {
                show(dr, immediate);
            }); 
        } else {
            _.each(dependent_rows, function(dr) {
                hide(dr, immediate);
            });
        }
    }
}

function defineDependency(controlling_row_selector, active, dependent_row_selectors) {
    var controlling_rows = $(controlling_row_selector);    
    controlling_rows.on('change', showOrHideDependentRows(false, active, dependent_row_selectors));
    controlling_rows.each(showOrHideDependentRows(true, active, dependent_row_selectors));
}
