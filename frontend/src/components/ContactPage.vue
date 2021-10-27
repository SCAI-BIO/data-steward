<template>
  <div class="container blue-grey lighten-5">
      <h1>
          Contact

      </h1>

      <p>The Data Steward Tool is developed and maintained by Fraunhofer SCAI.</p>
      <p>For questions or data privacy concerns please contact:</p>
      <br>
      <br>
      <ul>
          <li><img class="materialboxed" style="left: 50%; transform: translate(-50%)" data-caption="Philipp Wegner" width="200" src="../../picture-philipp.jpg">Philipp Wegner: <a href="mailto:philipp.wegner@scai.fraunhofer.de">philipp.wegner@scai.fraunhofer.de</a></li>
          <li><img class="materialboxed"  style="left: 50%; transform: translate(-50%)" data-caption="Alpha Tom Kodamullil" width="250" src="https://scai.fraunhofer.de/en/business-research-areas/bioinformatics/fields-of-research/Applied-Semantics/team/jcr:content/contentPar/teaser_overview/teaserPar/teaser_1113960851/image.img.2col.large.jpg/1618558246164/Alpha-Tom-Kodamullil.jpg">Alpha Tom Kodamullil: <a href="mailto:alpha.tom.kodamullil@scai.fraunhofer.de">alpha.tom.kodamullil@scai.fraunhofer.de></a></li>
      </ul>
      <br>
      <br>
      
  </div>
</template>

<script>
import M from 'materialize-css';
export default {
    test: function(){
        var elems = document.querySelectorAll('.materialboxed');
        M.Materialbox.init(elems);
        
            
      
           
    
   

    }
 
    }


</script>

<style>

</style>