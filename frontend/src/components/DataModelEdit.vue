<template>
  <div class="container">
    <h1>Model Wizard</h1>
    <div class="row">
      <div class="col s12">
        <ul class="tabs">
          <li class="tab col s3">
            <a class="active" href="#core_tab">Variables and Mappings</a>
          </li>
          <li class="tab col s3">
            <a href="#measurement_tab">Measurements</a>
          </li>
          <li class="tab col s3">
            <a href="#codes_units_tab">Codes and Units</a>
          </li>
        </ul>
      </div>
    </div>
    <hr style="height: 1px; background-color: black" />


    <!--
      Modal Code Mappings

      -->
    <div id="modal_add_code_mapping" class="modal">
      <div class="modal-content">
        <h4>Add a Code Mapping: <a id="code_mapping_name_header"></a></h4>
        <p>Please provide more information</p>
        <h3>This is only available via the spreadsheet...</h3>
        <p class="error_message" id="code_mapping_error_message"></p>


        
      </div>
    </div>

  

    <!-- 

      Modal units

    -->
    <div id="modal_add_unit" class="modal">
      <div class="modal-content">
        <h4>Add a Unit: <a id="unit_name_header"></a></h4>
        <p>Please provide more information</p>
        <p class="error_message" id="unit_error_message"></p>


        <form id="form_add_unit">
          <div class="row">
            <div class="input-field col s6">
              <input type="text" id="unit_name" required name="unit_name" />
              <label for="unit_name">Unit name (required)</label>
              <span class="helper-text">
                The unique name of the unit throughout the complete datamodel
              </span>
            </div>
            <div class="input-field col s6">
              <input
                type="text"
                id="unit_description"
                required
                name="unit_description"
              />
              <label for="unit_description">Unit Description (required)</label>
              <span class="helper-text"> A description for the unit </span>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <p>
                  <label>
                    <input
                      type="checkbox"
                      name="ucum"
                      id="unit_ucum"
                      checked="checked"
                    />
                    <span>Is UCUM Unit (yes/no)</span>
                  </label>
                  <span class="helper-text"
                    >Indicates whether this unit is in UCUM or not</span
                  >
                </p>
              </div>
            </div>
            <div class="row">
              <div class="col s12 right-align">
                <button
                  class="btn waves-effect waves-green blue-grey lighten-1"
                >
                  Create Unit<i class="material-icons right">send</i>
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- 

      Modal codes

    -->
    <div id="modal_add_code" class="modal">
      <div class="modal-content">
        <h4>Add a Code: <a id="code_name_header"></a></h4>
        <p>Please provide more information</p>
                <p class="error_message" id="code_error_message"></p>

        <form id="form_add_code">
          <div class="row">
            <div class="input-field col s6">
              <input type="text" id="code_name" required name="code_name" />
              <label for="code_name">Code name (required)</label>
              <span class="helper-text">
                The unique name of the code throughout the complete datamodel
              </span>
            </div>
            <div class="input-field col s6">
              <input
                type="text"
                id="code_description"
                required
                name="code_discription"
              />
              <label for="code_description">Code description (required)</label>
              <span class="helper-text"> A description for the code </span>
            </div>
          </div>
          <div class="row">
            <p class="left-align ml-15">
              Provide the code keys with its values
            </p>
            <div class="col s6">
              <table>
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody id="table_body_code">
                  <tr>
                    <td><input name="key_1" type="text" required/></td>
                    <td><input name="val_1" type="text" required/></td>
                  </tr>
                </tbody>
                <br />
              </table>
            </div>
            <div class="input-field col s6">
              <p>
                <label>
                  <input
                    type="checkbox"
                    name="active"
                    id="code_active"
                    checked="checked"
                  />
                  <span>Active (yes/no)</span>
                </label>
                <span class="helper-text"
                  >Indicates whether item is in use in the backend's current
                  setup</span
                >
              </p>
            </div>
          </div>
          <div class="row">
            <div class="col s6 right-align">
              <a
                class="btn-floating btn-large waves-effect waves-light blue-grey"
                id="add_code_row_btn"
                ><i class="material-icons">add</i></a
              >
            </div>
          </div>
          <div class="row">
            <div class="col s12 right-align">
              <button class="btn waves-effect waves-green blue-grey lighten-1">
                Create Code<i class="material-icons right">send</i>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <div id="modal_add_src" class="modal">
      <div class="modal-content">
        <h4>Add a Source: <a id="src_name"></a></h4>
        <p>Please add more information</p>

        <form id="new_src_form">
          <div class="row">
            <div class="input-field col s6">
              <input
                type="text"
                name="abbreviation"
                id="src_abbreviation"
                required
              />
              <label for="src_abbreviation">Abbreviation (required)</label>
              <span class="helper-text">
                Abbreviated label, unique in the IDSN clinical datamodel</span
              >
            </div>
            <div class="input-field col s6">
              <input type="text" name="source" id="src_source" />
              <label for="src_source">Source</label>
              <span class="helper-text">
                Name of the registry/study/source</span
              >
            </div>
          </div>
          <div class="row">
            <div class="input-field col s6">
              <input type="text" name="pid_colname" id="src_pid_colname" />
              <label for="src_pid_colname">PID_colname</label>
              <span class="helper-text">
                Alternate name of column containing the patient's ID</span
              >
            </div>
            <div class="input-field col s6">
              <input type="text" name="site_colname" id="src_site_colname" />
              <label for="src_site_colname">SITE_colname</label>
              <span class="helper-text">
                Alternate name of column containing the site's ID (multi-center
                study data)</span
              >
            </div>
          </div>
          <div class="row">
            <div class="input-field col s6">
              <input
                type="text"
                name="timestamp_colname"
                id="src_timestamp_colname"
              />
              <label for="src_timestamp_colname">TIMESTAMP_colname</label>
              <span class="helper-text">
                Alternate name of column containing the measurement's time
                stamp</span
              >
            </div>
            <div class="input-field col s6">
              <input type="text" name="header_offset" id="src_header_offset" />
              <label for="src_header_offset">Header_offset</label>
              <span class="helper-text">
                Number of lines to ignore before expecting the first line of the
                actual data (which is the header)</span
              >
            </div>
          </div>
          <div class="row">
            <div class="input-field col s6">
              <input type="text" name="filepath" id="src_filepath" />
              <label for="src_filepath">Filepath</label>
              <span class="helper-text"> Location of the uploaded file</span>
            </div>
          </div>
          <div class="row">
            <div class="progress" id="src_loader" style="display: none">
              <div class="indeterminate"></div>
            </div>

            <div class="col s12 right-align" id="src_btn">
              <button class="btn waves-effect waves-green blue-grey lighten-1">
                Create Source<i class="material-icons right">send</i>
              </button>
            </div>
            <div
              class="col s12"
              id="error_src"
              style="display: none; color: red"
            >
              Ooops... Something went wrong
            </div>
          </div>
        </form>
      </div>
    </div>
    <!-- Modal Structure Add Mapping-->
    <div id="modal_add_mapping" class="modal">
      <div class="modal-content">
        <h4>Add Attribute Mapping:</h4>
        <div class="row">
          <div class="col s4 right-align"><a id="mapping_name_1"></a></div>
          <div class="col s4">
            <i class="material-icons">trending_flat</i>
          </div>
          <div class="col s4 left-align"><a id="mapping_name_2"></a></div>
        </div>
        <p>Please Fill in additional Information</p>
        <div class="row">
          <form id="add_mapping_form">
            <div class="row">
              <div class="input-field col s6">
                <p>
                  <label>
                    <input
                      type="checkbox"
                      name="active"
                      id="attr_mapping_active"
                      checked="checked"
                    />
                    <span>Active (yes/no)</span>
                  </label>
                  <span class="helper-text"
                    >Indicates whether item is in use in the backend's current
                    setup</span
                  >
                </p>
              </div>
              <div class="input-field col s6">
                <input
                  type="text"
                  name="source_attr"
                  id="attr_mapping_source"
                  required
                  readonly
                />
                <label for="attr_mapping_source">Source Attribute</label>
                <span class="helper-text">
                  Unique attribute name in the source datamodel</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <input
                  type="text"
                  name="target"
                  id="attr_mapping_target"
                  required
                  readonly
                />
                <label for="attr_mapping_target">Target Attribute</label>
                <span class="helper-text"> Name of the Target Attribute</span>
              </div>

              <div class="input-field col s6">
                <input
                  type="text"
                  name="source"
                  id="mapping_source"
                  class="autocomplete"
                  required
                />

                <label for="mapping_source">Source</label>
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <input
                  type="text"
                  name="transformation"
                  id="attr_mapping_transformation"
                />
                <label for="attr_mapping_target">Transformation</label>
                <span class="helper-text"
                  >Operation to be applied, if necessary, when mapping</span
                >
              </div>
            </div>
            <div class="row">
              <div
                class="progress"
                id="attr_mapping_loader"
                style="display: none"
              >
                <div class="indeterminate"></div>
              </div>

              <div class="col s12 right-align" id="attr_mapping_btn">
                <button
                  class="btn waves-effect waves-green blue-grey lighten-1"
                >
                  Create Attribute-Mapping<i class="material-icons right"
                    >send</i
                  >
                </button>
              </div>
              <div
                class="col s12"
                id="error_mapping"
                style="display: none; color: red"
              >
                Ooops... Something went wrong
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    <!-- Modal Structure Add Attribute-->
    <div id="modal_attr_add" class="modal">
      <div class="modal-content">
        <h4>Add Attribute: <a id="attribute_name"></a></h4>
        <p>Please fill in as many information you know</p>
        <div class="row">
          <form class="col s12" id="add_attr">
            <div class="row">
              <div class="input-field col s6">
                <p>
                  <label>
                    <input
                      type="checkbox"
                      name="active"
                      id="new_attr_active"
                      checked="checked"
                    />
                    <span>Active (yes/no)</span>
                  </label>
                  <span class="helper-text"
                    >Indicates whether item is in use in the backend's current
                    setup</span
                  >
                </p>
              </div>
              <div class="input-field col s6">
                <input type="text" name="topic" id="new_attr_topic" />
                <label for="new_attr_topic">Topic</label>
                <span class="helper-text"
                  >Topic (= semantic category) the identifier belongs to (e.g.
                  neuropsychology, lab, medication, ...)</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <input
                  type="text"
                  name="topic_description"
                  id="new_attr_topic_deescription"
                />
                <label for="new_attr_topic_description"
                  >Topic Description</label
                >
                <span class="helper-text"> Topic's full text description</span>
              </div>
              <div class="input-field col s6">
                <input type="text" name="umbrella" id="new_attr_umbrella" />
                <label for="new_attr_umbrella">Umbrella</label>
                <span class="helper-text"
                  >Generalized term wrapping an attribute with further,
                  analogous terms (= semantically highly similar, but not
                  identical)</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <input
                  type="text"
                  name="umbrella_description"
                  id="new_attr_umbrella_description"
                />
                <label for="new_attr_umbrella_description"
                  >Umbrella Description</label
                >
                <span class="helper-text"
                  >Umbrella's full text description</span
                >
              </div>
              <div class="input-field col s6">
                <input
                  type="text"
                  name="attribute"
                  id="new_attr_attribute"
                  required="required"
                />
                <label for="new_attr_attribute">Attribute (required)</label>
                <div id="attr_taken_err"></div>
                <span class="helper-text"
                  >The unique item's name throughout the overall data
                  model</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <input
                  type="text"
                  name="attribute_description"
                  id="new_attr_attribute_description"
                  required="required"
                />
                <label for="new_attr_attribute_description"
                  >Attribute Description (required)</label
                >
                <span class="helper-text"
                  >Unique attribute's fulltext description</span
                >
              </div>
              <div class="input-field col s6">
                <input
                  type="text"
                  name="attribute_tooltip"
                  id="new_attr_tooltip"
                  required="required"
                />
                <label for="new_attr_tooltip"
                  >Attribute Tooltip (required)</label
                >
                <span class="helper-text"
                  >Very short description, suitable for tooltips or table
                  headings</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <select name="datatype" id="new_attr_datatype" class="browser-default">
                  <option value="" selected>Choose a datatype</option>
                  <option value="code">code</option>
                  <option value="date">date</option>
                  <option value="int">int</option>
                  <option value="float">float</option>
                  <option value="string">string</option>
                  <option value="array(date)">array(date)</option>
                  <option value="array(int)">array(int)</option>
                  <option value="array(float)">array(float)</option>
                  <option value="array(string)">array(string)</option>
                  <option value="array(code)">array(code)</option>
                </select>
              </div>
              <div class="input-field col s6">
                <input type="text" name="domain" id="new_attr_domain" />
                <label for="new_attr_domain">Attribute Range</label>
                <span class="helper-text"
                  >Accepted range of numeric values (2-items arry in Python
                  notation; empty entry is valid) or name of code (for
                  categorical items)</span
                >
              </div>
            </div>
            <div class="row">
              <div class="input-field col s6">
                <select
                  name="unit"
                  id="new_attr_unit_unit"
                  required="required"
                  class="browser-default"
                >
                  <option value="" selected disabled>Choose a unit</option>
                  <option v-for="unit in units" :key="unit.name">
                    {{ unit.name }}
                  </option>
                </select>

                <span class="helper-text">Unique code expressing unit</span>
              </div>
            </div>

            <div class="row">
              <div class="progress" id="add_attr_loader" style="display: none">
                <div class="indeterminate"></div>
              </div>

              <div class="col s12 right-align" id="add_attr_btn">
                <button
                  id="attr_submit_btn"
                  class="btn waves-effect waves-green blue-grey lighten-1"
                >
                  Create Attribute<i class="material-icons right">send</i>
                </button>
              </div>
              <div
                class="col s12"
                id="error_add"
                style="display: none; color: red"
              >
                Ooops... Something went wrong
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
    <div id="core_tab" class="col s12">
      <div class="row">
        <h4>Extend the Core Model</h4>

        <div class="col s12">
          <h5>
            Add an Attribute<i
              class="material-icons tooltipped"
              data-position="bottom"
              data-tooltip="Add a new variable to the clinical datamodel. Several information must be provided!"
              >info_outline</i
            >
          </h5>
          <div class="row">
            <div class="input-field col s10">
              <input id="attr_new" type="text" name="attr_new" />
              <label for="attr_new">Attribute Name</label>
            </div>
            <div class="col s2">
              <button
                class="btn waves-effect waves-light blue-grey lighten-1"
                type="button"
                id="submit_add_attr"
              >
                Add attribute
                <i class="material-icons right">submit</i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <br />
      <hr style="height: 1px; background-color: black" />
      <div class="row">
        <h4>Extend the Mappings</h4>

        <div class="row">
          <h5>
            Add a Source<i
              class="material-icons tooltipped"
              data-position="bottom"
              data-tooltip="Add a new source to the clinical datamodel."
              >info_outline</i
            >
          </h5>
          <div class="row">
            <div class="input-field col s10">
              <input id="src_new" type="text" name="src_new" />
              <label for="src_new">Source Name</label>
            </div>
            <div class="col s2">
              <button
                class="btn waves-effect waves-light blue-grey lighten-1"
                type="button"
                id="submit_add_src"
              >
                Add source
                <i class="material-icons right">submit</i>
              </button>
            </div>
          </div>
        </div>
        <div class="row">
          <h5>
            Add an Attribute-Mapping<i
              class="material-icons tooltipped"
              data-position="bottom"
              data-tooltip="The source attribute is the external variable that maps to an internal variable. Source of external variable must be specified!"
              >info_outline</i
            >
          </h5>
          <div class="col s12" id="attr_mapping_form">
            <div class="row">
              <div class="input-field col s4">
                <input type="text" name="source_attr" id="source_attr" />

                <label for="source_attr">Source Attribute</label>
              </div>
              <div class="col s2">
                <i class="material-icons large">trending_flat</i>
              </div>
              <div class="input-field col s4">
                <input
                  type="text"
                  name="target_attr"
                  id="target_attr"
                  class="autocomplete"
                />

                <label for="target_attr">Target Attribute</label>
              </div>
              <div class="col s2">
                <button
                  class="btn waves-effect waves-light blue-grey lighten-1"
                  name="action"
                  type="button"
                  id="submit_mapping"
                >
                  Add mapping
                  <i class="material-icons right">submit</i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div id="measurement_tab" class="col s12">
      <div class="row">
        <h4>
          Add a measurement
          <i
            class="material-icons tooltipped"
            data-position="bottom"
            data-tooltip="A measurement consists of up to three inputs. WHAT is measured (Object of measurement). WHERE is it measured (Location of measurement). HOW is it measured (Method of measurement)."
            >info_outline</i
          >
        </h4>
        <div class="row">
          <form id="measurement_form" class="col s12">
            <div class="row">
              <div class="input-field col s6">
                <input
                  required
                  placeholder="e.g. Adrenaline"
                  id="object"
                  name="object"
                  type="text"
                  class="validate"
                />
                <label for="object">Object of measurement</label>
              </div>
              <div class="input-field col s6">
                <input
                  placeholder="e.g. Blood"
                  name="location"
                  id="location"
                  type="text"
                  class="validate"
                />
                <label for="location">Location of measurement</label>
              </div>
            </div>
            <div class="row">
              <div class="input-field col s12">
                <textarea
                  id="textarea1"
                  name="method"
                  class="materialize-textarea"
                  placeholder="e.g. The patient provides a blood sample of 5ml. The sample needs to be taken on an empty stomach."
                ></textarea>
                <label for="textarea1">Method of measurement</label>
              </div>
            </div>
            <div class="row">
              <div class="col s12 right-align">
                <button
                  class="btn waves-effect waves-green blue-grey lighten-1"
                >
                  Create Measurement<i class="material-icons right">send</i>
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>

    <div id="codes_units_tab" class="col s12">
      <div class="row">
        <div class="col s12">
          <h5>Add a Code</h5>
          <div class="input-field col s10">
            <input
              placeholder="Code"
              name="code"
              id="code"
              type="text"
              class="validate"
            />
            <label for="code">Code name</label>
          </div>
          <div class="col s2">
            <button
              class="btn waves-effect waves-light blue-grey lighten-1"
              type="button"
              id="code_add_btn"
            >
              Add Code
            </button>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col s12">
          <h5>Add a Unit</h5>
          <div class="input-field col s10">
            <input
              placeholder="Unit"
              name="unit"
              id="unit"
              type="text"
              class="validate"
            />
            <label for="unit">Unit name</label>
          </div>
          <div class="col s2">
            <button
              class="btn waves-effect waves-light blue-grey lighten-1"
              type="button"
              id="unit_add_btn"
            >
              Add Unit
            </button>
          </div>
        </div>
      </div>
      <div class="row">
        <h5>Add a Code-Mapping</h5>
        <div class="col s12">
          <div class="input-field col s10">
          <input type="text" class="validate" id="code_mapping_input" placeholder="Code Mapping" name="code_mapping_input"/>
          <label for="code_mapping_input">Code-Mapping name</label>
          </div>
          <div class="col s2">
            <button
              class="btn waves-effect waves-light blue-grey lighten-1"
              type="button"
              id="code_mapping_add_btn"
            >
              Add Code Mapping
            </button>
          </div>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script>
