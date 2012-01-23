$(document).ready(function() { 
    $("#myTable").tablesorter({ 
        // pass the headers argument and assing a object 
        headers: { 
            // assign the secound column (we start counting zero) 
            0: { 
                // disable it by setting the property sorter to false 
                sorter: false 
            }, 
            // assign the third column (we start counting zero) 
            3: { 
                // disable it by setting the property sorter to false 
                sorter: false 
            },
	    9: {
		 // disable it by setting the property sorter to false
                sorter: false
            }		 
        } 
    }); 
});

//returns difference between two arrays
function arr_diff(a1, a2){
                var a=[], diff=[];
                for(var i=0;i<a1.length;i++)
                a[a1[i]]=true;
                for(var i=0;i<a2.length;i++)
                        if(a[a2[i]]) delete a[a2[i]];
                        else a[a2[i]]=true;
                        for(var k in a)
                        diff.push(k);
                         return diff;
}

//return unique entries in array
function unique(a){
   var r = new Array();
   o:for(var i = 0, n = a.length; i < n; i++) {
      for(var x = i + 1 ; x < n; x++)
      {
         if(a[x]==a[i]) continue o;
      }
      r[r.length] = a[i];
   }
   return r;
}
var top_data;

function select(ref){
	 selector_value=ref.value;
        //alert(selector_value);
        tempdir_element=document.getElementById('tempdir');
        tempdir_value=tempdir_element.value;
        //alert(tempdir_value);
	sRNA_element=document.getElementById('sRNA');
        sRNA_value=sRNA_element.value;
	//alert(sRNA_value);
	window.location = "http://insulin.tbi.univie.ac.at/target_search.cgi?page=2&sRNA=" + sRNA_value + "&tempdir=" + tempdir_value + "&top=" + selector_value ; 
	
}


function filter(ref){ 
   var invisible_entries_array = [];
   var selection_id = "selectorid";
   var from_id = "fromid";
   var to_id = "toid";
   var top_all_id = "top.all";
   var top_allid_id ="topid.all";
   var selection_value = parseInt(document.getElementById(selection_id).value);
   var from_value = document.getElementById(from_id).value;
   var to_value = document.getElementById(to_id).value;
   if(!to_value){
     to_value = 10000000;
   }
   if(!from_value){
     from_value = -200;
   }
   var test_array=new Array();
   for(d=1; d<selection_value+1; d++){
			test_array.push("t"+d);
                        var field = "t"+d+"-start";
                        var end_field = "t"+d+"-end";
                        var mRNA_interaction_site_start = parseInt(document.getElementById(field).innerHTML);
                        var mRNA_interaction_site_end = parseInt(document.getElementById(end_field).innerHTML);
                        if(mRNA_interaction_site_start<from_value){
                                parent_id=document.getElementById(field).parentNode.id;
                                //set invisible by adding to invisible_entries_array
                                invisible_entries_array.push(parent_id);
                        }
                        if(mRNA_interaction_site_end>to_value){
                               end_parent_id=document.getElementById(end_field).parentNode.id;
                                //set invisible by adding to invisible_entries_array
                                invisible_entries_array.push(end_parent_id);
                        }
   }
   var visible_entries_array =[];
   visible_entries_array = arr_diff(test_array,invisible_entries_array); 
	 visible_entries_array_length=visible_entries_array.length;
        for (y=0; y<visible_entries_array_length; y++){
                        var visible_filter_field =  visible_entries_array[y];
                        document.getElementById(visible_filter_field).style.display='';
        }

        invisible_entries_array_length=invisible_entries_array.length;
        for (j=0; j<invisible_entries_array_length; j++){
                        var invisible_filter_field = invisible_entries_array[j];
                        document.getElementById(invisible_filter_field).style.display='none';
        }
}

