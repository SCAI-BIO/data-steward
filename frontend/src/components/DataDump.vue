<template>
  <div class="container">
    <h5>
      Upload Semantic Asset
      <i
        class="material-icons tooltipped"
        data-position="bottom"
        data-tooltip="A Semantic Asset can be any variable that you are using or planning to use. Uploading your variables here help to higher the coverage of the Common Datamodel!"
        >info</i
      >
    </h5>
    <br />
    <p id="error"></p>
     <div class="progress" style="display: none; width: 40vw; margin: auto">
      <div class="indeterminate"></div>
  </div>
    <p id="success"></p>
    <br />
    <div class="row">
      <form id="data_dump">
        <div class="row">
          <div class="input-field col s6">
            <input
              type="text"
              name="label"
              id="input_label"
              placeholder="A unique name for the variable"
              required
            />
            <label for="label">Variable Name</label>
            <div id="label-error"></div>
          </div>
          <div class="input-field col s6">
            <input
              type="text"
              name="provenance"
              id="input_provenance"
              placeholder="Optionally add adescription"
            />
            <label for="provenance">Provenance (optional)</label>
          </div>
        </div>
        <div class="row">
          <div class="col s12">
            <label for="textarea1">Description</label>
            <textarea
              id="textarea1"
              name="description"
              class="materialize-textarea"
              required
            ></textarea>

            <span class="helper-text" data-error="wrong" data-success="right"
              >Make your desciption as common as possible because this is later
              used to map your variable to the Common Datamodel.</span
            >
          </div>
        </div>

        <button
          class="btn waves-effect waves-light right"
          type="submit"
          name="action"
          id="submit"
        >
          Upload
          <i class="material-icons right">send</i>
        </button>
      </form>
    </div>
  </div>
</template>
<script>
import M from "materialize-css";
import ax from "axios";
const axios = ax;

export default {
  name: "DataDump",
  data() {
    return {
      assets: [],
    };
  },
  async mounted() {
     const assets = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/semantic-assets-all"
    );
    this.assets = assets["data"]["assets"];
    var this_assets = this.assets;
    document.getElementById("data_dump").onsubmit = async function (e) {
      document.getElementsByClassName('progress')[0].style.display = 'block';
      e.preventDefault();
      console.log("POST....");
      var formData = new FormData(this);
      const uploadResponse = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/semantic-asset",
        data: formData,
      });
      console.log(uploadResponse);
      if (!uploadResponse["data"]["message"] == "ok") {
        document.getElementById("error").innerHTML =
          uploadResponse["data"]["message"];
        document.getElementById("error").style.display = "block";
      } else {
        this.reset();
        // document.getElementById("error").innerHTML = "";
        // document.getElementById("success").innerHTML =
        //   "Successfully uploaded a semantic asset.";
        // document.getElementById("success").style.display = "block";
        M.updateTextFields();
        const assets = await axios.get(
          process.env.VUE_APP_CLINICALURL + "/get/semantic-assets-all"
        );
        this_assets = assets["data"]["assets"];

          M.toast({html: 'Successfully contributed a Semantic Asset! Thank you!'});
           document.getElementsByClassName('progress')[0].style.display = "none";
      }
    };

   
    document.getElementById("input_label").onchange = function () {
      if (this_assets.some((e) => e == this.value)) {
        document.getElementById("label-error").innerHTML =
          "This variable name already exists!";
        document.getElementById("submit").disabled = true;
      } else {
        document.getElementById("label-error").innerHTML = "";
        document.getElementById("submit").disabled = false;
      }
    };
  },
};
</script>

<style scoped>
#label-error {
  color: red;

}
#error {
  color: red;
    
  padding: 15px;
  background-color: lightgray;
  width: 20vw;
  margin: auto;
  display: none;
}
#success {
  color: green;
  padding: 15px;
  background-color: lightgray;
  width: 20vw;
  margin: auto;
  display: none;
}
.tooltipped:hover {
  cursor: help;
}
</style>