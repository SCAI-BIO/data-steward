<template>
  <div>
    <nav class="light-blue-bg">
      <div class="nav-wrapper">
        
        <a href="#" data-target="mobile-demo" class="sidenav-trigger"
          ><i class="material-icons">menu</i></a
        >

        <ul id="nav-mobile" class="left hide-on-med-and-down">
          <li><a href="/data-steward" class="pt-10 hover-none">
          <img src="../assets/logo_data_steward_no_text.png" width=50/>
          </a></li>

          <!-- Dropdown Trigger -->
          <li><a href="/data-steward/datapoints">Data Upload</a></li>
          <li>
            <a class="dropdown-trigger" href="#" data-target="dropdown1"
              >Model Upload</a
            >
          </li>

          <!-- Dropdown Structure -->
          <ul id="dropdown1" class="dropdown-content">
            <li>
              <a href="/data-steward/datamodel">Model Upload</a>
            </li>
            <li><a href="/data-steward/semantic-dump">Asset Upload</a></li>
            <li><a href="/data-steward/owl-upload">OWL upload</a></li>
          </ul>

          <li><a href="/data-steward/edit">Wizard</a></li>
          
          <li><a class="dropdown-trigger" data-target="dropdown2" href="#">Model Explorer</a></li>  
          <ul id="dropdown2" class="dropdown-content">
            <li>
              <a href="/data-steward/graph">Graph</a>
            </li>
            <li><a href="/data-steward/table">Table</a></li>
             <li><a href="/data-steward/metrics">Statistics</a></li>
          </ul>
          <li><a href="/clinical-viewer">Clinical Viewer</a></li>
          <li><a href="/data-steward/download">Download</a></li>
          <li><a href="/data-steward/contact">Contact</a></li>
        </ul>
      </div>
    </nav>
    <ul class="sidenav" id="mobile-demo">
      <li><a href="/data-steward">Home</a></li>
      <li><a href="/data-steward/datapoints">Data Upload</a></li>
      <li><a href="/data-steward/datamodel">Model Upload</a></li>
      <li>
        <a href="/data-steward/datamodel">Model Upload</a>
      </li>
      <li><a href="/data-steward/owl-upload">OWL Upload</a></li>

      <li><a href="/data-steward/edit">Wizard</a></li>
      
      <li><a href="/data-steward/graph">Visualization</a></li>
      <li><a href="/clinical-viewer">Clinical Viewer</a></li>
      
      <li><a href="/data-steward/download">Download</a></li>
    </ul>
  </div>
</template>


<script>
import M from "materialize-css";
export default {
  name: "stewardheader",
  created() {
    var elems = document.querySelectorAll(".dropdown-trigger");
    M.Dropdown.init(elems);
  },
};
</script>
