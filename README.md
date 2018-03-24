# panos_rule_exporter
> Tool for exporting PANOS security rulebase to a spreadsheet with address and service objects resolved

[![MIT License][license-badge]](LICENSE)

This script takes either a Panorama URL or Panorama configuration XML as input as well as device-group name and returns the security rulebase as an Excel spreadsheet with all address and service objects resolved. A sample [Panorama configuration file](get_config_panorama.xml) is included, though you are encouraged to work with your own configuration when testing and extending the script!


## Requirements
- Python 3.6+
- xmltodict
- ipaddress
- openpyxl
- requests
- pytz

## Usage example

Currently you can run the script as-is and it will process the included local [Panorama configuration XML](get_config_panorama.xml). However, you are encouraged to either replace that XML file with one exported from your own Panorama, or pull the configuration live by uncommenting [this code](https://github.com/bilalbox/panos_rule_exporter/blob/d1c1a7f44658abb4a006e01f1e9f27a602eccfa9/export.py#L232) and updating the [config.py](utils/config.py) with your Panorama information.


## Development setup
- Use your favorite IDE.
- Using Python 3.6 or later.
- There is no automated test-suite.
- Feel free to open issues for any questions or comments.


## Contributing

1. Fork it (<https://github.com/bilalbox/panos_rule_exporterfork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request


## Meta

Nasir Bilal - bilalbox@gmail.com

Distributed under the MIT license. See ``LICENSE`` for more information.

[https://github.com/bilalbox/panos_rule_exporter](https://github.com/bilalbox/panos_rule_exporter)

<!-- Markdown link & img dfn's -->
[license-badge]:   https://img.shields.io/badge/license-MIT-007EC7.svg
