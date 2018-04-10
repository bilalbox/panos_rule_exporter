from sys import path
path.append('..')
from web_ui import app
import export
from flask import render_template, Response
import logging
import xmltodict
import flask_excel


PAN_CFG_FILE = 'tests/get_config_panorama.xml'


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/run_it/<chosen_dg>')
def run_it(chosen_dg):
    # Initialize log file for exceptions
    logging.basicConfig(level=logging.INFO, filename='exceptions.log')

    with open(PAN_CFG_FILE, 'r') as f:
        pan_cfg = xmltodict.parse(f.read())['response']['result']

    device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
    dg_tree = [a for a in device_groups if a['@name'] == chosen_dg][0]
    sec_tree = dg_tree['post-rulebase']['security']['rules']['entry']

    # BUILD LIST FOR DUMPING TO WEBPAGE
    rows = list()
    for r in sec_tree:
        try:
            # resolve source address(es)
            src_ip = export.resolve_address(r['source'].get('member'), pan_cfg)

            # resolve destination address(es)
            dst_ip = export.resolve_address(r['destination'].get('member'), pan_cfg)

            # Resolve destination port object(s) to a list of ports
            if type(r['service']) == list:
                dport = r['service'][0].get('member')
            else:
                dport = r['service'].get('member')
            dst_port = export.resolve_service(dport, pan_cfg)

            # Fill out table row with all rule details
            row = (
                str(r['@name']),
                str(r['from'].get('member')),
                str(r['source'].get('member')),
                str(src_ip),
                str(r['to'].get('member')),
                str(r['destination'].get('member')),
                str(dst_ip),
                str(r['application'].get('member')),
                str(r['service'].get('member')),
                str(dst_port),
                str(r['category'].get('member')),
                str(r['action']),
                str(r.get('profile-setting', {}).get('group', {}).get('member', 'none')),
                str(r['log-setting']),
            )
            rows.append(row)
        except BaseException as e:
            logging.exception("UNABLE TO EXPORT RULE {} DUE TO {}".format(r, e))

    return render_template('export.html', title='EXPORT RESULTS', rows=rows, chosen_dg=chosen_dg)


@app.route("/download")
def download():
    chosen_dg = 'child_dg_lab01'
    # Initialize log file for exceptions
    logging.basicConfig(level=logging.INFO, filename='exceptions.log')

    with open(PAN_CFG_FILE, 'r') as f:
        pan_cfg = xmltodict.parse(f.read())['response']['result']

    device_groups = pan_cfg['config']['devices']['entry']['device-group']['entry']
    dg_tree = [a for a in device_groups if a['@name'] == chosen_dg][0]
    sec_tree = dg_tree['post-rulebase']['security']['rules']['entry']

    # BUILD LIST FOR DUMPING TO WEBPAGE
    rows = list()
    rows.append([
        'NAME',
        'FROM',
        'SOURCE',
        'RESOLVED SRC',
        'TO',
        'DESTINATION',
        'RESOLVED DST',
        'APP',
        'SERVICE',
        'RESOLVED PT',
        'CATEGORY',
        'ACTION',
        'PROFILE-SETTING',
        'LOG-SETTING',
    ])
    for r in sec_tree:
        try:
            # resolve source address(es)
            src_ip = export.resolve_address(r['source'].get('member'), pan_cfg)

            # resolve destination address(es)
            dst_ip = export.resolve_address(r['destination'].get('member'), pan_cfg)

            # Resolve destination port object(s) to a list of ports
            if type(r['service']) == list:
                dport = r['service'][0].get('member')
            else:
                dport = r['service'].get('member')
            dst_port = export.resolve_service(dport, pan_cfg)

            # Fill out table row with all rule details
            row = (
                str(r['@name']),
                str(r['from'].get('member')),
                str(r['source'].get('member')),
                str(src_ip),
                str(r['to'].get('member')),
                str(r['destination'].get('member')),
                str(dst_ip),
                str(r['application'].get('member')),
                str(r['service'].get('member')),
                str(dst_port),
                str(r['category'].get('member')),
                str(r['action']),
                str(r.get('profile-setting', {}).get('group', {}).get('member', 'none')),
                str(r['log-setting']),
            )
            rows.append(row)
        except BaseException as e:
            logging.exception("UNABLE TO EXPORT RULE {} DUE TO {}".format(r, e))

    return flask_excel.make_response_from_array(rows, "xlsx")
