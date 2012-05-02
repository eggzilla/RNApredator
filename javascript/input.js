//define relevant variables once
var data_table = document.getElementById('tableId');
function go(){
    //alert("works");
    var accession_field = document.getElementById("accession_id");
    var tax_id_field = document.getElementById("tax_id");
    accession_check(accession_field);
    tax_check(tax_id_field);   
}


/////////////////////////////////////////////////////////////////////////////
///////////////Cross Browser Code for Tooltips /////////////////////////////
(function(window, document, undefined){
    var XBTooltip = function( element, userConf, tooltip) {
      var config = {
          id: userConf.id|| undefined,
          className: userConf.className || undefined,
          x: userConf.x || 20,
          y: userConf.y || 20,
          text: userConf.text || undefined
      };
	var over = function(event) {
            tooltip.style.display = "block";
	},
	out = function(event) {
        tooltip.style.display = "none";
	},
	move = function(event) {
            event = event ? event : window.event;
        if ( event.pageX == null && event.clientX != null ) {
            var doc = document.documentElement, body = document.body;
            event.pageX = event.clientX + (doc && doc.scrollLeft || body && body.scrollLeft || 0) - (doc && doc.clientLeft || body && body.clientLeft || 0);
            event.pageY = event.clientY + (doc && doc.scrollTop  || body && body.scrollTop  || 0) - (doc && doc.clientTop  || body && body.clientTop  || 0);
        }
            tooltip.style.top = (event.pageY+config.y) + "px";
            tooltip.style.left = (event.pageX+config.x) + "px";
	}
      if (tooltip === undefined && config.id) {
          tooltip = document.getElementById(config.id);
          if (tooltip) tooltip = tooltip.parentNode.removeChild(tooltip)
      }
	if (tooltip === undefined && config.text) {
            tooltip = document.createElement("div");
        if (config.id) tooltip.id= config.id;
            tooltip.innerHTML = config.text;
	}
	if (config.className) tooltip.className = config.className;
	tooltip = document.body.appendChild(tooltip);
	tooltip.style.position = "absolute";
	element.onmouseover = over;
	element.onmouseout = out;
	element.onmousemove = move;
	over();
    };
    window.XBTooltip = window.XBT = XBTooltip;
})(this, this.document);

////////////////////////////////////////////////////////////////////////
////////Process tax-id Input//////////////////////////////////////

