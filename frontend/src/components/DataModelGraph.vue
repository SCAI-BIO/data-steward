<template>
  <div>
    <br />
    <br />
    <div id="loader">
      <div class="preloader-wrapper big active">
        <div class="spinner-layer spinner-blue-only">
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
      <div id="loader_text">Initializing Network...</div>
    </div>
    <div id="network_div" style="visibility: hidden">
      <!-- Modal Structure -->
      <div id="modal1" class="modal">
        <div class="modal-content" id="modalContent">
          <h4 id="headerModal"></h4>
          <p id="textModal"></p>
        </div>
        <div class="modal-footer">
          <a
            href="#!"
            class="modal-close waves-effect waves-green btn-flat blue-grey lighten-1"
            >Close</a
          >
        </div>
      </div>
      <div id="modal2" class="modal">
        <div class="modal-content" id="modalContent2">
          <h4 id="headerModal2"></h4>
          <p id="textModal2">
            <network
              ref="sub_network"
              :nodes="sub_nodes"
              :edges="sub_edges"
              :options="sub_options"
              :events="['doubleClick', 'oncontext', 'click']"
              @double-click="onNodeClick"
              @oncontext="onContextClickSub"
              @click="generalClick"
            ></network>
          </p>
        </div>
        <div class="modal-footer">
          <a
            href="#!"
            class="modal-close waves-effect waves-green btn-flat blue-grey lighten-1"
            >Close</a
          >
        </div>
      </div>
      <div id="modal_fulltext" class="modal">
        <div class="modal-content">
          <h4>Fulltext Search</h4>
          <p>
            Search through all descriptions, tooltips and definitions of the
            datmodel.
          </p>
          <div class="row">
            <form id="fulltext_form">
              <div class="input-field col s10">
                <input type="text" required name="text" id="fulltext_input" />
              </div>
              <div class="col s2">
                <button class="waves-effect btn blue-grey lighten-1">Go</button>
              </div>
            </form>
          </div>
          <div class="row" id="fulltext_result"></div>
        </div>
      </div>
      <div>
        <div class="row" style="margin-bottom: 3px;">
          <div class="col s4"></div>
          <div class="col s4">
        <h2 style="margin-top: 0" class="center-align">Model Explorer <i class="small material-icons tooltipped" data-position="bottom" :data-tooltip="helpText">help_outline</i></h2>
        </div>
        <div class="col s4 right">
          <button class="waves-effect waves-light btn blue-grey lighten-1" id="hideNavBtn" @click="hideNav()">Hide Navigation</button>
          <button class="waves-effect waves-light btn blue-grey lighten-1 hide" id="showNavBtn" @click="showNav()">Show Navigation</button>
        </div>
        </div>
       

        <div class="row valign-wrapper" id="top_nav_div">
          
          <div class="col s2">
            <button
              @click="disablePhysics"
              class="waves-effect waves-light btn blue-grey lighten-1 left"
            >
              Disable Physics</button
            ><br /><br />
            <button
              @click="enablePhysics"
              class="waves-effect waves-light btn blue-grey lighten-1 left"
            >
              Enable Physics</button
            ><br />
            <br />
            <button
              @click="clusterAll"
              class="waves-effect waves-light btn blue-grey lighten-1 left"
            >
              Close all Clusters</button
            ><br />
          
          </div>

          
          <div class="col s4">
            <div class="row">
              <div class="input-field col s12">
                <i class="material-icons prefix">textsms</i>
                <input
                  type="text"
                  id="autocomplete-input"
                  class="autocomplete"
                />
                <label for="autocomplete-input">Search for Nodes...</label>
              </div>
              <div class="col s12">or</div>
              <br />
              <div class="col s12">
                <div
                  @click="fulltextSearch"
                  class="btn blue-grey lighten-1"
                  id="fulltext_btn"
                >
                  Fulltext Search
                </div>
              </div>
            </div>
          </div>


          <div class="col s6">
             LEGEND
            <table class="striped">
              <thead>
                <tr>
                <th>Clusters and Nodes</th>
                <th>Edges</th>
                </tr>
              </thead>
              <tbody>
                <tr>

                  <td><a
              style="
                background-color: #1d6e88;
                color: white;
                padding-left: 18px;
                padding-right: 18px;
                margin: 4px;
                
              "
              ></a
            >
            = data root groups; internal variables with available mappings
                  </td>
                  <td>

                    <a  style="
                background-color: black;
                color: black;
                padding-left: 18px;
                padding-right: 18px;
                margin: 4px;
              "></a> = part_of <br />
        

                  </td>
                </tr>
                <tr>

                  <td><a
              style="
                background-color: #00bcbd;
                color: black;
                padding-left: 18px;
                padding-right: 18px;
                margin: 4px;
              "
              ></a
            >
            = attributes by sources; external variables</td>
            <td>

                  <a
              style="
                background-color: blue;
                color: white;
                padding-right: 18px;
                padding-left: 18px;
                margin: 4px;
              "
              ></a
            >
            = maps_to

            </td>

                </tr>
                <tr>
                  <td>
                     <a
              style="
                background-color: #c2ad4b;
                color: black;
                padding-left: 18px;
                padding-right: 18px;
                margin: 4px;
              "
              ></a
            >
            = sources

                  </td>
                  <td>
                       <a
              style="
                background-color: gray;
                color: black;
                padding: 4px;
                margin: 4px;
              "
              >dashed</a
            >
            = variable_in
                  </td>
                </tr>
                <tr><td>
                  <a
              style="
                background-color: #c55e2d;
                color: black;
                padding-left: 18px;
                padding-right: 18px;
                margin: 4px;
              "
              ></a
            >
            = root nodes
                  </td></tr>
            

              </tbody>
           
          <br />
         
            
            </table>
          </div>
        </div>
      </div>
      <network class="mynetwork"
        ref="network"
        :nodes="nodes"
        :edges="edges"
        :options="options"
        :events="['doubleClick', 'oncontext', 'click']"
        @double-click="onNodeClick"
        @oncontext="onContextClick"
        @click="generalClick"
      ></network>

      <div class="menu" id="rightClickMenu">
        <ul class="menu-options" id="rightMenuList">
          <component v-if="menuView" :is="menuView"></component>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import ax from "axios";
