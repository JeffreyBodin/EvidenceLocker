// enable/disable signature fields based on perjury oath being selected
$("#oathcheck").change(function(){
  $('.signature-field').prop('disabled', !$('#oathcheck').prop('checked'));
  $('#sig-section').toggleClass('text-muted');
  var txt ='Save Changes';
  if (window.location.href.endsWith("/create_exhibit")) {
    txt="Save"
  }
  if ($('#oathcheck').prop('checked')){
    txt='Sign and Save'
  }
  $('#savebutton').prop('value', txt)
});


//post utility function
function post(url, callback, errortext) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("csrf_token", csrftoken());
  xhr.withCredentials=true;
  xhr.onerror=function() { 
      $('#toast-error .toast-text').text(errortext);
      $('#toast-error').toast('show')
  };
  xhr.onload = function() {
    if (xhr.status >= 200 && xhr.status < 300) {
      callback();
    } else {
      xhr.onerror();
    }
  };
  xhr.send(form);
}

//delete utility function
function delete_toast(url) {
  var xhr = new XMLHttpRequest();
  xhr.open("DELETE", url, true);
  var form = new FormData()
  form.append("csrf_token", csrftoken());
  xhr.withCredentials=true;
  xhr.onerror=function() { 
      $('#toast-error .toast-text').text("Something went wrong. Please try again later.");
      $('#toast-error').toast('show')
  };
  xhr.onload = function() {
    data=JSON.parse(xhr.response);
    if (xhr.status >= 200 && xhr.status < 300) {
      $('#toast-success .toast-text').text(data['message']);
      $('#toast-success').toast('show')
    } else if (xhr.status >= 300 && xhr.status < 400 ) {
      window.location.href=data['redirect']
    } else {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
    }
  };
  xhr.send(form)
}

//attach delete function to delete buttons
$(".delete-btn").click(function(){
  delete_toast(window.location.href)
})

//post form toast utility function
function post_form_toast(form_id) {
  var xhr = new XMLHttpRequest();
  url=$('#'+form_id).prop('action');
  xhr.open("POST", $('#'+form_id).prop('action'), true);
  var form = new FormData(document.querySelector('#'+form_id));
  xhr.withCredentials=true;
  xhr.onerror=function() { 
      $('#toast-error .toast-text').text("Something went wrong. Please try again later.");
      $('#toast-error').toast('show')
  };
  xhr.onload = function() {
    data=JSON.parse(xhr.response);
    if (xhr.status >= 200 && xhr.status < 300) {
      $('#toast-success .toast-text').text(data['message']);
      $('#toast-success').toast('show')
    } else if (xhr.status >= 300 && xhr.status < 400 ) {
      window.location.href=data['redirect']
    } else {
      $('#toast-error .toast-text').text(data['error']);
      $('#toast-error').toast('show')
    }
  };
  xhr.send(form);
}

//attach post_form_toast to form "submit" buttons
$('.toast-form-submit').click(function(){
  post_form_toast($(this).data('form'));
})

//Dark mode toggle
$("#dark-mode-toggle").click(function(){
  post('/toggle_darkmode',
    callback=function(){
      var s = $('#mainstyle')
      if( s.prop('href').endsWith('light.css')){
        s.prop('href','/assets/style/dark.css?v=1.0.17')
      }
      else{
        s.prop('href','/assets/style/light.css?v=1.0.17')
      }
    })
})


//Image attach preview

$('#file-upload').on('change', function(e){
  f=document.getElementById('file-upload');
  $('#filename-show').text("Change Image");

  var fileReader = new FileReader();
  fileReader.readAsDataURL(f.files[0]);
  fileReader.addEventListener("load", function () {
    $('#image-preview').attr('src', this.result);
  });  

  $("#image_action").attr("value", "replace");
  $("#image-delete-button").removeClass("d-none")
})

//Image delete preview
$("#image-delete-button").click(function(){
  $("#image-delete-button").addClass("d-none");
  $("#image_action").attr("value", "delete");
  $("#image-preview").attr("src",'');
  $("#filename-show").text("Select Image")
})

//Image display toggle
$("#img-toggle-button").click(function(){
  $("#img-toggle-icon").toggleClass("fa-image");
  $("#img-toggle-icon").toggleClass("fa-image-slash");
  $("#img-toggle-display").toggleClass("d-none")
})


//Auto-expanding textarea

$("textarea").on("input", function () {
  this.style.height = "auto";
  this.style.height = (this.scrollHeight+3) + "px";
});

$("#editModal").on("shown.bs.modal", function(){
  $("textarea").each(function () {
    this.style.height = "auto";
    this.style.height = (this.scrollHeight+3) + "px";
  })
});