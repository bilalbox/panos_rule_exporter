# panos_rule_exporter
> Tool for exporting PANOS security rulebase to a spreadsheet with address and service objects resolved

[![MIT License][license-badge]](LICENSE)
[![Circle-CI][circleci-badge]](https://circleci.com/gh/bilalbox/panos_rule_exporter)

This script takes either a Panorama URL or Panorama configuration XML as input as well as device-group name and returns the security rulebase as an Excel spreadsheet with all address and service objects resolved. A sample [Panorama configuration file](tests/get_config_panorama.xml) is included, though you are encouraged to work with your own configuration when testing and extending the script!


## Requirements
- Python 3.6+
- xmltodict
- openpyxl
- requests
- pytz
- pytest

## Usage

Currently you can run the script as-is and it will process the included local [Panorama configuration XML](tests/get_config_panorama.xml). However, you are encouraged to either replace that XML file with one exported from your own Panorama, or pull the configuration live by this code in the main function:
```python
def main():
...
    with open(PAN_CFG_FILE, 'r') as f:
        pan_cfg = xmltodict.parse(f.read())['response']['result']
```

with something like this:
```python
def main():
...
    pan_cfg = xmltodict.parse(get_config(Config.URL, Config.API_KEY))
``` 
 
You'll also need to update the [config.py](utils/config.py) with your Panorama information.


## Contributing

1. Fork it (<https://github.com/bilalbox/panos_rule_exporter/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request


## License

Distributed under the MIT license. See [``LICENSE``](LICENSE) for more information.

<!-- Markdown link & img dfn's -->
[license-badge]: https://img.shields.io/badge/license-MIT-007EC7.svg
[circleci-badge]: https://circleci.com/gh/bilalbox/panos_rule_exporter/tree/circle_ci.svg?style=shield&circle-token=:circle-token
