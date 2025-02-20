/** @odoo-module **/
import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormController } from '@web/views/form/form_controller';
import { FormRenderer } from '@web/views/form/form_renderer';


var AbstractField = require('web.AbstractField');
var core = require('web.core');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');

var QWeb = core.qweb;
var _t = core._t;
var rpc = require('web.rpc')



const { Component, onMounted, onWillUnmount, onWillUpdateProps, useState } = owl;

export class cusLocController extends FormController {
    setup() {
        super.setup();
    }


    cust_loc_func(){


        const options = {
        enableHighAccuracy: true,
        timeout: 5000,
        maximumAge: 0,
        };

        if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {

          var latitude = position.coords.latitude;
          var longitude = position.coords.longitude;

          var location = latitude + ', ' + longitude;
          var res_id=this.model.root.data.id;
          rpc.query({
                    model: 'res.partner',
                    method: 'update_current_locations',
                    args: [0,res_id,latitude,longitude]
                });
          window.location.reload();
        },
        function(error) {console.log(error);  },
        options);

      } else {
        reject('Geolocation is not supported');
      }
       }
   }

cusLocController.template="droga_pharma.JsFormView";

export class cusLocRenderer extends FormRenderer {
    setup() {

        super.setup();

        onMounted(()=>{

        });

        onWillUpdateProps(async(nextProps)=>{

        });

    }


}

registry.category('views').add('js_form_view', {
    ...formView,
    Controller: cusLocController,
    Renderer: cusLocRenderer,
});

