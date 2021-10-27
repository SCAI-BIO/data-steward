<template>
  <div class="container pt-10" id="main_container">
    <div id="global-loader" class="global-loader">
      <div class="loader-elem">
        <atomspinner :size="80" color="#5AA8EA" />
        <p id="loader-text">updating...</p>
      </div>
    </div>
    <div id="errorMessageTop" style="display: none">
      <div class="materialert error">
        <i class="material-icons">report_problem</i>
        <span id="errorText"></span>
        <button type="button" class="close-alert" @click="closeError()">
          ×
        </button>
      </div>
    </div>
    <h2 class="mb-30">
      Mapping Assistant
      <a class="tooltipped" data-position="bottom" :data-tooltip="helpText"
        ><i class="material-icons">help_outline</i></a
      >
    </h2>

    <div class="row">
      <div class="col" v-if="checkForSingleSource()">
        <button
          class="btn waves-effect waves-light blue-grey lighten-1"
          @click="fillSources()"
        >
          Fill sources
        </button>
      </div>
      <div class="col">
        <p>
          <label>
            <input
              type="checkbox"
              class="filled-in"
              id="suggestion_checkbox"
              @change="alterSuggestions()"
            />
            <span>Make suggestions</span>
          </label>
        </p>
      </div>
      <div class="col">
        <p>
          <label>
            <input type="checkbox" class="filled-in" @change="alterOLS()" />
            <span>Include OLS</span>
          </label>
        </p>
      </div>
      <div v-if="makeSuggestion == true" class="col">
        <span class="badge blue" style="color: white">matched &#62; 80%</span>
        <span class="badge orange" style="color: white">matched &#60; 80%</span>
      </div>

      <!-- 

            Modal for editing the row
        -->

      <div id="modal1" class="modal">
        <div class="modal-content">
          <h4>Edit mapping for {{ modal.extVar }}</h4>

          <div class="row">
            <div class="input-field col s6">
              <label for="sourceModal">Source</label>
              <input
                class="autocomplete_source"
                type="text"
                id="sourceModal"
                :value="modal.source"
                @change="alterSource()"
              />
            </div>
            <div class="input-field col s6">
              <label for="sourceModal">External Variable</label>
              <input
                type="text"
                id="extVarModal"
                :value="modal.extVar"
                readonly
              />
            </div>
          </div>
          <div v-if="includeOLS == true" class="row">
            <div class="input-field col s6">
              <label for="sourceModal">Internal Variable</label>
              <input
                class="autocomplete"
                type="text"
                id="intVarModal"
                :value="modal.intVar"
                @change="alterIntVar()"
              />
            </div>
            <div class="input-field col s6">
              <label for="sourceModal">OLS Variable</label>

              <input
                @input="addOLStoAutocomplete()"
                class="ols_autocomplete"
                type="text"
                id="olsVarModal"
                :value="modal.olsVar"
                @change="alterOLSVar()"
              />
            </div>
          </div>
          <div v-else class="row">
            <div class="input-field col s10">
              <label for="sourceModal">Internal Variable</label>
              <input
                class="autocomplete"
                type="text"
                id="intVarModal"
                :value="modal.intVar"
                @change="alterIntVar()"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <a class="modal-close waves-effect waves-green btn-flat" href="#!">
            Ok
          </a>
        </div>
      </div>
    </div>

    <datatable
      title="Add mappings (Click on rows to edit)"
      :columns="columns"
      :rows="rows"
      v-on:row-click="onRowClick"
    >
      <th slot="thead-tr">Actions</th>
      <template slot="tbody-tr" scope="props">
        <td>
          <button
            class="btn waves-effect waves-light blue-grey lighten-1"
            @click="(e) => submitMapping(props.row, e)"
          >
            Edit mappings<i class="material-icons white-text">send</i>
          </button>
        </td>
      </template>
    </datatable>
  </div>
</template>

<script>
import { AtomSpinner } from "epic-spinners";
import axios from "axios";
import DataTable from "vue-materialize-datatable";
import M from "materialize-css";