const axios = ax;
import M from "materialize-css";

export default {
  name: "graph",
  methods: {
    hideNav: function(){
      document.getElementById("top_nav_div").style.display = "none"; 
      document.getElementById("hideNavBtn").classList.add("hide");
      document.getElementById("showNavBtn").classList.remove("hide");

    },
    showNav: function(){
      document.getElementById("top_nav_div").style.display = "flex";
      document.getElementById("showNavBtn").classList.add("hide");
      document.getElementById("hideNavBtn").classList.remove("hide");
    },

    userKeyboard: function (e) {
      if (e.keyCode == 70 && e.ctrlKey) {
        alert("ctrl F");
      }
    },
    clusterAll: function () {
      // CLUSTERING via TOPICS

      var options_topics = [];
      this.topics_all.forEach(function (topic) {
        var options_topic = {
          joinCondition: function (nodeOptions) {
            //console.log("HALLOHALLO");
            return nodeOptions.cid == topic;
          },
          clusterNodeProperties: {
            id: "cidCluster_" + topic,
            borderWidth: 3,
            shape: "square",

            label: topic,
          },
        };
        options_topics.push(options_topic);
        // console.log(topic + " clustering...");
        // this.$refs.network.cluster(options_topic);
      });
      for (var i = 0; i < options_topics.length; i++) {
        this.$refs.network.cluster(options_topics[i]);
      }

      // CLUSTERING via SOURCES

      var options_sources = [];
      this.sources_all.forEach(function (source) {
        var options_source = {
          joinCondition: function (nodeOptions) {
            //console.log("HALLOHALLO");
            return nodeOptions.cid == source;
          },
          clusterNodeProperties: {
            id: "cidCluster_" + source,
            borderWidth: 3,
            shape: "square",
            label: source,
            color: {
              background: "#c2ad4b",
              border: "#c2ad4b"
            },
          },
        };
        options_sources.push(options_source);
        // console.log(topic + " clustering...");
        // this.$refs.network.cluster(options_topic);
      });
      for (var p = 0; p < options_sources.length; p++) {
        this.$refs.network.cluster(options_sources[p]);
      }
    },
    generalClick: function () {
      const menu = document.getElementById("rightClickMenu");
      if (menu.style.display == "block") {
        menu.style.display = "none";
      }
    },
    onContextClickSub: function (params) {
      document.getElementById("rightMenuList").innerHTML = "";
      if (params.nodes.length == 1) {
        const e = params.event;
        e.preventDefault();

        const menu = document.getElementById("rightClickMenu");
        var pagex = e.pageX;
        var pagey = e.pageY;
        menu.style.left = `${pagex}px`;
        menu.style.top = `${pagey}px`;
        menu.style.display = "block";
        document.getElementById("rightMenuList").innerHTML = "";

        if (this.$refs.network.isCluster(params.nodes[0])) {
          console.error("cluster occured in sub graph...");
        } else {
          ["Inspect", "Show more in OLS"].forEach((s) => {
            var listelemNode = document.createElement("li");
            listelemNode.classList.add("menu-option");
            var btn = document.createElement("button");
            btn.classList.add("btn");
            btn.classList.add("waves-effect");
            btn.classList.add("blue-grey", "lighten-1");
            btn.style.height = "auto";
            btn.style.width = "auto";
            btn.style.margin = "2px";
            var textNode = document.createTextNode(s);
            if (s == "Inspect") {
              btn.onclick = function () {
                var getParams = {};
                if (params.nodes[0].startsWith("attr_")) {
                  getParams["type"] = "attribute";
                  getParams["node"] = params.nodes[0].replace("attr_", "");
                } else if (params.nodes[0].startsWith("sources_")) {
                  getParams["type"] = "source";
                  getParams["node"] = params.nodes[0].replace("sources_", "");
                } else {
                  getParams["type"] = "core";
                  getParams["node"] = params.nodes[0];
                }
                const attributeInformation = axios.get(
                  process.env.VUE_APP_CLINICALURL + "/get/attribute",
                  { params: getParams }
                );

                attributeInformation.then((data) => {
                  var elem = document.getElementById("modal1");
                  var instance = M.Modal.getInstance(elem);
                  var modalHeader = document.getElementById("headerModal");

                  modalHeader.textContent =
                    "Variable Name: " + getParams["node"];
                  var modalText = document.getElementById("textModal");
                  modalText.innerHTML = "";

                  if (data["data"]["information"] == "none") {
                    modalText.appendChild(
                      document.createTextNode(
                        "No information available in Clinical Backend..."
                      )
                    );
                    menu.style.display = "none";
                    instance.open();
                  } else {
                    var data_as_json = JSON.parse(
                      data["data"]["information"]
                    )[0]["fields"];

                    var keys = Object.keys(data_as_json);

                    var tbl = document.createElement("table");
                    tbl.style.width = "100%";
                    tbl.setAttribute("border", "1");
                    var tbdy = document.createElement("tbody");
                    keys.forEach(function (value) {
                      var row = document.createElement("tr");
                      var cell1 = document.createElement("td");
                      var cell2 = document.createElement("td");
                      cell1.appendChild(document.createTextNode(value));

                      cell2.appendChild(
                        document.createTextNode(data_as_json[value])
                      );
                      row.appendChild(cell1);
                      row.appendChild(cell2);
                      tbdy.appendChild(row);
                    });

                    tbl.appendChild(tbdy);

                    modalText.appendChild(tbl);
                    menu.style.display = "none";
                    instance.open();
                  }
                });
                //console.log(attributeInformation);
              };
            }
            if (s == "Show more in OLS") {
              btn.onclick = function () {
                window.open(
                  process.env.VUE_APP_OLSURL +
                    "search?q=" +
                    params.nodes[0].replace("attr_", ""),
                  "popUpWindow",
                  "height=800,width=1200,left=10,top=10,,scrollbars=yes,menubar=no"
                );
                return false;
              };
            }

            btn.appendChild(textNode);
            listelemNode.appendChild(btn);
            menu.firstChild.appendChild(listelemNode);
          });
        }
      } else {
        if (params.edges.length == 1) {
          var btn = document.createElement("button");
          var edge = params.edges[0];
          const e = params.event;
          e.preventDefault();

          const menu = document.getElementById("rightClickMenu");
          pagex = e.pageX;
          pagey = e.pageY;
          menu.style.left = `${pagex}px`;
          menu.style.top = `${pagey}px`;
          menu.style.display = "block";
          document.getElementById("rightMenuList").innerHTML = "";
          const netw = this.$refs.network;
          var listelemNode = document.createElement("li");
          listelemNode.classList.add("menu-option");
          btn = document.createElement("button");
          btn.classList.add("btn");
          btn.classList.add("waves-effect");
          btn.classList.add("blue-grey", "lighten-1");
          btn.style.height = "auto";
          btn.style.width = "auto";
          btn.style.margin = "2px";
          var s = "Inspect";
          var textNode = document.createTextNode(s + " Edge");
          if (s == "Inspect") {
            btn.onclick = async function () {
              var getParams = {};
              var connectedNodes = netw.getConnectedNodes(edge);
              if (
                connectedNodes[0].toLowerCase().includes("cluster") ||
                connectedNodes[1].toLowerCase().includes("cluster")
              ) {
                M.toast({
                  html: "Please Open the cluster before inspecting edges!",
                });
                return;
              }
              if (
                connectedNodes[0].toLowerCase().includes("source") ||
                connectedNodes[1].toLowerCase().includes("source")
              ) {
                M.toast({
                  html:
                    "Mappings of type 'part_of' do not contain more information!",
                });
                return;
              }
              getParams["attr_1"] = connectedNodes[0].replace("attr_", "");
              getParams["attr_2"] = connectedNodes[1].replace("attr_", "");

              //console.log(connectedNodes);

              const attributeMappingInformation = await axios.get(
                process.env.VUE_APP_CLINICALURL + "/get/attribute-mapping",
                { params: getParams }
              );
              //console.log(attributeMappingInformation);
              var data = attributeMappingInformation["data"];
              //console.log(data);

              var elem = document.getElementById("modal1");
              var instance = M.Modal.getInstance(elem);
              var modalHeader = document.getElementById("headerModal");

              modalHeader.textContent =
                "Variable Mapping: " +
                getParams["attr_1"] +
                ", " +
                getParams["attr_2"];
              var modalText = document.getElementById("textModal");
              modalText.innerHTML = "";
              if (data["information"] == "none") {
                modalText.appendChild(
                  document.createTextNode(
                    "No information available in Clinical Backend..."
                  )
                );
                menu.style.display = "none";
                instance.open();
              } else {
                var data_as_json = JSON.parse(data["information"])[0]["fields"];

                var keys = Object.keys(data_as_json);

                var tbl = document.createElement("table");
                tbl.style.width = "100%";
                tbl.setAttribute("border", "1");
                var tbdy = document.createElement("tbody");
                keys.forEach(function (value) {
                  var row = document.createElement("tr");
                  var cell1 = document.createElement("td");
                  var cell2 = document.createElement("td");
                  cell1.appendChild(document.createTextNode(value));

                  cell2.appendChild(
                    document.createTextNode(data_as_json[value])
                  );
                  row.appendChild(cell1);
                  row.appendChild(cell2);
                  tbdy.appendChild(row);
                });

                tbl.appendChild(tbdy);

                modalText.appendChild(tbl);
                menu.style.display = "none";
                instance.open();
              }
            };
            btn.appendChild(textNode);
            listelemNode.appendChild(btn);
            menu.firstChild.appendChild(listelemNode);
          }
        } else {
          return;
        }
      }
    },
    onContextClick: function (params) {
      document.getElementById("rightMenuList").innerHTML = "";
      var pagey;
      var pagex;

      if (params.nodes.length == 1) {
        const e = params.event;
        e.preventDefault();

        const menu = document.getElementById("rightClickMenu");
        pagex = e.pageX;
        pagey = e.pageY;
        menu.style.left = `${pagex}px`;
        menu.style.top = `${pagey}px`;
        menu.style.display = "block";
        document.getElementById("rightMenuList").innerHTML = "";
        const netw = this.$refs.network;

        if (this.$refs.network.isCluster(params.nodes[0])) {
          var listelem = document.createElement("li");
          listelem.classList.add("menu-option");
          var text = document.createTextNode("Open this Cluster");
          var btn = document.createElement("button");
          btn.classList.add("btn");
          btn.classList.add("waves-effect");
          btn.classList.add("blue-grey", "lighten-1");
          btn.style.height = "auto";
          btn.style.width = "auto";
          btn.style.margin = "2px";
          btn.onclick = function () {
            netw.openCluster(params.nodes[0]);
            document.getElementById("rightClickMenu").style.display = "none";
          };
          btn.appendChild(text);
          listelem.appendChild(btn);

          menu.firstChild.appendChild(listelem);
        } else {
          ["Inspect", "Open sub graph", "Show more in OLS"].forEach((s) => {
            var listelemNode = document.createElement("li");
            listelemNode.classList.add("menu-option");
            var btn = document.createElement("button");
            btn.classList.add("btn");
            btn.classList.add("waves-effect");
            btn.classList.add("blue-grey", "lighten-1");
            btn.style.height = "auto";
            btn.style.width = "auto";
            btn.style.margin = "2px";
            var textNode = document.createTextNode(s);
            if (s == "Inspect") {
              btn.onclick = function () {
                var getParams = {};
                if (params.nodes[0].startsWith("attr_")) {
                  getParams["type"] = "attribute";
                  getParams["node"] = params.nodes[0].replace("attr_", "");
                } else if (params.nodes[0].startsWith("sources_")) {
                  getParams["type"] = "source";
                  getParams["node"] = params.nodes[0].replace("sources_", "");
                } else {
                  getParams["type"] = "core";
                  getParams["node"] = params.nodes[0];
                }
                const attributeInformation = axios.get(
                  process.env.VUE_APP_CLINICALURL + "/get/attribute",
                  { params: getParams }
                );

                attributeInformation.then((data) => {
                  var elem = document.getElementById("modal1");
                  var instance = M.Modal.getInstance(elem);
                  var modalHeader = document.getElementById("headerModal");

                  modalHeader.textContent =
                    "Variable Name: " + getParams["node"];
                  var modalText = document.getElementById("textModal");
                  modalText.innerHTML = "";

                  if (data["data"]["information"] == "none") {
                    modalText.appendChild(
                      document.createTextNode(
                        "No information available in Clinical Backend..."
                      )
                    );
                    menu.style.display = "none";
                    instance.open();
                  } else {
                    var data_as_json = JSON.parse(
                      data["data"]["information"]
                    )[0]["fields"];

                    var keys = Object.keys(data_as_json);

                    var tbl = document.createElement("table");
                    tbl.style.width = "100%";
                    tbl.setAttribute("border", "1");
                    var tbdy = document.createElement("tbody");
                    keys.forEach(function (value) {
                      var row = document.createElement("tr");
                      var cell1 = document.createElement("td");
                      var cell2 = document.createElement("td");
                      cell1.appendChild(document.createTextNode(value));

                      cell2.appendChild(
                        document.createTextNode(data_as_json[value])
                      );
                      row.appendChild(cell1);
                      row.appendChild(cell2);
                      tbdy.appendChild(row);
                    });

                    tbl.appendChild(tbdy);

                    modalText.appendChild(tbl);
                    menu.style.display = "none";
                    instance.open();
                  }
                });
                //console.log(attributeInformation);
              };
            }
            if (s == "Show more in OLS") {
              btn.onclick = function () {
                window.open(
                  process.env.VUE_APP_OLSURL +
                    "search?q=" +
                    params.nodes[0].replace("attr_", ""),
                  "popUpWindow",
                  "height=800,width=1200,left=10,top=10,,scrollbars=yes,menubar=no"
                );
                return false;
              };
            }
            if (s == "Open sub graph") {
              //const subnetw = this.$refs.sub_network;
              this.sub_nodes = [];
              this.sub_edges = [];
              var sub_n = this.sub_nodes;
              var sub_e = this.sub_edges;
              btn.onclick = function () {
                var node = params.nodes[0];
                var connectedNodes = netw.getConnectedNodes(node);
                connectedNodes.push(node);
                var connectedEdges = netw.getConnectedEdges(node);

                var instance2 = M.Modal.getInstance(
                  document.getElementById("modal2")
                );
                instance2.open();

                connectedNodes.forEach((node) => {
                  var n = netw.getNode(node);
                  if (n != null) {
                    sub_n.push(n);
                  }
                });
                connectedEdges.forEach((edge) => {
                  var ed = netw.getEdge(edge);
                  if (ed != null) {
                    sub_e.push(ed);
                  }
                });

                menu.style.display = "none";
              };
            }

            btn.appendChild(textNode);
            listelemNode.appendChild(btn);
            menu.firstChild.appendChild(listelemNode);
          });
        }
      } else {
        if (params.edges.length == 1) {
          var edge = params.edges[0];
          const e = params.event;
          e.preventDefault();

          const menu = document.getElementById("rightClickMenu");
          pagex = e.pageX;
          pagey = e.pageY;
          menu.style.left = `${pagex}px`;
          menu.style.top = `${pagey}px`;
          menu.style.display = "block";
          document.getElementById("rightMenuList").innerHTML = "";
          const netw = this.$refs.network;
          var listelemNode = document.createElement("li");
          listelemNode.classList.add("menu-option");
          btn = document.createElement("button");
          btn.classList.add("btn");
          btn.classList.add("waves-effect");
          btn.classList.add("blue-grey", "lighten-1");
          btn.style.height = "auto";
          btn.style.width = "auto";
          btn.style.margin = "2px";
          var s = "Inspect";
          var textNode = document.createTextNode(s + " Edge");
          if (s == "Inspect") {
            btn.onclick = async function () {
              var getParams = {};
              var connectedNodes = netw.getConnectedNodes(edge);
              if (
                connectedNodes[0].toLowerCase().includes("cluster") ||
                connectedNodes[1].toLowerCase().includes("cluster")
              ) {
                M.toast({
                  html: "Please Open the cluster before inspecting edges!",
                });
                return;
              }
              if (
                connectedNodes[0].toLowerCase().includes("source") ||
                connectedNodes[1].toLowerCase().includes("source")
              ) {
                M.toast({
                  html:
                    "Mappings of type 'part_of' do not contain more information!",
                });
                return;
              }
              getParams["attr_1"] = connectedNodes[0].replace("attr_", "");
              getParams["attr_2"] = connectedNodes[1].replace("attr_", "");

              //console.log(connectedNodes);

              const attributeMappingInformation = await axios.get(
                process.env.VUE_APP_CLINICALURL + "/get/attribute-mapping",
                { params: getParams }
              );
              //console.log(attributeMappingInformation);
              var data = attributeMappingInformation["data"];
              //console.log(data);

              var elem = document.getElementById("modal1");
              var instance = M.Modal.getInstance(elem);
              var modalHeader = document.getElementById("headerModal");

              modalHeader.textContent =
                "Variable Mapping: " +
                getParams["attr_1"] +
                ", " +
                getParams["attr_2"];
              var modalText = document.getElementById("textModal");
              modalText.innerHTML = "";
              if (data["information"] == "none") {
                modalText.appendChild(
                  document.createTextNode(
                    "No information available in Clinical Backend..."
                  )
                );
                menu.style.display = "none";
                instance.open();
              } else {
                var data_as_json = JSON.parse(data["information"])[0]["fields"];

                var keys = Object.keys(data_as_json);

                var tbl = document.createElement("table");
                tbl.style.width = "100%";
                tbl.setAttribute("border", "1");
                var tbdy = document.createElement("tbody");
                keys.forEach(function (value) {
                  var row = document.createElement("tr");
                  var cell1 = document.createElement("td");
                  var cell2 = document.createElement("td");
                  cell1.appendChild(document.createTextNode(value));

                  cell2.appendChild(
                    document.createTextNode(data_as_json[value])
                  );
                  row.appendChild(cell1);
                  row.appendChild(cell2);
                  tbdy.appendChild(row);
                });

                tbl.appendChild(tbdy);

                modalText.appendChild(tbl);
                menu.style.display = "none";
                instance.open();
              }
            };
            btn.appendChild(textNode);
            listelemNode.appendChild(btn);
            menu.firstChild.appendChild(listelemNode);
          }
        } else {
          return;
        }
      }
    },
    clusterOpenAll: function () {
      for (var node in this.nodes) {
        if (this.$refs.network.isCluster(node) == true) {
          this.$refs.network.openCluster(node);
        }
      }
    },
    onNodeClick: function (params) {
      console.log("Clicked double");
      //console.log("HALLOHALLO");
      if (params.nodes.length == 1) {
        if (this.$refs.network.isCluster(params.nodes[0]) == true) {
          this.$refs.network.openCluster(params.nodes[0]);
        }
      }
    },
    disablePhysics: function () {
      var opts = this.$refs.network["options"];
      opts["physics"]["enabled"] = false;
      this.$refs.network.setOptions(opts);
    },
    enablePhysics: function () {
      var opts = this.$refs.network["options"];
      opts["physics"]["enabled"] = true;
      this.$refs.network.setOptions(opts);
    },
    btnClick: function () {
      var options_topic = {
        joinCondition: function (nodeOptions) {
          //console.log("HALLOHALLO");
          return nodeOptions.cid == this.topics_all[1];
        },
        clusterNodeProperties: {
          id: "cidCluster_" + this.topics_all[1],
          borderWidth: 3,
          shape: "circle",
          label: this.topics_all[1],
        },
      };
      console.log("clustering...");
      this.$refs.network.cluster(options_topic);
    },
    fulltextSearch: function () {
      document.getElementById("fulltext_result").innerHTML = "";
      var network = this.$refs.network;
      var nodes = this.nodes;
      function selectThisNode(nodeId) {
        var findNodesReturn = network.findNode(nodeId);
        if (network.isCluster(findNodesReturn[0])) {
          network.openCluster(findNodesReturn[0]);
          return selectThisNode(nodeId);
        }
        //console.log(nodeId);
        network.focus(nodeId);
        network.selectNodes([nodeId], [true]);
        // console.log(nodes);
        var sel = nodes.find((obj) => {
          return obj["id"] == nodeId;
        });
       
        sel["color"] = {
          background: "red",
        };
        
        network.editNode();
        return;
      }

      var fulltext_modal = M.Modal.getInstance(
        document.getElementById("modal_fulltext")
      );
      fulltext_modal.open();
      document.getElementById("fulltext_input").value = "";
      document.getElementById("fulltext_input").focus();
      document.getElementById("fulltext_form").onsubmit = async function (e) {
        e.preventDefault();

        const fulltextResult = await axios({
          url:
            process.env.VUE_APP_CLINICALURL +
            "/get/fulltext" +
            "?text=" +
            document.getElementById("fulltext_input").value,
        });
        if (
          fulltextResult.status == 200 &&
          fulltextResult["data"]["result"].length > 0
        ) {
          document.getElementById("fulltext_result").innerHTML = "";
          document
            .getElementById("fulltext_result")
            .appendChild(document.createTextNode("Search Results: "));
          fulltextResult["data"]["result"].forEach((result) => {
            var btn = document.createElement("button");
            btn.onclick = function () {
              fulltext_modal.close();
              //console.log(result);
              selectThisNode("attr_" + result);
            };
            btn.classList.add("btn", "waves-effect", "blue-grey", "lighten-1");
            btn.innerHTML = result;
            var row = document.createElement("div");
            row.classList.add("row");
            row.appendChild(btn);
            document.getElementById("fulltext_result").appendChild(row);
          });
        } else {
          document.getElementById("fulltext_result").innerHTML = "";
          document
            .getElementById("fulltext_result")
            .appendChild(document.createTextNode("No Attribute/s Found..."));
        }
      };
    },
  },

  mounted(){
     document.getElementsByClassName("footer-fixed")[0].style.position = "relative";
  },
  async created() {
   

    var elems_tooltip = document.querySelectorAll('.tooltipped');
    M.Tooltip.init(elems_tooltip);
    //document.getElementById('loader_text').innerHTML="Fetching Attributes...";
    const attributes = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attributes/all"
    );
    //document.getElementById('loader_text').innerHTML="Fetching Sources...";
    const sources_all = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/sources/all"
    );
    //document.getElementById('loader_text').innerHTML="Fetching Mappings...";
    const attr_mappings = await axios.get(
      process.env.VUE_APP_CLINICALURL + "/get/attribute-mappings/all"
    );

    var elemsModal = document.querySelectorAll(".modal");
    M.Modal.init(elemsModal);


    for(const t in this.topics_dict){
      if (!this.nodes.filter(e => e.id == this.topics_dict[t]).length > 0) {
  
        console.log("ADDED:" + t);
      
      this.nodes.push(
      {
          id: this.topics_dict[t],
          label: this.topics_dict[t],
          color: {
             background: "#c55e2d",
             border: "#c55e2d"
          },
          fixed: true,

          font: { color: "white" },
        }
    );
    this.edges.push({ from: this.topics_dict[t], to: "root", color: "black" });
      }
  }


    var topics = new Set();
    //console.log(response);
    var attr = attributes["data"]["attributes"];
    //document.getElementById('loader_text').innerHTML="Building graph...";
    for (var k = 0; k < attr.length; k++) {
      //console.log(attr[k]["topic"]);
      topics.add(attr[k]["topic"]);

      this.nodes.push({
        id: "attr_" + attr[k]["name"],
        label: attr[k]["tooltip"],
        cid: attr[k]["topic"],
        color: {
          background: "#1d6e88",
          border: "#1d6e88"
        },
        font: {
          color: "white"
        }
      });
      for(const t in this.topics_dict){
        if(t == attr[k]["topic"]){
          this.edges.push({
            from: "attr_" + attr[k]["name"],
            to: this.topics_dict[t],

            color: "black",
          });
        }
      }
      // switch (attr[k]["topic"]) {
      //   case "Disturbances":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "qualifneurotest",

      //       color: "blue",
      //     });
      //     break;
      //   case "master":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "singular",
      //       label: "part of",

      //       color: "blue",
      //     });
      //     break;
      //   case "NPT":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "neurotest",

      //       color: "blue",
      //     });
      //     break;
      //   case "Blood":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "blood",

      //       color: "blue",
      //     });
      //     break;
      //   case "CSF":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "spinefluid",

      //       color: "blue",
      //     });
      //     break;
      //   case "Ataxia":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "ataxia",
      //       color: "blue",
      //     });
      //     break;
      //   case "SARA scores":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "sara_scores",
      //       color: "blue",
      //     });
      //     break;
      //   case "SARA subscores":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "sara_subscores",
      //       color: "blue",
      //     });
      //     break;
      //   case "SARA":
      //     this.edges.push({
      //       from: "attr_" + attr[k]["name"],
      //       to: "sara",
      //       color: "blue",
      //     });
      //     break;

      //   default:
      //     console.log("No topic found...");
      //}
    }

    var sources = sources_all["data"]["sources"];
    //console.log(response);
    for (var s = 0; s < sources.length; s++) {
      this.nodes.push({
        id: "sources_" + sources[s],
        label: sources[s],
        cid: sources[s],
        fixed: true,
        color: {
          background: "#c2ad4b",
          border: "#c2ad4b"
        },
        highlight: "red",
        font: { color: "black" },
      });
      //TODO add edges
    }
    this.sources_all = Array.from(sources);
    this.topics_all = Array.from(topics);

    var attribute_mappings = attr_mappings["data"]["mappings"];
    for (var d = 0; d < attribute_mappings.length; d++) {
      if (
        !this.nodes.some(
          (node) => node.id == "attr_" + attribute_mappings[d]["name"]
        )
      ) {
        this.nodes.push({
          id: "attr_" + attribute_mappings[d]["name"],
          cid: attribute_mappings[d]["Source"],
          label: attribute_mappings[d]["name"],
          color: {
            background: "#00bcbd",
            border: "#00bcbd",
            highlight: {
              background: "red",
            },
          },

          font: { color: "black" },
        });
      }
      if (
        // check if edge is already set and if not self-map is set
        !this.edges.some(
          (edge) =>
            edge.from == "attr_" + attribute_mappings[d]["name"] &&
            edge.to == "attr_" + attribute_mappings[d]["Target"]
        ) &&
        "attr_" + attribute_mappings[d]["name"] !=
          "attr_" + attribute_mappings[d]["Target"]
      ) {
        this.edges.push({
          from: "attr_" + attribute_mappings[d]["name"],
          to: "attr_" + attribute_mappings[d]["Target"],

          color: "blue",
        });
      }
      this.edges.push({
        to: "sources_" + attribute_mappings[d]["Source"],
        from: "attr_" + attribute_mappings[d]["name"],
        color: "grey",
        dashes: true
      });
    }
    document.getElementById("fulltext_form").onsubmit = function (e) {
      e.preventDefault();
      alert("Not implemented yet...");
    };
    // align fixed nodes on unit circle:
    var _topics = this.nodes.filter((elem) => {
      return elem.fixed && elem.id != "root" && !elem.id.startsWith("sources_");
    });
    var _sources = this.nodes.filter((elem) => {
      return elem.fixed && elem.id.startsWith("sources_");
    });
    console.log(_sources);




    var _z = _sources.length;
    _sources.forEach((s, l) => {
      s.x = Math.round(Math.cos((2 * Math.PI * l) / _z) * 500);
      s.y = Math.round(Math.sin((2 * Math.PI * l) / _z) * 500);
    });
    //console.log(_topics);
    var _k = _topics.length;
    _topics.forEach((t, l) => {
      t.x = Math.round(Math.cos((2 * Math.PI * l) / _k) * 300);
      t.y = Math.round(Math.sin((2 * Math.PI * l) / _k) * 300);
    });
  },
  data() {
    return {
      helpText: "The Datamodel Explorer gives insight about the variables contained in the CCDM (Common Clinical Datamodel) "+
      "You can inspect single nodes by right click or search through the graph via the node search or more advanced the fulltext search. Each edge represents the ralationship between two nodes."
      + " Physics can be enabled and disabled at anytime.",
      update: true,
      topics_dict: {"Demography": "Master", 
               "Organizational": "Master", 
               "Demetia_biomarker": "Master", 
               "Demographics": "Master",
               "Diagnosis": "Master", 
               "Family": "Master", 
               "BNT": "NPT", 
               "FAQ": "NPT", 
               "TMT": "NPT", 
               "CDR": "NPT", 
               "MOCA": "NPT", 
               "GDS": "NPT", 
               "NPI": "NPT", 
               "NPIQ": "NPT", 
               "Memory deficit": "Deficits", 
               "Language deficits": "Deficits", 
               "Executive deficits": "Deficits", 
               "Attention deficits": "Deficits", 
               "Other deficits": "Deficits", 
               "Blood": "Lab", 
               "CSF": "Lab", 
               "Ataxia": "Ataxia",
               "SARA scores": "SARA",
               "Dementia": "Dementia"   
                                      },
      nodes: [
        {
          id: "root",
          label: "The Data Model Root",
          color: {
            background: "#c55e2d",
            border: "#c55e2d"
          },
          fixed: true,
          x: 0,
          y: 0,
          font: { color: "white" },
        },
        // {
        //   id: "site",
        //   label: "SITE",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "pid",
        //   label: "PID",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "ts",
        //   label: "TIMESTAMP",
        //   fixed: true,

        //   color: "DarkViolet",
        //   font: { color: "white" },
        // },
        // {
        //   id: "singular",
        //   label: "Singular Patient information",
        //   //cid: "master",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "blood",
        //   label: "Laboratory measurements in blood",
        //   //cid: "Blood",
        //   fixed: true,

        //   color: "DarkViolet",
        //   font: { color: "white" },
        // },
        // {
        //   id: "spinefluid",
        //   label: "Laboratory measurements in cerebral spine fluid",
        //   //cid: "CSF",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "neurotest",
        //   label: "Neuropsychological test scores",
        //   color: "DarkViolet",
        //   //cid: "NPT",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "qualifneurotest",
        //   label: "Qualifiable neuropsychological disturbances",
        //   color: "DarkViolet",
        //   //cid: "Disturbances",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "ataxia",
        //   label: "Ataxia",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "sara",
        //   label: "SARA",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "sara_subscores",
        //   label: "SARA Subscores",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // {
        //   id: "sara_scores",
        //   label: "SARA Scores",
        //   color: "DarkViolet",
        //   fixed: true,

        //   font: { color: "white" },
        // },
        // // ,{
        // //   id:"sca_characterization",
        // //   label: "SCA CHARACTERIZATION",
        // //   fixed: true,
        // //   x: -210,
        // //   y: -110,
        // //   font: { color: "white" },
        // // }
      ],
      edges: [
        // { from: "site", to: "root", color: "blue" },
        // { from: "spinefluid", to: "root", color: "blue" },
        // { from: "pid", to: "root", color: "blue" },
        // { from: "ts", to: "root", color: "blue" },
        // { from: "blood", to: "root", color: "blue" },
        // { from: "neurotest", to: "root", color: "blue" },
        // { from: "singular", to: "root", color: "blue" },
        // { from: "qualifneurotest", to: "root", color: "blue" },
      ],
      menuView: "",
      options: {
        nodes: {
          borderWidth: 4,
          color: {
            highlight: {
              background: "red",
            },
          },
        },
        edges: {
          color: "lightgray",

          arrows: {
            to: { enabled: true, scaleFactor: 1, type: "arrow" },
          },
        },
        height: (window.innerHeight * 0.9).toString(),
        width: (window.innerWidth * 0.99).toString(),

        physics: {
          enabled: true,
          solver: "barnesHut",
        },
        manipulation: true,
      },
      sub_nodes: [],
      sub_edges: [],
      sub_options: {
        nodes: {
          borderWidth: 4,
        },
        edges: {
          color: "black",

          arrows: {
            to: { enabled: true, scaleFactor: 1, type: "arrow" },
          },
        },
        height: (window.innerHeight * 0.5).toString(),
        physics: {
          enabled: true,
          solver: "barnesHut",
        },
      },
    };
  },
  updated() {
    const this_nodes = this.nodes;
    const network = this.$refs.network;
    function selectThisNode(nodeId) {
      var findNodesReturn = network.findNode(nodeId);
      if (network.isCluster(findNodesReturn[0])) {
        network.openCluster(findNodesReturn[0]);
        return selectThisNode();
      }
      network.focus(nodeId);
      network.selectNodes([nodeId], [true]);
      return;
    }
    if (this.update) {
      document.getElementById("loader_text").innerHTML = "Clustering Nodes...";
      console.log("UPDATING..");

      // NETWORK PROPERTIES
      //console.log(this.topics_all);

      // CORE CLUSTERING
      // var options_core = {
      //   joinCondition: function (nodeOptions) {
      //     return nodeOptions.cid === "core";
      //   },
      //   clusterNodeProperties: {
      //     id: "cidCluster",
      //     borderWidth: 3,
      //     shape: "circle",
      //     label: "Core Model",
      //   },
      // };

      // this.$refs.network.cluster(options_core);

      // CLUSTERING via TOPICS

      var options_topics = [];
      this.topics_all.forEach(function (topic) {
        var options_topic = {
          joinCondition: function (nodeOptions) {
            //console.log("HALLOHALLO");
            return nodeOptions.cid == topic;
          },
          clusterNodeProperties: {
            id: "cidCluster_" + topic,
            borderWidth: 3,
            shape: "square",
            color: {
              background: "#1d6e88",
              border: "#1d6e88"
            },
            label: topic,
          },
        };
        options_topics.push(options_topic);
        // console.log(topic + " clustering...");
        // this.$refs.network.cluster(options_topic);
      });
      for (var i = 0; i < options_topics.length; i++) {
        this.$refs.network.cluster(options_topics[i]);
      }

      // CLUSTERING via SOURCES

      var options_sources = [];
      this.sources_all.forEach(function (source) {
        var options_source = {
          joinCondition: function (nodeOptions) {
            //console.log("HALLOHALLO");
            return nodeOptions.cid == source;
          },
          clusterNodeProperties: {
            id: "cidCluster_" + source,
            borderWidth: 3,
            shape: "square",
            label: source,
            color: {
              background: "#c2ad4b",
              border: "#c2ad4b"
            },
          },
        };
        options_sources.push(options_source);
        // console.log(topic + " clustering...");
        // this.$refs.network.cluster(options_topic);
      });
      for (var p = 0; p < options_sources.length; p++) {
        this.$refs.network.cluster(options_sources[p]);
      }

      let autoCompleteData = {};
      this.nodes.forEach((node) => {
        autoCompleteData[node.label] = null;
      });

      var autoCompleteOptions = {
        data: autoCompleteData,
        onAutocomplete: function (params) {
          var node = this_nodes.find((node) => {
            return node.label == params;
          });

          selectThisNode(node.id);
        },
      };

      var elems = document.querySelectorAll(".autocomplete");
      M.Autocomplete.init(elems, autoCompleteOptions);

      document.getElementById("loader").style = "display: none";

      document.getElementById("network_div").style = "visibility: visible";

      //this.edges = [...new Set(this.edges)];

      //console.log(this.$refs.network);
      // CLUSTERING
      this.update = false;
    } else {
      console.log("prevented updating...");
    }
  },
};
</script>
<style scoped>
.btn.waves-effect {
  height: auto !important;

  min-height: 20px;
  line-height: 20px;
  padding-top: 8px;
  padding-bottom: 8px;
}
.waves-effect.btn {
  height: auto !important;

  min-height: 20px;
  line-height: 20px;
  padding-top: 8px;
  padding-bottom: 8px;
}

.btn {
  height: auto !important;
}

.menu {
  background-color: white;
  z-index: 999999;
  width: 120px;
  box-shadow: 0 4px 5px 3px rgba(0, 0, 0, 0.2);
  position: absolute;
  display: none;
}
.menu .menu-options {
  list-style: none;
  padding: 10px 0;
}
.menu .menu-options .menu-option {
  font-weight: 500;
  font-size: 14px;
  padding: 10px 40px 10px 20px;
  cursor: pointer;
}
.menu .menu-options .menu-option:hover {
  background: rgba(0, 0, 0, 0.2);
  cursor: pointer;
}
li .menu-option:hover {
  cursor: pointer;
}

.mynetwork{
  border: 2px solid black;
  margin-left:5px; 
  margin-right: 5px;
  margin-bottom: 10px

}

</style>