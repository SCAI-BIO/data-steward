<template>
  <div><!--
    <div class="container" id="main_container">
      
      <div class="row">
        <h1>Datamodel Download</h1>
        <button class="btn blue-grey lighten-1" id="download_btn">
          Download Datamodel as .xlsx
        </button>
      </div>
      <div class="row">
        <h1>OWL Download</h1>
        <button class="btn blue-grey lighten-1" id="download_btn_owl">
          Download CCDM Ontology
        </button>
      </div>
    </div>
    <div class="loading center-align">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
    <h5 id="helper_text"></h5>
    -->
  </div>
</template>
<script>
import ax from "axios";
const axios = ax;
export default {
  name: "download",
  mounted() {
    function downloadFile(data, filename, mime) {
      // It is necessary to create a new blob object with mime-type explicitly set
      // otherwise only Chrome works like it should
      const blob = new Blob([data], {
        type: mime || "application/rdf+xml",
      });
      if (typeof window.navigator.msSaveBlob !== "undefined") {
        // IE doesn't allow using a blob object directly as link href.
        // Workaround for "HTML7007: One or more blob URLs were
        // revoked by closing the blob for which they were created.
        // These URLs will no longer resolve as the data backing
        // the URL has been freed."
        window.navigator.msSaveBlob(blob, filename);
        return;
      }
      // Other browsers
      // Create a link pointing to the ObjectURL containing the blob
      const blobURL = window.URL.createObjectURL(blob);
      const tempLink = document.createElement("a");
      tempLink.style.display = "none";
      tempLink.href = blobURL;
      tempLink.setAttribute("download", filename);
      // Safari thinks _blank anchor are pop ups. We only want to set _blank
      // target if the browser does not support the HTML5 download attribute.
      // This allows you to download files in desktop safari if pop up blocking
      // is enabled.
      if (typeof tempLink.download === "undefined") {
        tempLink.setAttribute("target", "_blank");
      }
      document.body.appendChild(tempLink);
      tempLink.click();
      document.body.removeChild(tempLink);
      setTimeout(() => {
        // For Firefox it is necessary to delay revoking the ObjectURL
        window.URL.revokeObjectURL(blobURL);
      }, 100);
    }
    document.getElementById("download_btn").onclick = function () {
      window.location = process.env.VUE_APP_CLINICALURL + "/get/datamodel-file";
    };
    document.getElementById("download_btn_owl").onclick = async function () {
      document.getElementById("main_container").style.display = "none";
      document.getElementsByClassName("loading")[0].style.display =
        "inline-flex";
      document.getElementById("helper_text").innerHTML =
        "Your OWL Ontology is getting assembled...";
      const fileResponse = await axios.get(
        process.env.VUE_APP_CLINICALURL + "/get/owl"
      );
      //var f = new Blob([fileResponse.data]);
      //console.log(f);
      document.getElementsByClassName("loading")[0].style.display = "none";
      document.getElementById("helper_text").innerHTML =
        "CCDM is ready to download!";
      downloadFile(fileResponse.data, "CCDM.owl");
    };
  },
};
</script>
<style scoped>
.loading {
  margin-top: 33vh;
  display: none;
}
.loading .dot {
  position: relative;
  width: 2em;
  height: 2em;
  margin: 0.8em;
  border-radius: 50%;
}
.loading .dot::before {
  position: absolute;
  content: "";
  width: 100%;
  height: 100%;
  background: inherit;
  border-radius: inherit;
  animation: wave 2s ease-out infinite;
}
.loading .dot:nth-child(1) {
  background: #c3a3d6;
}
.loading .dot:nth-child(1)::before {
  left: 0;
  animation-delay: 0.2s;
}
.loading .dot:nth-child(2) {
  background: #b48dcc;
}
.loading .dot:nth-child(2)::before {
  left: 0;
  animation-delay: 0.4s;
}
.loading .dot:nth-child(3) {
  background: #965fb8;
}
.loading .dot:nth-child(3)::before {
  left: 0;
  animation-delay: 0.6s;
}
.loading .dot:nth-child(4) {
  background: #8748ae;
}
.loading .dot:nth-child(4)::before {
  left: 0;
  animation-delay: 0.8s;
}
.loading .dot:nth-child(5) {
  background: #6a1b9a;
}
.loading .dot:nth-child(5)::before {
  left: 0;
  animation-delay: 1s;
}

@keyframes wave {
  50%,
  75% {
    transform: scale(2.5);
  }
  80%,
  100% {
    opacity: 0;
  }
}
</style>