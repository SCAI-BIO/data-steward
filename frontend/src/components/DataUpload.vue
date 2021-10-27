<template>
  <div>
    <h1>Data Upload</h1>
    <div class="container center-align">
      <div class="row">
        
        <div class="input-field col s6">
        <p>Please select a source for your data!</p>
      <select class="browser-default" id="sourceSelect">
        <option v-for="src in sourceList" :key="src" :value="src">{{src}}</option>
      </select>
      </div>
      </div>
      <vue-dropzone
        ref="myVueDropzone"
        id="dropzone"
        :options="dropzoneOptions"
        @vdropzone-success="vsuccess"
        @vdropzone-error="verror"
        @vdropzone-file-added="addedFile"
        @vdropzone-sending="sendingEvent"
      ></vue-dropzone>
      <vue-ellipse-progress
        id="loader"
        class="hide"
        :progress="progress"
        v-bind="options"
      >
        <!--
        <span slot="legend-value" style="color : black" id="totalCount"></span>-->
        <p slot="legend-caption" id="feedback"></p>
      </vue-ellipse-progress>

      <p id="totalCount"></p>
      
      <p id="post_process_feedback"></p>
      <p id="totalOLS"></p>
      <div
        id="not_found"
        v-if="notFound.length > 0"
        class="container"
        style="margin-bottom: 80px"
      >
        <h5>Variables not automatically mapped (total: {{ this.notFound.length }}):</h5>
       
            <ul v-for="attr in notFound" :key="attr">
              <li>{{ attr }}</li>

             
            </ul>

        <a href="/data-steward/mapper">Go to mapping assistant</a>
     
        <!--
        <div class="row mt-3">
          <div class="col s1">
        <button class="btn blue-grey lighten-1" @click="refreshAttributes()">refresh targets</button>
          </div>
          <div class="col s11"></div>
        </div>-->
      </div>
    </div>

  </div>
</template>

<script>
import vue2Dropzone from "vue2-dropzone";
import "vue2-dropzone/dist/vue2Dropzone.min.css";
import { v4 as uuidv4 } from "uuid";
import M from "materialize-css";
import $ from "jquery";
import axios from "axios";