export default {
  components: {
    datatable: DataTable,
    atomspinner: AtomSpinner,
  },
  data: function () {
    return {
      openModalTS: "",
      helpText:
        "This assistant provides help for mapping variaables. The list below provides all variables in the dataset uploaded, that yould not be found in the current system or there was no suitable mapping onto a variable currently in the system. The assistant provides a suggestion system and backup support from OLS (Ontology Lookup System). Enable the two checkboxes below to activate these features. Try and prefferedly choose those variables that are already in the system and if nothing fits your data import one from OLS. If there is not suitable variable in OLS then you can go to the Model Wizard and add a variable by hand.",
      attrObj: {},
      olsAutocomplete: {},
      sourceObj: {},
      has_suggestion: [],
      modal: {
        extVar: "",
        intVar: "",
        source: "",
        olsVar: "",
      },
      hasSuggestionOls: [],

      makeSuggestion: false,
      includeOLS: false,
      columns: [
        { label: "Source", field: "source" },
        { label: "External Variable", field: "extVar" },
        { label: "Internal Variable", field: "intVar", html: true },
      ],
      rows: [],
    };
  },
  async created() {
    const response = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/all-attr-unmapped"
    );
    for (var i = 0; i < response.data["datapoints"].length; i++) {
      this.rows.push({
        source: "",
        extVar: response.data["datapoints"][i],
        intVar: "",
        olsVar: "",
      });
    }
    await this.loadAttrAndSourceFromBackend();
  },

  mounted: function () {
    document.addEventListener("DOMContentLoaded", function () {
      var elems = document.querySelectorAll(".modal");
      M.Modal.init(elems);
      M.Tooltip.init(document.querySelectorAll(".tooltipped"));
    });
    if (window.innerWidth <= 1300) {
      document.getElementById("main_container").classList.remove("container");
      document.getElementById("main_container").classList.add("px-4");
    } else {
      document.getElementById("main_container").classList.add("container");
      document.getElementById("main_container").classList.remove("px-4");
    }
    window.onresize = function () {
      if (window.innerWidth <= 1300) {
        document.getElementById("main_container").classList.remove("container");
        document.getElementById("main_container").classList.add("px-4");
      } else {
        document.getElementById("main_container").classList.add("container");
        document.getElementById("main_container").classList.remove("px-4");
      }
    };
  },

  updated: function () {
    // autocomplete
    console.debug("Loading autocomplete...");
    var elems = document.querySelectorAll(".autocomplete");

    M.Autocomplete.init(elems, { data: this.attrObj });

    var elems_source = document.querySelectorAll(".autocomplete_source");
    M.Autocomplete.init(elems_source, { data: this.sourceObj });

    var elems_ols = document.querySelector(".ols_autocomplete");
    M.Autocomplete.init(elems_ols, { data: this.olsAutocomplete });
  },

  methods: {
    checkForSingleSource: function () {
      function onlyUnique(value, index, self) {
        return self.indexOf(value) === index;
      }
      var sources = [];
      this.rows.forEach((row) => {
        sources.push(row.source);
      });
      sources = sources.filter((src) => src != "");
      var filteredSources = sources.filter(onlyUnique);

      return filteredSources.length == 1;
    },
    fillSources: function () {
      console.debug("filling sources...");
      document.getElementById("global-loader").style.display = "block";
      if (this.checkForSingleSource()) {
        var src = this.rows.filter((row) => row.source != "")[0].source;
        this.rows.forEach((row) => (row.source = src));
        M.toast({ html: `Successfully filled sources with ${src}` });
        document.getElementById("global-loader").style.display = "none";
      } else {
        console.debug("Sources not unique");
        document.getElementById("global-loader").style.display = "none";
        return;
      }
    },
    checkValid: (literal) => {
      if (literal == null) {
        return false;
      }
      if (literal == "") {
        return false;
      }
      return true;
    },
    alterIntVar: function () {
      var row = this.rows.find((elem) => elem.extVar == this.modal.extVar);
      row.intVar = document.getElementById("intVarModal").value;
      this.modal.intVar = document.getElementById("intVarModal").value;
      return;
    },
    alterOLSVar: function () {
      var row = this.rows.find((elem) => elem.extVar == this.modal.extVar);
      row.olsVar = document.getElementById("olsVarModal").value;
      this.modal.olsVar = document.getElementById("olsVarModal").value;
      return;
    },
    alterSource: function () {
      var row = this.rows.find((elem) => elem.extVar == this.modal.extVar);
      row.source = document.getElementById("sourceModal").value;
      this.modal.source = document.getElementById("sourceModal").value;
      return;
    },
    alterTrans: function () {
      var row = this.rows.find((elem) => elem.extVar == this.modal.extVar);
      row.trans = document.getElementById("transModal").value;
      return;
    },
    extractContent: function(s) {
  var span = document.createElement('span');
  span.innerHTML = s;
  return span.textContent || span.innerText;
},

    submitMapping: async function (props, e) {
      this.openModalTS = new Date().getTime();

    

      e.preventDefault(); // does not prevent modal from opening...
      var extVar = props.extVar;
      var intVar = this.extractContent(props.intVar);
      console.log(intVar);
      var src = props.source;
      var olsVar = props.olsVar;

      //console.log(extVar,intVar, src);
      /*var trans = props.trans;*/
      if (
        (this.checkValid(extVar) &&
          this.checkValid(intVar) &&
          this.checkValid(src) &&
          !this.checkValid(olsVar)) ||
        (this.checkValid(extVar) &&
          !this.checkValid(intVar) &&
          this.checkValid(src) &&
          this.checkValid(olsVar))
        /* this.checkValid(trans) this is maybe optional */
      ) {
        // mapping
        if (this.checkValid(olsVar)) {
          intVar = olsVar;
        }
        const mappingResponse = await axios({
          method: "post",
          url: process.env.VUE_APP_CLINICALURL + "/post/basic-mapping",
          data: {
            source: src,
            source_attribute: extVar,
            target: intVar,
          },
          withCredentials: true,
        });
        //console.log(mappingResponse);
        if (mappingResponse.data["message"] == "ok") {
          this.rows = this.rows.filter((elem) => elem.extVar != extVar); // remove the row from the table
          M.toast({ html: "You successfully mapped: " + extVar });
          if (intVar.split("|").length > 2) {
            M.toast({
              html:
                "You successfully added term from OLS: " + extVar.split("|")[0],
            });
          }
        } else {
          document.getElementById("errorMessageTop").style.display = "block";
          document.getElementById("errorText").innerText =
            mappingResponse.data["message"];
        }
      } else {
        M.toast({ html: "Please check your input" });
        return;
      }
    },

    closeError: function () {
      document.getElementById("errorMessageTop").style.display = "none";
    },
    onRowClick: async function (row) {
      var ts = new Date().getTime();
      if (ts - this.openModalTS < 1000) {
        // prevent row click when submit is intended @future_philipp : feel free to implement better !
        return;
      }
      function extractContent(s) {
        var span = document.createElement("span");
        span.innerHTML = s;
        return span.textContent || span.innerText;
      }

      // setting data to render it into the model body
      this.modal.extVar = row.extVar;
      this.modal.intVar = extractContent(row.intVar);
      this.modal.source = row.source;
      this.modal.olsVar = row.olsVar;

      this.olsAutocomplete = {};
      // open modal
      var elem = document.querySelectorAll(".modal")[0];
      var instance = M.Modal.getInstance(elem);
      await instance.open();
      M.updateTextFields();
    },

    addSuggestions: async function () {
      for (var i = 0; i < this.rows.length; i++) {
        if (this.rows[i].intVar === "") {
          const response = await axios.get(
            process.env.VUE_APP_CLINICALURL +
              "/get/nearest-neighbor?attribute=" +
              this.rows[i].extVar +
              "&ols=" +
              this.includeOLS
          );
          if (response.data["candidate"] != "--no-candidate--") {
            if (response.data["candidate"].split("|").length > 2) {
              // OLS VAR
              this.rows[i].olsVar = response.data["candidate"];

              this.hasSuggestionOls.push(this.rows[i].olsVar);
            } else {
              // Var from backend

              if (response.data["distance"] >= 0.8) {
                this.rows[i].intVar =
                  "<span class='badge blue' style='color: white'>" +
                  response.data["candidate"] +
                  "</span>";
                //this.rows[i].suggestionDistance =  "<span class='badge blue'> </span>";
              } else {
                this.rows[i].intVar =
                  "<span class='badge orange' style='color: white'>" +
                  response.data["candidate"] +
                  "</span>";
                //this.rows[i].suggestionDistance = "<span class='badge orange'> </span>";
              }
              this.has_suggestion.push(this.rows[i].extVar);
            }
          }
        }
      }
    },
    removeSuggestions: function () {
      this.rows
        .filter((row) => this.has_suggestion.includes(row.extVar))
        .forEach((row) => {
          row.intVar = "";
        });
      this.has_suggestion = [];
      this.rows
        .filter((row) => this.hasSuggestionOls.includes(row.olsVar))
        .forEach((row) => {
          row.olsVar = "";
        });
      this.hasSuggestionOls = [];
    },
    alterSuggestions: async function () {
      document.getElementById("global-loader").style.display = "block";
      if (this.makeSuggestion) {
        this.makeSuggestion = false;
        // this.columns.splice(
        //   this.columns.indexOf({
        //     label: "Suggestion",
        //     field: "suggestionDistance",
        //   }),
        //   1
        // );
        this.removeSuggestions();
        M.toast({ html: "Suggestions disabled" });
      } else {
        this.makeSuggestion = true;
        //this.columns.push({ label: "Suggestion", field: "suggestionDistance" , html: true});
        M.toast({ html: "Searching for suggestions..." });
        await this.addSuggestions();
        M.toast({ html: "Suggestions added to table!" });
      }
      document.getElementById("global-loader").style.display = "none";
    },
    alterOLS: async function () {
      document.getElementById("global-loader").style.display = "block";
      if (this.includeOLS) {
        //await this.removeOLSfromAutocomplete();
        this.columns.splice(
          this.columns.indexOf({ label: "OLS Variable", field: "olsVar" }),
          1
        );

        this.rows
          .filter((row) => this.hasSuggestionOls.includes(row.olsVar))
          .forEach((row) => {
            row.olsVar = "";
          });
        this.hasSuggestionOls = [];
        this.includeOLS = false;
        M.toast({ html: "OLS search disabled" });
      } else {
        //await this.addOLStoAutocomplete();
        this.columns.push({ label: "OLS Variable", field: "olsVar" });
        this.includeOLS = true;
        if (this.makeSuggestion) {
          await this.addSuggestions();
        }
        M.toast({ html: "OLS search enabled" });
      }
      document.getElementById("global-loader").style.display = "none";
    },
    addOLStoAutocomplete: async function () {
      /**
       * 
       Use this in case CORS fails
     var headers = {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json',
    }
    */
      var inputElem = document.getElementById("olsVarModal");
      var term = inputElem.value;

      var addToAutocomplete = {};

      const olsResponse = await axios.get(
        process.env.VUE_APP_OLSURL + `api/select?q=${term}&rows=10`
      );
      var responseObj = olsResponse.data.response.docs;
      for (var k = 0; k < responseObj.length; k++) {
        if (
          this.rows.filter((row) => {
            row.intVar === responseObj[k]["label"];
          }).length == 0
        ) {
          // make sure that this is not already in the backend
          addToAutocomplete[
            responseObj[k]["label"] +
              "|" +
              responseObj[k]["ontology_name"] +
              "|" +
              responseObj[k]["iri"]
          ] = null;
        }
      }
      // add the results to autocomplete
      this.olsAutocomplete = addToAutocomplete;
      var instance = M.Autocomplete.getInstance(
        document.getElementById("olsVarModal")
      );
      instance.updateData(addToAutocomplete);
    },

    loadAttrAndSourceFromBackend: async function () {
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

      var attrObj = {};
      attributes["data"]["attributes"].forEach((attr) => {
        attrObj[attr.name] = null;
      });
      this.attrObj = attrObj;
      this.sourceObj = sourceObj;
    },
    removeOLSfromAutocomplete: async function () {
      await this.loadAttrAndSourceFromBackend();
    },
  },
};
</script>