import ax from "axios";
const axios = ax;
import M from "materialize-css";
export default {
  name: "editDatamodel",
  data() {
    return {
      attrs: [],
      sources: [],
      units: [],
      addCodeTableRowNum: 1,
    };
  },
  async created() {
    const units = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/units"
    );
    const unitsAsJson = JSON.parse(units.data["units"]);
    unitsAsJson.forEach((unit) => {
      this.units.push({
        name: unit["pk"],
        UCUM: unit["fields"]["UCUM"],
        description: unit["fields"]["Description"],
      });
    });

    const attributes = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attributes/all"
    );
    const sources_all = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/sources/all"
    );
    //console.log(attributes['data']['attributes']);
    attributes["data"]["attributes"].forEach((element) => {
      this.attrs.push(element["name"]);
    });

    let autoCompleteData = {};
    this.attrs.forEach((att) => {
      autoCompleteData[att] = null;
    });
    var autoCompleteOptions = {
      data: autoCompleteData,
    };
    M.Tabs.init(document.querySelectorAll(".tabs"));

    var elems = document.querySelectorAll(".autocomplete");
    M.Autocomplete.init(elems, autoCompleteOptions);
    var elemsModal = document.querySelectorAll(".modal");
    M.Modal.init(elemsModal);

    document.getElementById("submit_add_attr").onclick = async function () {
      var instance = M.Modal.getInstance(
        document.getElementById("modal_attr_add")
      );
      var header = document.getElementById("attribute_name");
      header.innerHTML = "";
      var val = document.getElementById("attr_new").value;
      header.appendChild(document.createTextNode(val));
      if (val != null && val != "") {
        const resp = await axios.get(
          process.env.VUE_APP_CLINICALURL +
            "/get/check-attr" +
            "?attr_name=" +
            val
        );
        //console.log(resp);
        if (resp["data"]["message"] == "taken") {
          M.toast({ html: "Attribute Name already taken!" });
          return;
        }
        document
          .getElementById("new_attr_attribute")
          .setAttribute("value", val);
        M.updateTextFields();
        instance.open();
      } else {
        M.toast({ html: "Please check your input!" });
        return;
      }
    };

    /**
      Click on add code mapping

    */
    document.getElementById("code_mapping_add_btn").onclick = function(){
      var codeMappingName = document.getElementById("code_mapping_input").value;
      var modalInstance = M.Modal.getInstance(
          document.getElementById("modal_add_code_mapping")
        );
      if (codeMappingName == null || codeMappingName == "") {
        M.toast({
          html: "Please provide a valid Code-Mapping name!",
        });
        return;
      } else {
        modalInstance.open();

      }
      
      
    }

    /**
     * Click on unit add
     * adding unit
     *
     *
     */

    document.getElementById("unit_add_btn").onclick = () => {
      var unitName = document.getElementById("unit").value;
      if (unitName == null || unitName == "") {
        M.toast({
          html: "Please provide a valid unit name!",
        });
        return;
      } else {
        var modalInstance = M.Modal.getInstance(
          document.getElementById("modal_add_unit")
        );
        var headerUnitModal = document.getElementById("unit_name_header");
        headerUnitModal.innerText = unitName;
        document.getElementById("unit_name").value = unitName;
        M.updateTextFields();

        modalInstance.open();
      }
    };
    /**
     *
     * submit unit add
     *
     */

    document.getElementById("form_add_unit").onsubmit = async function (e) {
      var unitName = document.getElementById("unit").value;
      e.preventDefault();
      const formData = new FormData(this);
      const unitUploadResponse = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/unit",
        data: formData,
        withCredentials: true,
      });
      if (unitUploadResponse.data["message"] == "ok") {
        var modalInstance = M.Modal.getInstance(
          document.getElementById("modal_add_unit")
        );
        modalInstance.close();
        M.toast({
          html: "You successfully added a unit: " + unitName,
        });
        return;
      } else {
        document.getElementById("unit_error_message").innerText = "Something went wrong... try again or contact the support.";
      }
    };

    /**
     * Click on code add
     * Adding Code
     * Code add
     *
     */
    document.getElementById("code_add_btn").onclick = function () {
      var codeName = document.getElementById("code").value;
      if (codeName == null || codeName == "") {
        M.toast({
          html: "Please provide a valid code name!",
        });
        return;
      } else {
        var modalInstance = M.Modal.getInstance(
          document.getElementById("modal_add_code")
        );

        var headerCodeModal = document.getElementById("code_name_header");
        headerCodeModal.innerText = codeName;
        document.getElementById("code_name").value = codeName;
        M.updateTextFields();

        modalInstance.open();
      }
    };
    /**
     * Adding rows in add code dialog
     * add row
     * add code key value
     *
     *
     */
    var addCodeTableRows = this.addCodeTableRowNum;
    document.getElementById("add_code_row_btn").onclick = function () {
      var tableBody = document.getElementById("table_body_code");
      var row = document.createElement("tr");
      var tdKey = document.createElement("td");
      var tdVal = document.createElement("td");
      var inputKey = document.createElement("input");
      var inputVal = document.createElement("input");
      inputKey.setAttribute("name", "key_" + String(addCodeTableRows + 1));
      inputVal.setAttribute("name", "val_" + String(addCodeTableRows + 1));
      tdKey.appendChild(inputKey);
      tdVal.appendChild(inputVal);
      row.appendChild(tdKey);
      row.appendChild(tdVal);
      tableBody.appendChild(row);
      addCodeTableRows++;
      return;
    };

    /**
     * Submit of code app form
     *
     *
     */

    document.getElementById("form_add_code").onsubmit = async function (e) {
      e.preventDefault();
      var formData = new FormData(this);

      const codeUploadResponse = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/code",
        data: formData,
        withCredentials: true,
      });

      
      if (codeUploadResponse.status == 200 &&  codeUploadResponse.data["message"] == "ok") {
        var modalInstance = M.Modal.getInstance(
          document.getElementById("modal_add_code")
        );
        modalInstance.close();
        var codeName = document.getElementById("code").value;

        M.toast({
          html: "You successfully added a code: " + codeName,
        });
        this.reset();
        document.getElementById("code").value = "";



        return;
      }
      else{
        console.log("error adding code.")
        document.getElementById("code_error_message").innerText = "Something went wrong.... Try again or contact the support."

      }
    };

    document.getElementById("add_attr").onsubmit = async function (e) {
      e.preventDefault();
      document.getElementById("add_attr_btn").style.display = "none";
      document.getElementById("add_attr_loader").style.display = "block";

      var form_data = new FormData(document.getElementById("add_attr"));
      console.log(form_data);
      const postAttribute = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/attribute",
        data: form_data,
        withCredentials: true,
      });
      if (
        postAttribute["data"]["message"] == "ok" &&
        postAttribute.status == 200
      ) {
        var instance = M.Modal.getInstance(
          document.getElementById("modal_attr_add")
        );
        instance.close();
        document.getElementById("add_attr_btn").style.display = "block";
        document.getElementById("add_attr_loader").style.display = "none";
        document.getElementById("add_attr").reset();

        M.toast({
          html: "You created a new Attribute: " + form_data.get("attribute"),
        });
        const attributes = await axios.get(
          process.env.VUE_APP_CLINICALURL + "/get/attributes/all"
        );
        attributes["data"]["attributes"].forEach((element) => {
          this.attrs.push(element["name"]);
        });

        let autoCompleteData = {};
        this.attrs.forEach((att) => {
          autoCompleteData[att] = null;
        });
        var autoCompleteOptions = {
          data: autoCompleteData,
        };

        var elems = document.querySelectorAll(".autocomplete");
        M.Autocomplete.init(elems, autoCompleteOptions);
      } else {
        console.log("Something went wrong...");
        document.getElementById("add_attr_loader").style.display = "none";

        document.getElementById("error_add").style.display = "block";
        document.getElementById("error_add").innerHTML +=
          ": " + postAttribute["data"]["message"];
      }
    };
    document.getElementById("submit_mapping").onclick = function () {
      var instance = M.Modal.getInstance(
        document.getElementById("modal_add_mapping")
      );
      var attr1 = document.getElementById("source_attr").value;
      var attr2 = document.getElementById("target_attr").value;
      if (attr1 == "" || attr2 == "" || attr1 == null || attr2 == null) {
        M.toast({ html: "Please check your input!" });
        return;
      } else {
        document.getElementById("mapping_name_1").innerHTML = attr1;
        document.getElementById("mapping_name_2").innerHTML = attr2;
        document.getElementById("attr_mapping_source").value = attr1;
        document.getElementById("attr_mapping_target").value = attr2;
        var autocomplete_source = document.getElementById("mapping_source");
        let autoCompleteData_source = {};
        sources_all["data"]["sources"].forEach((elem) => {
          autoCompleteData_source[elem] = null;
        });
        var autoCompleteOptions_source = {
          data: autoCompleteData_source,
        };

        M.Autocomplete.init(autocomplete_source, autoCompleteOptions_source);
        M.updateTextFields();
        instance.open();
      }
    };
    document.getElementById("add_mapping_form").onsubmit = async function (e) {
      e.preventDefault();
      var instance = M.Modal.getInstance(
        document.getElementById("modal_add_mapping")
      );
      var attr1 = document.getElementById("source_attr").value;
      var attr2 = document.getElementById("target_attr").value;
      var form_data = new FormData(document.getElementById("add_mapping_form"));

      const postMapping = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/mapping",
        data: form_data,
        withCredentials: true,
      });
      console.log(postMapping);
      document.getElementById("attr_mapping_btn").style.display = "none";
      document.getElementById("attr_mapping_loader").style.display = "block";
      if (postMapping["data"]["message"] == "ok" && postMapping.status == 200) {
        instance.close();
        document.getElementById("add_mapping_form").reset();
        M.toast({
          html:
            "You successfully added an Attribute Mapping: " +
            attr1 +
            " --> " +
            attr2,
        });
      } else {
        document.getElementById("error_mapping").style.display = "block";
        document.getElementById("attr_mapping_loader").style.display = "none";
        document.getElementById("attr_mapping_btn").style.display = "block";

        document.getElementById("error_mapping").innerHTML =
          "Ooops... Something went wrong: ";
        document
          .getElementById("error_mapping")
          .appendChild(document.createTextNode(postMapping["data"]["message"]));
      }
      return;
    };

    document.getElementById("submit_add_src").onclick = function () {
      var instance = M.Modal.getInstance(
        document.getElementById("modal_add_src")
      );
      var srcName = document.getElementById("src_new").value;
      if (srcName == "" || srcName == null) {
        M.toast({ html: "Please check your input!" });
      } else {
        instance.open();
        document.getElementById("src_name").innerHTML = srcName;
        document.getElementById("src_source").value = srcName;
        M.updateTextFields();
      }
    };
    document.getElementById("new_src_form").onsubmit = async function (e) {
      e.preventDefault();
      var instance = M.Modal.getInstance(
        document.getElementById("modal_add_src")
      );
      var srcName = document.getElementById("src_new").value;
      document.getElementById("src_btn").style.display = "none";
      document.getElementById("src_loader").style.display = "block";
      var form_data = new FormData(document.getElementById("new_src_form"));
      //console.log(form_data);

      const postSrc = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/source",
        data: form_data,
        withCredentials: true,
      });

      if (postSrc["data"]["message"] == "ok" && postSrc.status == 200) {
        document.getElementById("new_src_form").reset();
        document.getElementById("src_loader").style.display = "none";
        document.getElementById("src_btn").style.display = "block";

        instance.close();
        M.toast({ html: "You successfully added a new source: " + srcName });
      } else {
        document.getElementById("src_loader").style.display = "none";
        document.getElementById("error_src").style.display = "block";
        document.getElementById("error_src").innerHTML +=
          ": " + postSrc["data"]["message"];
        document.getElementById("src_btn").style.display = "block";
      }
      return;
    };
    document.getElementById("new_attr_attribute").onchange = async function () {
      document.getElementById("attr_taken_err").innerHTML = "";
      document.getElementById("attr_taken_err").style.color = "red";
      document.getElementById("attr_submit_btn").disabled = false;
      const resp = await axios.get(
        process.env.VUE_APP_CLINICALURL +
          "/get/check-attr" +
          "?attr_name=" +
          document.getElementById("new_attr_attribute").value
      );
      //console.log(resp);
      if (resp["data"]["message"] == "taken") {
        document.getElementById("attr_taken_err").innerHTML =
          "Attribute name is already taken";
        document.getElementById("attr_submit_btn").disabled = true;
      } else {
        document.getElementById("attr_submit_btn").disabled = false;
      }
    };
    document.getElementById("measurement_form").onsubmit = async function (e) {
      e.preventDefault();
      var formData = new FormData(this);
      const uploadResponse = await axios({
        method: "post",
        url: process.env.VUE_APP_CLINICALURL + "/post/measurement",
        data: formData,
        withCredentials: true,
      });
      if (uploadResponse.data["message"] == "ok") {
        M.toast({
          html:
            "You added a measurement for: " +
            document.getElementById("location").value,
        });
        this.reset();
      } else {
        console.error("Somethong went wrong...");
      }
    };
  },
  updated() {},
};
</script>

<style scoped>
.error_message {
  color: red;
}
</style>