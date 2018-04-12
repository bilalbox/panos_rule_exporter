# panos_rule_exporter
> Tool for exporting PANOS security rulebase to a spreadsheet with address and service objects resolved

[![MIT License](https://img.shields.io/badge/license-MIT-007EC7.svg)](LICENSE)
[![Circle-CI](https://circleci.com/gh/bilalbox/panos_rule_exporter.svg?circle-token=f8d784311a11a51740574e1ea4206054e4d5fd9f)](https://circleci.com/gh/bilalbox/panos_rule_exporter)
[![Travis-CI Status](https://travis-ci.org/bilalbox/panos_rule_exporter.svg)](https://travis-ci.org/bilalbox/panos_rule_exporter)

This script takes either a Panorama URL or Panorama configuration XML as input as well as device-group name and returns the security rulebase as an Excel spreadsheet with all address and service objects resolved. A sample [Panorama configuration file](tests/get_config_panorama.xml) is included, though you are encouraged to work with your own configuration when testing and extending the script!


## Requirements
- xmltodict
- requests
- pytest
- flask
- flask-excel
- pyexcel-xlsx

## Usage

The current recommended usage for this script is via a docker container. You can build your own via the included Dockerfile:
```bash
docker build -t bilalbox/panos_rule_exporter .
```

Or you can pull the pre-built container from docker hub:
```bash
docker pull bilalbox/panos_rule_exporter
```

Then run the container via:
```bash
docker run -i -t -p 5000:5000 --name=test bilalbox/panos_rule_exporter:latest
```
Once the container is running, navigate to the docker host IP address at http://{docker-host}:5000 and you will be able to use the web interface to upload configurations and export firewall policy.


## Contributing

1. Fork it (<https://github.com/bilalbox/panos_rule_exporter/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request
6. Make sure to add yourself to the list of [AUTHORS](AUTHORS)

## License

Distributed under the MIT license. See [``LICENSE``](LICENSE) for more information.
