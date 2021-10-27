<template>
  <div class="container">
    <div class="row">
      <h5 class="center-align">Model Statistics</h5>
    </div>
    <div class="row">
      <div>
        <Plotly
          :data="data"
          :layout="layout"
          :display-mode-bar="false"
        ></Plotly>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { Plotly } from "vue-plotly";
export default {
  components: {
    Plotly,
  },
  data() {
    return {
      data: [{
        x: [],
        y: [],
        type: "bar",
        text:"",
         textposition: 'auto',
        hoverinfo: 'none',
      }],
      layout: { title: "Data model Statistics",
      yaxis:{
        title: "Variables mapped"
      },
      xaxis:{
        title: "Sources"
        }
   },
    };
  },
  async created() {
    const response = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attr-by-source"
    );
    var data = response.data["attr_by_src"];
    Object.keys(data).forEach((src) => {
      this.data[0].x.push(src);
      this.data[0].y.push(data[src]);
    });
    this.data[0].text =  this.data[0].y.map(String);
  },
};
</script>

<style>
</style>