export default {
  components: {
    vueDropzone: vue2Dropzone,
  },
  data: function () {
    return {
      dropzoneOptions: {
        url: process.env.VUE_APP_CLINICALURL + "/post/basic-upload",
        thumbnailWidth: 150,
        addRemoveLinks: true,
        maxFiles: 1,
      },
      notFound: [],
      allAttributes: {},
      allSources: {},
      sourceList: [],
      id: uuidv4(),
      updateUrl: process.env.VUE_APP_CLINICALURL + "/get/cache",
      interval: 2000,
      progress: 0,
      options: {
        color: "#579fdc",
        "empty-color": "#324c7e",
        size: 300,
        thickness: 5,
        "empty-thickness": 3,
        "line-mode": "out 5",
        animation: "rs 700 1000",
        "font-size": "1.5rem",
        "font-color": "white",
      },
    };
  },
  async created() {
    const attributes = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attributes/all"
    );
    const sources_all = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/sources/all"
    );
    var sourceObj = {};
    var sourceList = [];
    sources_all["data"]["sources"].forEach((elem) => {
      sourceObj[elem] = null;
      
    });
    sources_all['data']["abbreviations"].forEach(elem =>{
      sourceList.push(elem);
    });
    this.allSources = sourceObj;
    this.sourceList = sourceList;
    var attrObj = {};
    attributes["data"]["attributes"].forEach((attr) => {
      attrObj[attr.name] = null;
    });
    this.allAttributes = attrObj;
  },

  mounted(){
    var elems = document.querySelectorAll('select');
    M.FormSelect.init(elems);
  },
  updated() {
    var elems = document.querySelectorAll(".autocomplete");

    M.Autocomplete.init(elems, { data: this.allAttributes });
    var elems_source = document.querySelectorAll(".autocomplete_source");

    M.Autocomplete.init(elems_source, {
      data: this.allSources,
      onAutocomplete: function (val) {
        var emptyFields = [];
        document.querySelectorAll(".autocomplete_source").forEach((elem) => {
          if (elem.value == null || elem.value == "") {
            emptyFields.push(elem);
          }
        });

        emptyFields.forEach((elem) => {
          elem.value = val;
        });
        M.updateTextFields();
      },
    });
  },

  methods: {


    refreshAttributes: async function(){
          const attributes = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attributes/all"
    );
    const sources_all = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/sources/all"
    );
    var sourceObj = {};
    sources_all["data"]["sources"].forEach((elem) => {
      sourceObj[elem] = null;
    });
    this.allSources = sourceObj;

    var attrObj = {};
    attributes["data"]["attributes"].forEach((attr) => {
      attrObj[attr.name] = null;
    });
    this.allAttributes = attrObj;
    M.toast({html: "Refreshed variable autocomplete..."});

    },
    addMapping: async function (attr) {
      var target = document.getElementById(attr + "_mapping_field").value;
      if (target == null || target == "") {
        M.toast({ html: "Please check your input!" });
        return;
      }

      var source = document.getElementById(attr + "_source_field").value;

      const mappingResponse = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/basic-mapping",
        data: {
          source: source,
          source_attribute: attr,
          target: target,
        },
        withCredentials: true,
      });
      if (mappingResponse.data["message"] == "ok") {
        this.notFound = this.notFound.filter((item) => item != attr);
        M.toast({ html: "You successfully mapped: " + attr });
      } else {
        document.getElementById(attr + "_feedback").innerText =
          mappingResponse.data["message"];
      }
      return;
    },
    addedFile: function () {
      document.getElementById("feedback").innerText =
        "Your data is getting processed";
    },
    setProgress: function (prog) {
      this.progress = prog;
      return;
    },

    check_status: function () {
      var self = this;
      $.ajax({
        type: "GET",
        url: self.updateUrl,
        data: { _id: self.id },
        success: function (e) {
          console.log(e);
          if (e.message != null && e["message"]["status"] == "done") {
            console.log("Done");
          }
        },
        complete: function (e) {
          if(e.responseJSON['message'] == null){
            setTimeout(self.check_status, self.interval);
          }
          var notFoundList = e.responseJSON["message"]["not_found"];

          if (e.responseJSON["message"]["status"] == "done") {
            self.progress = 100;
            //$("#loader").addClass("hide");
            $("#totalCount").hide();

            self.notFound = notFoundList;
            document.getElementById("feedback").innerText =
              e.responseJSON["message"]["message"];

            document.getElementById("post_process_feedback").innerText =
              e.responseJSON["message"]["message"];
            //document.getElementById('totalOLS').innerText = "Imported from OLS: "  + e.responseJSON['message']['ols_count'];
            $("#loader").hide();
            return;

            /**
             *
             * Add not found feed back
             */
          } else {
            self.notFound = notFoundList;
            document.getElementById("totalCount").innerText =
              "Processing " +
              e.responseJSON["message"]["total"] +
              " lines of data...";
            self.progress = e.responseJSON["message"]["done"];
            setTimeout(self.check_status, self.interval);
          }
        },
      });
    },
    vsuccess: function (file, response) {
      var text = "Successfully uploaded file " + file.name;
      M.toast({ html: text });

      document.getElementById("feedback").innerText = response["message"];
      document.getElementById("dropzone").classList.add("hide");
      document.getElementById("loader").classList.remove("hide");

      //var self = this;

      this.check_status();
    },
    verror: function (file) {
      var text = "Error while uploading " + file.name;
      M.toast({ html: text });
      document.getElementById("loader").classList.add("hide");
      document.getElementById("feedback").innerText =
        "Something went wrong... Please try again later";
    },

    sendingEvent(file, xhr, formData) {
      formData.append("_id", this.id);
      formData.append("_source", document.getElementById('sourceSelect').value);
    },
  },
};
</script>

<style>
.float_bottom_right {
  position: absolute;
  bottom: 30px;
  right: 30px;
}

.tap-target {
  color: #fff;
}
.tap-target a {
  color: #fff;
  text-decoration: underline;
}
</style>