import Vue from 'vue'
import VueRouter from 'vue-router'
import App from './App.vue'


import axios from 'axios'
import VueAxios from 'vue-axios'
import VueMeta from 'vue-meta'

import { Network } from "vue-vis-network";
Vue.component('network', Network);

import VueEllipseProgress from 'vue-ellipse-progress';

Vue.use(VueEllipseProgress);
Vue.use(VueMeta);

import { VuejsDatatableFactory } from 'vuejs-datatable';
 
Vue.use( VuejsDatatableFactory );


Vue.use(VueAxios, axios)
Vue.use(VueRouter);


Vue.config.productionTip = false





// CSS
import 'materialize-css/dist/css/materialize.min.css'
import 'material-design-icons/iconfont/material-icons.css'


// Components
import Welcome from './components/Welcome.vue';
//import DataPointsForm from './components/DataPointsForm.vue'
import DataModelGraph from './components/DataModelGraph.vue'
import DataModelForm from './components/DataModelForm.vue'
import DataModelEdit from './components/DataModelEdit.vue'
import DownloadArea from './components/DownloadArea.vue'
import DataDump from './components/DataDump.vue'
import OWLUpload from './components/OWLUpload.vue'
import DataTable from './components/DataTable.vue'
import DataUpload from './components/DataUpload.vue'
import Metrics from './components/Metrics.vue'
import DataMapper from './components/DataMapper.vue'
import ContactPage from './components/ContactPage.vue'


// Routing
const routes = [{
        path: '/',
        component: Welcome
    },
    {
        path: '/datapoints',
        component: DataUpload
    },
    {
        path: "/contact",
        component: ContactPage
    },
    {
        path: '/datamodel',
        component: DataModelForm
    },
    {
        path: '/graph',
        component: DataModelGraph
    },
    {
        path: '/edit',
        component: DataModelEdit
    },
    {
        path:"/download", 
        component: DownloadArea
    },
    {
        path:"/semantic-dump", 
        component: DataDump
    }
    ,{
        path:"/owl-upload",
        component: OWLUpload
    },
    {
        path: "/table",
        component: DataTable
    },
    {
        path: "/metrics", 
        component: Metrics
    },
    {
        path: "/mapper", 
        component: DataMapper
    }
]

const router = new VueRouter({
    base: "/data-steward/",
    routes: routes,
    mode: 'history'
});

new Vue({
    router: router,
    render: h => h(App),
}).$mount('#app');