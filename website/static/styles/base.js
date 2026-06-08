function favorite(name) {
    // Get the checkbox
    var checkBox = document.getElementsByName(name)[1];
    var tr = document.getElementsByName(name)[0];
  
    // If the checkbox is checked, display the output text
    if (checkBox.checked == true){
      tr.style.backgroundColor = "#dfd";
    } else {
      tr.style.backgroundColor = "rgba(255, 0, 0, 0.4)";
    }
  }