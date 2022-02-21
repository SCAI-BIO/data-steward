<template>
  <div>
    <div class="parallax-1"></div>

    <div class="row container">
      <div class="col s12">
        <h1>Welcome to the SCAI Data Steward</h1>
        <p class="flow-text">
          This service provides several features such as uploading and editing
          the current clinical datamodel which is used right now to normalize
          data in the used in the <a href="/clinical-viewer">Clinical Viewer</a>.
          Moreover you can download the datamodel in .xlsx format after you
          added attributes, mappings or new sources.
         
        </p>
        <img src="../assets/How it works.png"  width="500px"/>
        <p class="flow-text">
          Another key feature of the Data-Steward is the graph explorer of the
          datamodel. That graph provides deeper insight into the model currently
          used by SCAI. Edges in that graph represent the connections between
          different sources and its attributes as well as the mappings between
          those attributes.
        </p>
      </div>
    </div>

    <div class="parallax-2"></div>

    <div class="row container" style="min-height: 300px">
      <div class="col s12">
        <h1>Normalization with OLS</h1>
        <p class="flow-text">
          The graph visualization provides an uplink with
          <a href="https://www.ebi.ac.uk/ols/index">OLS</a> to normalize the
          attributes against popular Ontologies. This feature makes the
          data-steward a useful tool for IDSN in the context of semantic
          integration.
        </p>
      </div>
    </div>
  </div>
</template>


<script>
import M from "materialize-css";

export default {
  name: "welcome",
  created() {
    var elems = document.querySelectorAll(".parallax");
    M.Parallax.init(elems);
  },
  data() {
    return {
      version: process.env.VUE_APP_VERSION,
    };
  },
};
</script>
<style scoped>
.parallax-1 {
  /* The image used */
  background: url("../assets/logo_data_steward.png");
  background-size: 30%;

  /* Set a specific height */
  min-height: 33vh;

  /* Create the parallax scrolling effect */
  background-attachment: fixed;
  background-position: top 100px left 50%;

  background-repeat: no-repeat;
}
.parallax-2 {
  /* The image used */
  background: url("https://www.ebi.ac.uk/ols/img/OLS_logo_2017.png");
  background-size: 25%;

  /* Set a specific height */
  min-height: 25vh;

  /* Create the parallax scrolling effect */
  background-attachment: fixed;
  background-position: bottom 260px left 50%;
  background-repeat: no-repeat;
}
.footer-fixed {
  position: relative !important;
}
</style>