<style>

.waves-light{
  z-index: 0 !important;

}
.global-loader {
  position: absolute;
  display: none;
  top: 0;
  left: 0;
  z-index: 9999;
  width: 100vw;
  height: 100vh;
  background-color: rgba(220, 220, 220, 0.5);
}
.loader-elem {
  position: absolute;
  top: 45%;
  left: 50%;
  transform: translateX(-50%);
}
.materialert {
  position: relative;
  min-width: 150px;
  padding: 15px;
  margin-bottom: 20px;
  margin-top: 15px;
  border: 1px solid transparent;
  border-radius: 4px;
  transition: all 0.1s linear;
  webkit-box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
    0 3px 1px -2px rgba(0, 0, 0, 0.12), 0 1px 5px 0 rgba(0, 0, 0, 0.2);
  box-shadow: 0 2px 2px 0 rgba(0, 0, 0, 0.14),
    0 3px 1px -2px rgba(0, 0, 0, 0.12), 0 1px 5px 0 rgba(0, 0, 0, 0.2);
  display: -webkit-box;
  display: -webkit-flex;
  display: -ms-flexbox;
  display: flex;
  -webkit-box-align: center;
  -webkit-align-items: center;
  -ms-flex-align: center;
  align-items: center;
}
.materialert .material-icons {
  margin-right: 10px;
}
.materialert .close-alert {
  -webkit-appearance: none;
  border: 0;
  cursor: pointer;
  color: inherit;
  background: 0 0;
  font-size: 22px;
  line-height: 1;
  font-weight: bold;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.7);
  filter: alpha(opacity=40);
  margin-bottom: -5px;
  position: absolute;
  top: 16px;
  right: 5px;
}
.materialert.info {
  background-color: #039be5;
  color: #fff;
}
.materialert.success {
  background-color: #43a047;
  color: #fff;
}
.materialert.error {
  background-color: #c62828;
  color: #fff;
}
.materialert.danger {
  background-color: #c62828;
  color: #fff;
}
.materialert.warning {
  background-color: #fbc02d;
  color: #fff;
}
</style>