/*
 *	jQuery.centerToParent
 *	Centers an element within it's parent.
 *
 *	Usage:
 *
 *	To center along both x and y axes: $(el).centerToParent();
 *	To center along the x axis only: $(el).centerToParent("x");
 *	To center along the y axis only: $(el).centerToParent("y");
 *
 */
(function( $ ){

	var css = {
		position: 'relative'
	}

	var methods = {
		init : function() { 
			return private_methods.center($(this));
		},
		x : function() {
			return private_methods.center($(this), true, false);
		},
		y : function() { 
			return private_methods.center($(this), false, true);
		}
	}

	var private_methods = {
		center : function(els, x, y) {
			els.each(function(i){
				var el = $(this);
				var p = el.parent();
				p = p.is('body') ? $(window) : p;
				x = (typeof(x)==='undefined') ? true : x;
				y = (typeof(y)==='undefined') ? true : y;
				if(p.height() <= el.height()) {
					$.error("Selected element is larger than it's parent");
				} else if(y && x) {
					css['top'] = ((p.height() / 2) - (el.height() / 2)) + "px";
					css['left'] = ((p.width() / 2) - (el.width() / 2)) + "px";
				} else if(y) {
					css['top'] = ((p.height() / 2) - (el.height() / 2)) + "px";
				} else if(x) {
					css['left'] = ((p.width() / 2) - (el.width() / 2)) + "px";
				}
				el.css(css);
			});
			return els;
		}
	}

	$.fn.centerToParent = function( method ) {  
		if ( methods[method] ) {
			return methods[ method ].apply( this, Array.prototype.slice.call( arguments, 1 ));
		} else if ( typeof method === 'object' || ! method ) {
			return methods.init.apply( this, arguments );
		} else {
			$.error( 'Method ' +  method + ' does not exist on jQuery.centerToParent' );
		}
	};
})( jQuery );