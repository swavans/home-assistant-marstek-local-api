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


## Development

### Testing

This project includes comprehensive unit tests to ensure reliability and maintainability.

### Prerequisites

Install the testing dependencies:

```bash
pip install -r requirements-test.txt
```

### Running Tests

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=custom_components.marstek_local_api --cov-report=html --cov-report=term-missing
```

Run specific test files:

```bash
pytest tests/test_device.py -v
pytest tests/test_sensor.py -v
pytest tests/test_config_flow.py -v
pytest tests/test_init.py -v
```

Run only unit tests (fast):

```bash
pytest -m "unit"
```

Run only integration tests:

```bash
pytest -m "integration"
```

### Test Coverage

The test suite covers:

- **UDP Communication**: Socket handling, timeouts, error recovery
- **Device Management**: Data caching, method handling, throttling
- **Sensor Entities**: State updates, transforms, device info
- **Config Flow**: User input validation, form handling
- **Integration Setup**: Entry loading/unloading, platform forwarding

Current test coverage target is 80%+.

### Code Quality

The project uses several tools to maintain code quality:

```bash
# Check code formatting
black --check custom_components/ tests/

# Format code
black custom_components/ tests/

# Check import sorting
isort --check-only custom_components/ tests/

# Sort imports
isort custom_components/ tests/

# Lint code
flake8 custom_components/ tests/

# Type checking
mypy custom_components/marstek_local_api/
```

### GitHub Actions

The project includes automated testing via GitHub Actions that runs on:

- Push to main/develop branches
- Pull requests to main branch

The workflow tests multiple Python versions (3.11, 3.12) and includes:

- Unit tests with coverage reporting
- Code formatting checks
- Import sorting verification
- Type checking
- Home Assistant component validation
- Integration testing

## Contribute

If you want to contribute feel free too. This is my first home assistant integration and also my first python project.
The API specification can be found in the [Marstek Device Open API documentation](https://eu.hamedata.com/ems/resource/agreement/MarstekDeviceOpenApi.pdf).

When contributing:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass and coverage remains high
5. Run code quality checks
6. Submit a pull request

[hacs-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-link]: https://my.home-assistant.io/redirect/hacs_repository/?owner=swavans&repository=home-assistant-marstek-local-api&category=integration
[config-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[config-link]: https://my.home-assistant.io/redirect/config_flow_start/?domain=marstek_local_api
