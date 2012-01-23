$(document).ready(function() {
   $("#myTable").tablesorter({
        // pass the headers argument and assing a object
        headers: {
        }
    });
   $("#myTable1").tablesorter({
        // pass the headers argument and assing a object
        headers: {
        }
    });
   $("#myTable2").tablesorter({
        // pass the headers argument and assing a object
        headers: {
        }
    });
    $('.demo5').collapser({
        target: 'prev',
	targetOnly: 'table',
	effect: 'slide',
        expandHtml: 'Expand Table',
        collapseHtml: 'Collapse Table',
        expandClass: 'expIco',
        collapseClass: 'collIco'
     });

     $("#tabs").tabs();

});

