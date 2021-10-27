<template>
  <div>
    <div class="container">
      <h3>Upload a CCDM Ontology</h3>
      <div class="row">
        <form id="owl_form">
          <div
            id="drop-zone"
            class="drop-div"
            v-on:dragover="ondragover"
            v-on:dragenter="ondragover"
            v-on:drop="dragdrop"
            v-on:click="dropZoneClick"
          >
            <p id="drop-text">Drag and drop your owl file.</p>
            <i class="large material-icons" v-if="dropped">attach_file</i>
            <p id="file_info"></p>
          </div>

          <input
            type="file"
            id="file_input"
            style="display: none"
            v-on:change="dragdrop"
          />
          <button
            class="btn waves-effect waves-light right blue-grey lighten-1"
            id="upload-btn"
            type="submit"
            name="action"
            v-if="dropped"
          >
            Upload
            <i class="material-icons right">send</i>
          </button>
          <button
            class="btn waves-effect waves-light left blue-grey lighten-1"
            id="upload-btn-reset"
            type="button"
            v-on:click="reset"
            v-if="dropped"
          >
            Reset
            <i class="material-icons right">send</i>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
import ax from "axios";
const axios = ax;
export default {
  name: "OWLUpload",
  data() {
    return {
      dropped: false,
    };
  },

  methods: {
    reset: function (e) {
      e.preventDefault();
      document.getElementById("owl_form").reset();
      document.getElementById("file_info").innerText = "";
      this.dropped = false;
    },
    ondragover: function (e) {
      e.preventDefault();
    },
    dragdrop: function (e) {
      var fileInput = document.getElementById("file_input");
      if (fileInput.files === undefined || fileInput.files.length == 0) {
        fileInput.files = e.dataTransfer.files;

        // If you want to use some of the dropped files
        const dT = new DataTransfer();
        dT.items.add(e.dataTransfer.files[0]);
        fileInput.files = dT.files;
      }

      e.preventDefault();
      document.getElementById("file_info").innerText = fileInput.files[0].name;

      this.dropped = true;
    },
    dropZoneClick: function (e) {
      e.preventDefault();
      document.getElementById("file_input").click();
    },
  },
  created() {
    document.getElementById("owl_form").onsubmit = async function (e) {
      e.preventDefault();
      var formData = new FormData();

      var fileInput = document.getElementById("file_input").files[0];
      formData.append("file", fileInput);
      const uploadResponse = await axios.post(
        process.env.VUE_APP_CLINICALURL + "/post/owl",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      console.log(uploadResponse);
    };
  },
};
</script>
<style scoped>
upload-btn {
  margin: 15px !important;
}
h5,
p {
  color: #2c3e50;
}
.drop-div {
  width: 100%;
  border-style: dashed;
  height: 30vh;
  margin: auto;
  color: rgba(0, 0, 0, 0.3);
}
.drop-div:hover {
  box-shadow: 0 0 6px rgba(35, 173, 278, 1);
}
</style>