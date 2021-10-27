<template>
  <div class="container">
    <div id="header_datapoints">
      <h1>Datapoints upload</h1>
      <p>
        Import EAV++-formatted data into database according to datamodel
        definitions and mappings.
      </p>
    </div>
    <div class="hide" id="loader">
      <p>Your data is getting processed...</p>
      <p>This may take some time...</p>
      <br />

      <div class="progress" id="process_bar">
       <div class="determinate" style="width: 0%"></div>
      </div>
    </div>
    <div id="after-logs" class="hide">
      <p id="results"></p>
      <ul class="collapsible">
        <li>
          <div class="collapsible-header">Process Logs (click to expand)</div>
          <div class="collapsible-body"><p id="process-log"></p></div>
        </li>
      </ul>
      <div class="row">
        <div class="col s12 right-align">
          <a class="waves-effect waves-light btn" href="/react-viewer"
            >Analyse your data</a
          >
        </div>
      </div>
    </div>

    <form id="datapoints_form">
      <div class="row">
        <div class="input-field col s12">
          <select
            name="source_origin"
            id="source_select"
            class="browser-default"
          >
            <option value="" disabled selected>
              Select the origin of your data (required for using respective
              mapping):
            </option>

            <option
              v-for="source in sources"
              :key="source.name"
              :value="source.name"
            >
              {{ source.name }}
            </option>
          </select>
          <label></label>
        </div>
      </div>
      <div class="row">
        <div class="input-field col s12">
          <select name="error_mode">
            <option value disabled selected>
              Determine strategy on how to treat data not perfectly matching
              datamodel definitions:
            </option>

            <option value="strict">Accept perfect data only</option>

            <option value="propose">
              Propose corrections, but skip imperfect data
            </option>

            <option value="sanitize">Auto-sanitize data where possible</option>
          </select>

          <label></label>
        </div>
      </div>
      <div class="row">
        <div class="input-field col s12">
          <select name="write_mode">
            <option value disabled selected>
              Determine strategy for existing attributes of an entity (ID +
              date):
            </option>

            <option value="sweep">
              Drop complete data before loading file
            </option>

            <option value="unique">Leave existing entries untouched</option>

            <option value="update">Modify existing entries</option>

            <option value="add">Accept duplicate entries</option>
          </select>
          <label></label>
        </div>
      </div>
      <div class="row">
        <div class="input-field col s3">
          <input
            name="min_date"
            id="id_min_date"
            type="text"
            class="validate"
            value="1875-01-01"
          />
          <label for="id_min_date">Earliest valid date:</label>
          <span class="helper-text left-align"
            >Earlier date entries will be regarded as invalid</span
          >
        </div>
        <div class="input-field col s3">
          <input
            name="max_date"
            id="id_max_date"
            type="text"
            class="validate"
            value=""
          />
          <label for="id_max_date">Latest valid date:</label>
          <span class="helper-text left-align"
            >Latest date entries will be regarded as invalid</span
          >
        </div>
        <div class="input-field col s6">
          <input
            name="delim"
            id="id_delim"
            type="text"
            class="validate"
            value=";"
          />
          <label for="id_delim">Field delimiter symbol:</label>
          <span class="helper-text left-align"
            >Delimiters within quotes are ignored.</span
          >
        </div>
      </div>
      <div class="row">
        <div class="input-field col s6">
          <p class="left-align">Use explicitly mapped variables only:</p>
          <div class="switch left-align">
            <label>
              No
              <input type="checkbox" name="mapping_only" />
              <span class="lever"></span>
              Yes
            </label>
          </div>
        </div>
        <div class="input-field col s6">
          <div class="file-field input-field">
            <div class="btn blue-grey lighten-1">
              <span>File</span>
              <input type="file" name="data_file" />
            </div>
            <div class="file-path-wrapper">
              <input
                class="file-path validate"
                type="text"
                placeholder="Data file (EAV++ format):"
              />
            </div>
          </div>
        </div>
      </div>
      <input name="_id" id="_id_input" style="display: none" />

      <div class="row" id="btn_row">
        <div class="col s12 right-align">
          <button
            class="btn waves-effect waves-light blue-grey lighten-1"
            name="action"
            id="form_btn"
          >
            Submit
            <i class="material-icons right">send</i>
          </button>
        </div>
      </div>
    </form>
  </div>
