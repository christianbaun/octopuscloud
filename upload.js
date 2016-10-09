// If frame 1 is loaded, the function prepareUpload() will be executed
$("#frame1").ready(function() {  
   prepareUpload();  
}); 


function prepareUpload(){
     
     // click-handler is registered to button1
     $('#button1').click(function(){
            // if clicked...
            // "Please Wait" window
            $.blockUI({ css: { 
                border: 'none', 
                padding: '15px', 
                backgroundColor: '#000', 
                '-webkit-border-radius': '10px', 
                '-moz-border-radius': '10px', 
                opacity: .5, 
                color: '#fff' 
            } }); 
            
            //register load handler on iframe which triggers uploadData() 
            $('#frame1').load(function(){
                // reload from iframe
                uploadData();
            });
            
            iTargetNumber = 0;
            // call function uploadData()
            uploadData();
            return true;
        });
}


function uploadData() {
    var dataSet = data[iTargetNumber];
    document.getElementById("statusbar").style.width = (iTargetNumber / data.length * 200) + "px";
    
    // if file is uploaded to all servers...
    if (iTargetNumber == data.length) {
       document.getElementById("statustext").innerHTML = "done";
       // Reload browser window
       document.location.reload();
       return;
    }
    
    // status message
    document.getElementById("statustext").innerHTML = "uploading to " + dataSet.sUrl;
            
    //set "action" attribute in HTML form    
    $('#form1').attr('action', dataSet.sUrl);
    
    //set hidden fields in HTML form   
    for (var key in dataSet){
        $('#' + key).attr('value', dataSet[key]);
    }

    //submit HTML form with correct values
    //$('#form1').submit();
    
    // click button1
    $('#button2').click();
    
    // increment variable +1
    iTargetNumber++;
}

// initialize variable 
var iTargetNumber = 0;
