# Introduction

This integration sets up a simple set of sensors for the different domains in the marstek local api.
Your device needs to have the local api activated which can be requested at marstek support. 
For more info see [Marsteks Faq](https://marstek-power.eu/en/Frequently-Asked-Questions?TreeItem=8449281) or ask them directly at [support@marstekenergy.com](email:support@marstekenergy.com)

# Setup

### Step 1: Add Repository to HACS

[![Open your Home Assistant instance and add a custom repository][hacs-badge]][hacs-link]

### Step 2: Install the Integration via HACS

After adding the repository, you need to install the integration.

1.  Go to **HACS** > **Integrations**.
2.  Search for **"Marstek Local API"** and click on it.
3.  Click the **DOWNLOAD** button and wait for the installation to complete.
4.  **Restart Home Assistant** when prompted.

### Step 3 Setup integration

After restarting, you can add and configure the integration.

[![Open your Home Assistant instance and start setting up a new integration.][config-badge]][config-link]

1. Request access to the local api at marstek support (if you haven't done so before)
1. Enable the API after access has been granted
1. Lookup the IP of your device
1. Setup the integration with IP and Port specified in the app
1. Specify which domains you want.
1. Set the scan interval to something that works for your system. Mine seems to stabilize at around once per minute but I've had different days/timings yield different results.

# Functionalities

Currently the integration supports all requests towards the api which includes retrieving the state for the:
- Wifi
- Bluetooth
- Battery
- Solar panels
- Charging Strategy
- Energy Management Stystem

If you only have the smart home battery I would recommend the Charging Strategy or Battery options only. 
Keep in mind that the API seems to fail quite often in the current firmware which is why I currently made the polling rate configurable.
See what works for your device/version but my current setup is 60 seconds which seems to be stable.


# Contribute
If you want to contribute feel free too. This is my first home assistant integration and also my first python project.
The api spec can be found [here](https://eu.hamedata.com/ems/resource/agreement/MarstekDeviceOpenApi.pdf)

[hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-link]: https://my.home-assistant.io/redirect/hacs_repository/?owner=swavans&repository=home-assistant-marstek-local-api&category=integration
[config-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[config-link]: https://my.home-assistant.io/redirect/config_flow_start/?domain=marstek_local_api