</template>

<script>
import ax from "axios";

import $ from "jquery";

import M from "materialize-css";

const axios = ax;

export default {
  name: "datapointsform",
  data() {
    return {
      sock_id: null,
      sources: [],
    };
  },
  created() {
    axios
      .get(process.env.VUE_APP_CLINICALURL + "/get/sources/all", {
        withCredentials: true,
      })
      .then((response) => {
        response["data"]["sources"].forEach((element) => {
          this.sources.push({ name: element });
        });
      });
  },
  updated() {},
  mounted() {
    M.FormSelect.init(document.getElementById("source_select"));
    document.getElementById("_id_input").value =
      Math.random().toString(36).substring(2, 15) +
      Math.random().toString(36).substring(2, 15);
    // var socket = io(process.env.VUE_APP_WSURL);
    // socket.
    // socket.on("connection", function(){
    //   console.log("hallo")
    //   var id = socket.id;
    //   console.log(id);
    //   console.log("IDENTIFIER:" + id);
    //   document.getElementById('socket_id_input').value = id;
    //   this.sock_id = id;
    // });

    // socket.on("message", function (msg) {
    //   console.log("HALLO HALLO");
    //   console.log(msg);
    //   //console.log(socket.id);
    //   if (msg.split(":")[0] == "Proc") {
    //     $("#procent").html(msg.split(":")[1] + "%");
    //     $("#process_bar").html(
    //       "<div class='determinate' style='width: " +
    //         msg.split(":")[1] +
    //         "%" +
    //         "' ></div>"
    //     );
    //     return;
    //   }

    //   if (msg.includes("SOCKET_ID")) {
    //     document.getElementById("socket_id_input").value = msg.split(":")[1];
    //     //this.sock_id = msg.split(":")[1];
    //     return;
    //   }
    //   $("#messages").append("<li class='collection-item'>" + msg + "</li>");
    //   return;
    // });

    var today = new Date();
    var dd = String(today.getDate()).padStart(2, "0");
    var mm = String(today.getMonth() + 1).padStart(2, "0");
    var yyyy = today.getFullYear();

    today = yyyy + "-" + mm + "-" + dd;

    $("#id_max_date").val(today);

    $("#datapoints_form").on("submit", (e) => {
      e.preventDefault();
      var form = $("#datapoints_form");
      form.addClass("hide");
      $("#header_datapoints").addClass("hide");
      $("#btn_row").addClass("hide");
      $("#loader").removeClass("hide");

      var form_data = new FormData(document.getElementById("datapoints_form"));

      //console.log(form_data);
      $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        xhrFields: {
          withCredentials: true,
        },
        url: process.env.VUE_APP_CLINICALURL + "/upload/datapoints",
        data: form_data,
        success: function (e) {
          //$("#after-logs").removeClass("hide");
          //   $("#loader").addClass("hide");
          console.log(e);
          //   document.getElementById("results").innerText = e["message"];
          //   document.getElementById("process-log").innerText = e["msg_queue"];
          setTimeout(check_status, interval);
        },
        error: function(e){
          console.log(e);
          $("#loader").addClass("hide");
              $("#after-logs").removeClass("hide");
               document.getElementById("results").innerText ="ERROR";
            

        }
      });

      var url = process.env.VUE_APP_CLINICALURL + "/get/cache";
      var interval = 2000;

      function check_status() {
        $.ajax({
          type: "GET",
          url: url,
          data: {'_id': document.getElementById("_id_input").value },
          success: function (e) {
            console.log(e);
            if (e.message != null && e["message"]["status"] == "done") {
              console.log("Done");
            }
          },
          complete: function (e) {
            console.log(e.responseJSON);
            if (e.responseJSON["message"]["status"] == "done") {
              $("#loader").addClass("hide");
              $("#after-logs").removeClass("hide");
               document.getElementById("results").innerText = e.responseJSON["message"]['message'];
                document.getElementById("process-log").innerText = e.responseJSON['message']["msg_queue"];
            } else {

              document.getElementsByClassName('determinate')[0].style.width = e.responseJSON["message"]["status"]*100 + "%"
              setTimeout(check_status, interval);
            }
          },
        });
      }
      
    });
  },
};
</script>