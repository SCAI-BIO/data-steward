<template>
  <div class="container pt-10">
    <h3 class="mb-30">Datamodel Mappings</h3>
    <button v-on:click="downloadCSV">Download as .csv</button>

    <datatable
      title="Variable Mappings"
      :columns="columns"
      :rows="rows"
    />
  </div>
</template>

<script>
import ax from "axios";

const axios = ax;
import DataTable from "vue-materialize-datatable";
export default {
  components: {
    datatable: DataTable,
  },
  data() {
    return {
      columns: [
        { label: "Source", field: "source" },
        { label: "External Variable", field: "extVar" },
        { label: "Internal Variable", field: "intVar" },
        { label: "Desciption (Internal Variable)", field: "intVarDesc" },
        { label: "Transformation", field: "trans" },
      ],
      rows: [],
    }
  },
  methods: {
    downloadCSV: function(){
    var header = [];
    this.columns.forEach(col =>{
      header.push(col.label);
    });
    var csvContent = "data:text/tsv;charset=utf-8," + header.join("\t") + "\n"
    + this.rows.map(e => Object.values(e).join("\t")).join("\n");

    console.log(header);
    console.log(csvContent);

    var encodedUri = encodeURI(csvContent);
    window.open(encodedUri);

  }},
  created() {
    axios
      .get(process.env.VUE_APP_CLINICALURL + "/get/attribute-mappings/all")
      .then((response) => {
        const mappings = response.data["mappings"];
        [...mappings].forEach((mapping) => {
          this.rows.push({
            source: mapping.Source,
            extVar: mapping.name,
            intVar: mapping.Target,
            intVarDesc: mapping.TargetDescription,
            trans: mapping.Transformation,
          });
        });
      });
  },
};
</script>

<style>
</style>