<template>
  <div class="container">
    <div class="row">
      <h1>Datamodel Bulk-Upload</h1>
      <h5 style="color: red; display: none" id="warning">
        Please upload a file...
      </h5>

      <div id="responses" style="display: none">
        <div class="row">
          <div class="col s6">
            <a class="blue-grey lighten-1 btn" href="/data-steward/graph"
              >See visualization</a
            >
          </div>
          <div class="col s6">
            <a class="blue-grey lighten-1 btn" href="/data-steward/edit"
              >Edit datamodel</a
            >
          </div>
        </div>
        <h5>Responses from the DSII (Data Steward Integration Intelligence)</h5>
        <ul id="resp_list"></ul>
      </div>

      <div
        class="preloader-wrapper big active"
        style="display: none"
        id="loader"
      >
        <div class="spinner-layer spinner-blue">
          <div class="circle-clipper left">
            <div class="circle"></div>
          </div>
          <div class="gap-patch">
            <div class="circle"></div>
          </div>
          <div class="circle-clipper right">
            <div class="circle"></div>
          </div>
        </div>

        <div class="spinner-layer spinner-red">
          <div class="circle-clipper left">
            <div class="circle"></div>
          </div>
          <div class="gap-patch">
            <div class="circle"></div>
          </div>
          <div class="circle-clipper right">
            <div class="circle"></div>
          </div>
        </div>

        <div class="spinner-layer spinner-yellow">
          <div class="circle-clipper left">
            <div class="circle"></div>
          </div>
          <div class="gap-patch">
            <div class="circle"></div>
          </div>
          <div class="circle-clipper right">
            <div class="circle"></div>
          </div>
        </div>

        <div class="spinner-layer spinner-green">
          <div class="circle-clipper left">
            <div class="circle"></div>
          </div>
          <div class="gap-patch">
            <div class="circle"></div>
          </div>
          <div class="circle-clipper right">
            <div class="circle"></div>
          </div>
        </div>
      </div>

      <form id="datamodel_form">
        <div class="row">
          <div class="input-field col s6">
            <select name="write_mode">
              <option value disabled selected>
                Determine strategy for existing datamodel entries:
              </option>
              <option value="new">
                Drop complete datamodel before loading file
              </option>
              <option value="add">
                Leave existing entries untouched, append your new ones
              </option>
            </select>
            <label>Choose a Strategy</label>
          </div>
          <div class="input-field col s6">
            <input
              value="0"
              id="header_line"
              name="header_line"
              required
              type="number"
              class="validate"
              placeholder="Offset of header line (0 = first line in file):"
            />
            <label for="header_line"
              >Offset of header line (0 = first line in file):</label
            >
          </div>
        </div>
        <div class="row">
          <div class="input-field col s4">
            <div class="file-field input-field">
              <div class="btn blue-grey lighten-1">
                <span>File</span>
                <input
                  type="file"
                  name="datamodel_file"
                  id="datamodel_file"
                  required
                />
              </div>
              <div class="file-path-wrapper">
                <input
                  class="file-path validate"
                  type="text"
                  placeholder="Upload your Datamodel"
                />
              </div>
            </div>
          </div>
        </div>
        <div class="row">
          <p class="left-align">What do you want to do?</p>
          <div class="col s6 left-align">
            <p>
              <label>
                <input type="checkbox" name="core_method" checked />
                <span>Load Core Model (Attributes, Codes, Units)</span>
              </label>
            </p>
            <p>
              <label>
                <input type="checkbox" name="mappings_method" />
                <span>Load Mappings</span>
              </label>
            </p>
          </div>
        </div>
        <div class="row">
          <div class="col s12 right-align">
            <button
              class="btn waves-effect waves-light blue-grey lighten-1"
              type="button"
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
  </div>
</template>


<script>
import $ from "jquery";

export default {
  name: "modelform",
  mounted() {
    var form = document.querySelector("#datamodel_form");
    //var file = document.querySelector('#datamodel_file');

    $("#form_btn").on("click", function () {
      if (document.getElementById("datamodel_file").files.length == 0) {
        $("#warning").show();
        return;
      }

      var form_data = new FormData(form);

      //console.log(form_data);
      $("#datamodel_form").hide();
      $("#warning").hide();
      $("#loader").show();

      $.ajax({
        type: "POST",
        processData: false,
        contentType: false,
        data: form_data,
        xhrFields: {
       withCredentials: true
    },
        url: process.env.VUE_APP_CLINICALURL + "/upload/datamodel",
        success: function (event) {
          console.log(event);
          var messages = event["report"];
          $("#loader").hide();
          for (var k = 0; k < messages.length; k++) {
            $("#resp_list").append("<li>" + messages[k] + "</li>");
          }
          $("#responses").show();
        },
        error: function (e) {
          console.log(e);
          $("#loader").hide();

          $("#resp_list").append(
            "<li>" + "Ooops something went wrong..." + "</li>"
          );

          $("#responses").show();
        },
      });
    });
  },
};
</script>