function tax_check(ref){
    //perform lookup if species name or tax_id or accession number exists starting with a certain length of input
    //first determine the calling input element and analyse accordingly
    var tax_input_field = ref;
    var tax_input_field_value = ref.value;
    var tax_input_field_value_length = tax_input_field_value.length;
    var minimal_tax_length = 3;
    //alert("got here:"+ tax_input_field_value_length+ "-" + tax_input_field_value + tax_input_field);
        if(tax_input_field_value_length>2){
            var current_input = document.getElementById(tax_input_field_value);
            //Accession-Length-Taxid-TaxName-Replicon-Create Date
            //alert(current_input_child.innerHTML);
            if(current_input != null){
                var current_input_id = current_input.id;
		//get all children from tax-id
		//<tr><td id="634499" >634499: Erwinia pyrifoliae Ep1/96,NC_012214,chromosome  :NC_013263,plasmid pEP36 :NC_013264,plasmid pEP03 :NC_013265,plasmid pEP05 :NC_013954,plasmid pEP2.6</td></tr>
                var current_input_children = current_input.innerHTML;
		var children_array = new Array();
		children_array = current_input_children.split(':');
		var children_array_length = children_array.length;
		var code =
                    "<p align=\"left\">NCBI Tax-id:<strong id=\"tax-id\">" + current_input_id + "</strong></p>";
		for (y=0; y<children_array_length; y++){
		    if(y==1){
				    var split_array = new Array();
			split_array = children_array[1].split(',');
			var tax_name = split_array[0];
			var accession_number = split_array[1];
			var replicon = split_array[2];
			code = code + "<p align=\"left\">Tax-Name:" + tax_name +"</p>";
			code = code + "<p align=\"left\">Associated Chromsoms/Plasmids:</p>";
			code = code + "<p align=\"left\">*" + accession_number + "-" + replicon + "</p>";
		    }
                    if(y>1){
			var split_array = new Array();   
                        split_array = children_array[y].split(',');
                        var accession_number = split_array[0];
                        var replicon = split_array[1];
					code = code + "<p align=\"left\">*" + accession_number +"-" + replicon + "</p>";		
		    }
		}
		//Produce Children Output text in for loop and include it in final output text
                //match
                //alert(current_input.value);
		code = code +
		    "<p align=\"left\" id=\"step2_buttons\" >Proceed <a href=\"#\" style=\"border-style: none\"><img src=\"pictures/confirm.png\" style=\"border-style:none\" id=\"step2_confirm\" alt=\"confirm\" onclick=\"tax_id_confirm(this)\" ></a>"+
                    " Back <a href=\"#\"><img src=\"pictures/deny.png\" style=\"border-style: none\" id=\"step2_reseter\"  alt=\"reset\" onclick=\"tax_id_check_back(this)\"></a></p>";
                var myText = document.createTextNode(code);
                //disable eventhandlers from step 
                //document.getElementById("accession_id").onkeyup = null;
                //document.getElementById("tax_id").onkeyup = null;
                //insert next step
                document.getElementById("step2_content").innerHTML=code;
            }
        }
}

function tax_id_check_back(){
    document.getElementById("step2_content").innerHTML="";
    document.getElementById("accession_id").value="";
    document.getElementById("tax_id").value="";
}

function tax_id_submitter_back(ref){
    //hide buttons from 3nd step and disable eventhandlers
    document.getElementById("sRNA-Input").disabled=false;
    document.getElementById("step3_buttons").style.display='';
    document.getElementById("step3_buttons").innerHTML="Proceed <a href=\"#\"><img src=\"pictures/confirm.png\"  style=\"border-style:none\" id=\"step3_confirm\"  alt=\"confirm\" onclick=\"tax_id_submitter(this)\"></a>"+
        " Back  <a href=\"#\"><img src=\"pictures/deny.png\" alt=\"deny\" style=\"border-style:none\" id=\"step3_reseter\"  onclick=\"tax_id_confirm_back(this)\"></a>";
    //set new stuff
    document.getElementById("step4_content").innerHTML="";
}

function tax_id_confirm(ref){
    var tax_id_value=document.getElementById("tax-id").innerHTML;
    var code ="<form action=\"target_search.cgi\" id=\"submit-form\"  method=\"post\" enctype=\"multipart/form-data\">" +
        "<textarea id=\"sRNA-Input\"  name=\"sRNA-submit\" type=\"text\" cols=\"40\" rows=\"4\"  maxlength=\"500\" onkeyup=\"lock_sRNA_upload_input(this)\"></textarea>" +
        "<div id=\"validation_message\"></div>"+
        "<strong>OR</strong><br>"+
        "Upload a fasta-file:<br>"+
        "<input name=\"fasta-file\" id=\"file-upload\" size=\"30\" type=\"file\" onchange=\"lock_sRNA_sequence_input(this)\"><br>"+
	"<input id=\"tax-id-submit\"  value=\""+ tax_id_value +"\" name=\"tax-id\" type=\"hidden\"  maxlength=\"30\">"+
        "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +
        "<div id=\"file_message\" style=\"color: red;\"></div>"+
        //"<br>Provide email-address(optional):<br>"+
        //"<input id=\"email-address\"  value=\"\" name=\"email\" type=\"text\" maxlength=\"50\"><br>"+
        "<div id=\"email_message\"></div>"+
	"<br><input type=\"checkbox\" id=\"suboptimal_toggle\" name=\"suboptimal_toggle\" value=\"on\">include suboptimal interactions<br>"+
        "<br><input type=\"button\" value=\"Predict\" onclick=\"accession_submitter(this)\">"+
        "<input type=\"reset\" value=\"Back\" onclick=\"tax_id_confirm_back(this)\" >"+
        "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
        "</form>";
    var myText = document.createTextNode(code);
    //hide buttons from 2nd step and disable eventhandlers
    document.getElementById("tax_id").disabled=true;
    document.getElementById("accession_id").disabled=true;
    document.getElementById("step2_buttons").style.display='none';
    document.getElementById("step2_confirm").onclick = null;
    document.getElementById("step2_reseter").onclick = null;
    //set new stuff
    document.getElementById("step3_content").innerHTML=code;
}

