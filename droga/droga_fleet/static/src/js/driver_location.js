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

export class DriverFormController extends FormController {
    setup() {
        super.setup();
    }


    onClickTestJavascript(){
        if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {

          var latitude = position.coords.latitude.toFixed(13);
          var longitude = position.coords.longitude.toFixed(13);


          var location = latitude + ', ' + longitude;
          rpc.query({
                    model:'droga.fleet.request',
                    method:'driver_location',
                    args: [0,location]
                });
        });

      } else {
        reject('Geolocation is not supported');
      }
    }
}



DriverFormController.template="droga_fleet.Driver_location";

export class DriverFormRenderer extends FormRenderer {
    setup() {

        super.setup();

        onMounted(()=>{

        });

        onWillUpdateProps(async(nextProps)=>{

        });

    }


}

registry.category('views').add('driver_location', {
    ...formView,
    Controller: DriverFormController,
    Renderer: DriverFormRenderer,
});