function tax_id_confirm_back(ref){
    //Go back to Genome confirm by reversing settings from accession_confirm
    document.getElementById("accession_id").disabled=false;
    document.getElementById("tax_id").disabled=false;
    document.getElementById("step2_buttons").style.display='';
    //var step2_confirm_element=document.getElementById("step2_confirm");
    //document.getElementById("step2_confirm").onclick ="accession_confirm()";
    //document.getElementById("step2_reseter").onclick ="reseter()";
    //set new stuff
    document.getElementById("step2_buttons").innerHTML="Proceed <a href=\"#\"><img src=\"pictures/confirm.png\" style=\"border-style:none\" id=\"step2_confirm\" alt=\"confirm\" onclick=\"tax_id_confirm(this)\"></a>"+
        " Back  <a href=\"#\"><img src=\"pictures/deny.png\" style=\"border-style:none\" id=\"step2_reseter\"  alt=\"reset\" onclick=\"tax_id_check_back(this)(this)\"></a>";
    document.getElementById("step3_content").innerHTML="";
}

function tax_id_submitter(ref){
    //get genome - taxid to submit
    var tax_id_value = document.getElementById("tax-id").innerHTML;
    //get sRNA - String
    var sRNA_input = document.getElementById("sRNA-Input").value;
    var isok=true;
    var is_fasta=false;
    var sRNA_number;
    var sRNA_header_output="";
    var provide_email=false;	
    if(sRNA_input.match(/>/gi)){
        var is_fasta=true;
        var error_message="Fasta-Format detected:<br>";
        //get number of fasta headers
        var sRNA_match=sRNA_input.match(/>/gi);
        sRNA_number=sRNA_match.length;
        if(sRNA_number>1){
            provide_email=true;
                }
        if(sRNA_number>5){
            error_message=error_message + "sRNA fasta-file must not contain more than 5 sequences<br>";
            isok=false;
        }
        //split at fasta header begin > now we have separated the sRNA 
        var sRNA_splits=sRNA_input.split(">");
        //split each sRNA at first linebreak..1. part header 2nd part sequence and treat each accordingly
        for(var i = 1; i < sRNA_splits.length; ++i){
            var sRNA_entry=sRNA_splits[i].split(/\n/);
            //now parse header for correctness
            var sRNA_header=sRNA_entry[0];
            sRNA_header_output=sRNA_header_output + sRNA_header+"<br>";
            if(sRNA_header.match(/[!@#%&*~|//]+/gi)){
            var match=sRNA_header.match(/[!@#%&*~|//]+/gi);
        error_message=error_message + "sRNA #"+i+" header contains invalid characters:"+match+"<br>";
                                                isok=false;
    }
    var sRNA_sequence=sRNA_entry[1];
    //first remove whithespaces and linebreaks
                                        sRNA_sequence = sRNA_sequence.replace(/\n+/g, "");
    sRNA_sequence = sRNA_sequence.replace(/\s+/g, "");
    if(sRNA_sequence.length<5){
        error_message=error_message + "sRNA #"+i+" sequence is too short, has to be >4 letters<br>";
        isok=false;
    }
    if(sRNA_sequence.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|//]+/gi)){
                                                var match=sRNA_sequence.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|//]+/gi);
error_message=error_message + "sRNA #"+i+" sequence contains invalid characters:"+match+"<br>";
isok=false;
}
}
//remove linebreaks and spaces in the sequence

//if everything is correct we submit, otherwise we print the error
if(!isok){
    document.getElementById("validation_message").innerHTML="<font color=\"#FF0000\">"+error_message+"</font>";
}
}else{
    //only seq, no fasta
    sRNA_input = sRNA_input.replace(/\n+/g, "");
    sRNA_input = sRNA_input.replace(/\s+/g, "");
    if(sRNA_input.length<5 || sRNA_input.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|//]+/gi)){
    var match = sRNA_input.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|//]+/gi);
document.getElementById("validation_message").innerHTML="<font color=\"#FF0000\">Non-Fasta Format detected: Enter a valid sequence >4 letters not containing:"+ match +"</font>";
isok=false;
}
}	
if(isok){
    document.getElementById("validation_message").innerHTML="";
    var email_text="<br>Please provide email-address for notification:<br>"+
        "<input id=\"email\"  value=\"\" name=\"email\" type=\"text\" maxlength=\"50\">(optional)<br>";
    //final submission form for tax_id
    if(is_fasta){
       	var code ="<form action=\"target_search.cgi\" method=\"post\">" +
            "<u>Tax-id:</u> <br><input id=\"tax-id-submit\"  value=\""+ tax_id_value +"\" name=\"tax-id\" type=\"hidden\"  maxlength=\"30\">" +
            tax_id_value  +"<br><br>"+
            "<u>sRNA Sequence:</u><br><input id=\"sRNA-submit\" value=\""+sRNA_input+"\"  name=\"sRNA\" type=\"hidden\"  maxlength=\"500\">" +
	    "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +	
            "Fasta with "+ sRNA_number +" sequences:<br>" + sRNA_header_output + 
            email_text+
	    "<input type=\"submit\" value=\"Predict\">"+
	    "<input type=\"reset\" value=\"Back\" onclick=\"tax_id_submitter_back(this)\" >"+
            "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
            "</form>"
        var myText = document.createTextNode(code);
        //hide buttons from 3nd step and disable eventhandlers
        document.getElementById("sRNA-Input").disabled=true;
        document.getElementById("step3_buttons").style.display='none';
        document.getElementById("step3_confirm").onclick = null;
        document.getElementById("step3_reseter").onclick = null;
        //set new stuff
        document.getElementById("step4_content").innerHTML=code;
    }else{
	var code ="<form action=\"target_search.cgi\" method=\"post\">" +
            "<u>Tax-id:</u> <br><input id=\"tax-id-submit\"  value=\""+ tax_id_value +"\" name=\"tax-id\" type=\"hidden\"  maxlength=\"30\">" +
            tax_id_value  +"<br><br>"+
            "<u>sRNA Sequence:</u><br><input id=\"sRNA-submit\" value=\""+sRNA_input+"\"  name=\"sRNA\" type=\"hidden\"  maxlength=\"500\">" +
            "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +    
            sRNA_input +"<br>"+
            "<input type=\"submit\" value=\"Predict\">"+
            "<input type=\"reset\" value=\"Back\" onclick=\"tax_id_submitter_back(this)\" >"+
            "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
            "</form>"
        var myText = document.createTextNode(code);
        //hide buttons from 3nd step and disable eventhandlers
        document.getElementById("sRNA-Input").disabled=true;
        document.getElementById("step3_buttons").style.display='none';
        document.getElementById("step3_confirm").onclick = null;
        document.getElementById("step3_reseter").onclick = null;
        //set new stuff
        document.getElementById("step4_content").innerHTML=code;	
    }
}
}

///////////////////////////////////////////////////////////////////////////////////
/////////////Process accession-id Input //////////////////////////////////////////

function accession_check(ref){
//perform lookup if species name or tax_id or accession number exists starting with a certain length of input
    //first determine the calling input element and analyse accordingly
    var input_field = ref;
    var input_field_value = ref.value;
    var input_field_value_lenght = ref.value.length;
    // if the entered accession number has the required length of 9 or above try to match
    // it to a available accession number.. otherwise print no matching accession number found
    // in the confimration field
    var minimal_accession_length = 7;
    if(input_field_value_lenght>=minimal_accession_length ){
	//alert("bigger");
	var current_input = document.getElementById(input_field_value);
	//Accession-Length-Taxid-TaxName-Replicon-Create Date
	//alert(current_input_child.innerHTML);
	if(current_input != null){
	    var current_input_id = current_input.id;
	    var current_input_child_name = current_input.children[3].innerHTML;
            var current_input_child_taxid = current_input.children[2].innerHTML;
            var current_input_child_replicon = current_input.children[4].innerHTML;
	    //match
	    //alert(current_input.value);
	    var code =
	        "<p align=\"left\">NCBI Accession Number:<strong id=\"accession_number\">" + current_input_id + "</strong></p>"+
        	"<p align=\"left\">Name:" + current_input_child_name +"</p>"+
		"<p align=\"left\">Tax-id:" + current_input_child_taxid +"</p>"+
		"<p align=\"left\">Replicon:" + current_input_child_replicon +"</p>"+
               	"<p align=\"left\" id=\"step2_buttons\" >Proceed <a href=\"#\"><img src=\"pictures/confirm.png\" style=\"border-style:none\" id=\"step2_confirm\" alt=\"confirm\" onclick=\"accession_confirm(this)\"></a>"+
                " Back  <a href=\"#\"><img src=\"pictures/deny.png\" style=\"border-style:none\" id=\"step2_reseter\"  alt=\"reset\" onclick=\"accession_check_back()\"></a></p>";
            var myText = document.createTextNode(code);
	    //disable eventhandlers from step 
	    //document.getElementById("accession_id").onkeyup = null;
	    //document.getElementById("tax_id").onkeyup = null;
	    //insert next step
			document.getElementById("step2_content").innerHTML=code;	
	}
    } 
}

function accession_check_back(){
    document.getElementById("step2_content").innerHTML="";
    document.getElementById("accession_id").value="";	
    document.getElementById("tax_id").value="";
}

function lock_sRNA_sequence_input(ref){
    var upload_field=document.getElementById("file-upload");
		if(upload_field.value != ""){
		    //lock sRNA-sequence input
		    document.getElementById("sRNA-Input").disabled=true;
		}else{
		    document.getElementById("sRNA-Input").disabled=false;
		}
}		

function lock_sRNA_upload_input(ref){
    var upload_field=document.getElementById("sRNA-Input");
    if(upload_field.value != ""){
        //lock sRNA-sequence input
        document.getElementById("file-upload").disabled=true;
                }else{
                    document.getElementById("file-upload").disabled=false;
                }
}


function accession_confirm(ref){
    var accession_number_value=document.getElementById("accession_number").innerHTML;
    var code ="<form action=\"target_search.cgi\" id=\"submit-form\"  method=\"post\"  enctype=\"multipart/form-data\">" +
        "<textarea id=\"sRNA-Input\"  name=\"sRNA-submit\" type=\"text\" cols=\"40\" rows=\"3\"  maxlength=\"500\" onkeyup=\"lock_sRNA_upload_input(this)\"></textarea>" +
	"<div id=\"validation_message\"></div>"+
	"<strong>OR</strong><br>"+
	"Upload a fasta-file:<br>"+
	"<input name=\"fasta-file\" id=\"file-upload\" size=\"30\" type=\"file\" onchange=\"lock_sRNA_sequence_input(this)\"><br>"+
	"<input id=\"accession-number-submit\" value=\""+accession_number_value+"\" name=\"accession\" type=\"hidden\"  maxlength=\"30\">" +
        "<input id=\"page\" value=\"1\"  name=\"page\" type=\"hidden\"  maxlength=\"1\">" +
	"<div id=\"file_message\" style=\"color: red;\"></div>"+
        //"<br>Provide email-address (optional):"+
        //"<input id=\"email-address\"  value=\"\" name=\"email\" type=\"text\" maxlength=\"30\"><br>"+
	"<div id=\"email_message\"></div>"+
	"<br><input type=\"checkbox\" id=\"suboptimal_toggle\" name=\"suboptimal_toggle\" value=\"on\">include suboptimal interactions<br>"+
        "<br><input type=\"button\" value=\"Predict\" onclick=\"accession_submitter(this)\">"+
        "<input type=\"reset\" value=\"Back\" onclick=\"accession_confirm_back(this)\" >"+
        "<input type=\"reset\" value=\"Reset\" onclick=\"reseter(this)\" >"+
	"</form>";				
    var myText = document.createTextNode(code);
    //hide buttons from 2nd step and disable eventhandlers
    document.getElementById("accession_id").disabled=true;
    document.getElementById("tax_id").disabled=true;
    document.getElementById("step2_buttons").style.display='none';
    document.getElementById("step2_confirm").onclick =null;
    document.getElementById("step2_reseter").onclick =null;
			//set new stuff
    document.getElementById("step3_content").innerHTML=code;
}

function accession_confirm_back(ref){
    //Go back to Genome confirm by reversing settings from accession_confirm
    document.getElementById("accession_id").disabled=false;
    document.getElementById("tax_id").disabled=false;
    document.getElementById("step2_buttons").style.display='';
    //var step2_confirm_element=document.getElementById("step2_confirm");
    //document.getElementById("step2_confirm").onclick ="accession_confirm()";
    //document.getElementById("step2_reseter").onclick ="reseter()";
    //set new stuff
    document.getElementById("step2_buttons").innerHTML="Proceed <a href=\"#\"><img src=\"pictures/confirm.png\" style=\"border-style:none\" id=\"step2_confirm\" alt=\"confirm\" onclick=\"accession_confirm(this)\"></a>"+
        " Back  <a href=\"#\"><img src=\"pictures/deny.png\" style=\"border-style:none\" id=\"step2_reseter\"  alt=\"reset\" onclick=\"reseter(this)\"></a>";
    document.getElementById("step3_content").innerHTML="";
}


function reseter(ref){
    //alert("reset");
    window.location = 'http://rna.tbi.univie.ac.at/RNApredator2/target_search.cgi';	
    // send reload header?
    
}

function sample(){
    var accession ="NC_000913";
    var sRNA_seq ="GAAAGACGCGCAUUUGUUAUCAUCAUCCCUGAAUUCAGAGAUGAAAUUUUGGCCACUCACGAGUGGCCUUUUUCUUUU";
    //set accession field and trigger eventhandler
    var accession_field = document.getElementById("accession_id");
    accession_field.value=accession;
    accession_field.onkeyup(accession_field);
    document.getElementById("step2_confirm").onclick();
    document.getElementById("sRNA-Input").value=sRNA_seq;
    document.getElementById("step3_confirm").onclick();
}

function accession_submitter_back(ref){
    //hide buttons from 3nd step and disable eventhandlers
    document.getElementById("sRNA-Input").disabled=false;
    document.getElementById("step3_buttons").style.display='';
    document.getElementById("step3_buttons").innerHTML="Proceed <a href=\"#\"><img src=\"pictures/confirm.png\"  style=\"border-style:none\" id=\"step3_confirm\"  alt=\"confirm\" onclick=\"accession_submitter(this)\"></a>"+
        " Back  <a href=\"#\"><img src=\"pictures/deny.png\" alt=\"deny\" style=\"border-style:none\" id=\"step3_reseter\"  onclick=\"accession_confirm_back(this)\"></a>";
    //set new stuff
    document.getElementById("step4_content").innerHTML="";
}


function accession_submitter(ref){
    //get genome - taxid to submit
    var isok=true;
    //get sRNA - String
    var sRNA_input = document.getElementById("sRNA-Input").value;
    //var email_address= document.getElementById("email-address").value;
    var is_fasta=false;
    var sRNA_number;
    var sRNA_header_output="";
    //if(email_address!=""){
//	if(email_address.match(/[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?/)){
    //ok
  //  document.getElementById("email_message").innerHTML="";
//}else{
  //  document.getElementById("email_message").innerHTML="<font color=\"#FF0000\">Email address is invalid</font>";
    //isok=false;
//}
//}
//if we find < signs we assume it is fasta
if(document.getElementById("file-upload").value!=null){
    //do not check will be done on serverside
}else{
    if(sRNA_input.match(/>/gi)){
	var is_fasta=true;
	var error_message="Fasta-Format detected:<br>";
	//get number of fasta headers
	var sRNA_match=sRNA_input.match(/>/gi);
	sRNA_number=sRNA_match.length;
	if(sRNA_number>5){
	    error_message=error_message + "sRNA fasta-file must not contain more than 5 sequences<br>";
	    isok=false;
	}
	//split at fasta header begin > now we have separated the sRNA 
	var sRNA_splits=sRNA_input.split(">");
	//split each sRNA at first linebreak..1. part header 2nd part sequence and treat each accordingly
	for(var i = 1; i < sRNA_splits.length; ++i){
	    var sRNA_entry=sRNA_splits[i].split(/\n/);
	    //now parse header for correctness
	    var sRNA_header=sRNA_entry.shift();
	    sRNA_header_output=sRNA_header_output + sRNA_header+"<br>";
	    if(sRNA_header.match(/[!@#%&*~|]+/gi)){
		var match=sRNA_header.match(/[!@#%&*~|]+/gi);
		error_message=error_message + "sRNA #"+i+" header contains invalid characters:"+match+"<br>";
		isok=false;
	    }
	    //header is removed we join the remaining strin without linebreaks again
	    var sRNA_sequence=sRNA_entry.join("");
	    //first remove whithespaces and linebreaks
	    sRNA_sequence = sRNA_sequence.replace(/\s+/g, "");	
	    if(sRNA_sequence.length<5){
		error_message=error_message + "sRNA #"+i+" sequence is too short, has to be >4 letters<br>";
		isok=false;
	    }
	    if(sRNA_sequence.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|]+/gi)){
		var match=sRNA_sequence.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|]+/gi);
							error_message=error_message + "sRNA #"+i+" sequence contains invalid characters:"+match+"<br>";
		isok=false;
            }
	}	
	//remove linebreaks and spaces in the sequence
	
	//if everything is correct we sumit, otherwise we print the error
	if(!isok){
	    document.getElementById("validation_message").innerHTML="<font color=\"#FF0000\">"+error_message+"</font>";
	}
    }else{
	//only seq, no fasta
	sRNA_input = sRNA_input.replace(/\n+/g, "");
        sRNA_input = sRNA_input.replace(/\s+/g, "");
	if(sRNA_input.length<5 || sRNA_input.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|]+/gi)){
            var match = sRNA_input.match(/[QWERYIOPSDFHJKLZXVBNM><!@#%&*~|]+/gi);
            document.getElementById("validation_message").innerHTML="<font color=\"#FF0000\">Non-Fasta Format detected: Enter a valid sequence >4 letters not containing:"+ match +"</font>";
            isok=false;
        }
    }
}
if(isok){
    document.forms["submit-form"].submit();	
}
}	

