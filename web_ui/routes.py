from sys import path
path.append('..')
from web_ui import app
import export
from flask import render_template, flash, redirect, url_for, Response, request
from werkzeug.utils import secure_filename
import logging
import xmltodict
import flask_excel
import datetime
import os


UPLOAD_FOLDER = '/home/panos/configs/'
ALLOWED_EXTENSIONS = set(['txt', 'xml'])


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/choose', methods=['GET', 'POST'])
def choose():
    PAN_CFG_FILE = f'{UPLOAD_FOLDER}current_config.xml'
    try:
        with open(PAN_CFG_FILE, 'r') as f:
            parsed_cfg = xmltodict.parse(f.read())
            pan_cfg = parsed_cfg.get('response', {}).get('result')
            if not pan_cfg:
                pan_cfg = parsed_cfg

        dg_list = [
            a['@name'] for a in pan_cfg['config']
            ['devices']['entry']['device-group']['entry']
            ]
    except FileNotFoundError:
        flash('Please upload a Panorama config XML before attempting to download.')
        return render_template('index.html')
    return render_template('export.html', dg_list=dg_list)        



@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file submitted')
            return redirect(request.url)
        file = request.files['file']

        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(f'{UPLOAD_FOLDER}current_config.xml'))
            flash('File successfully uploaded! Click "Download" to select device-group.')
            return redirect(url_for('index',
                                    filename=filename))
    return render_template('upload.html')

@app.route('/download')
def download():
    PAN_CFG_FILE = f'{UPLOAD_FOLDER}current_config.xml'
    chosen_dg = request.args.get("Device Group")
    with open(PAN_CFG_FILE, 'r') as f:
        parsed_cfg = xmltodict.parse(f.read())
        pan_cfg = parsed_cfg.get('response', {}).get('result')
        if not pan_cfg:
            pan_cfg = parsed_cfg
    print("your chosen dg is: ".upper(), chosen_dg)
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
            src_ip = export.resolve_address(r['source'].get('member'), pan_cfg, chosen_dg)

            # resolve destination address(es)
            dst_ip = export.resolve_address(r['destination'].get('member'), pan_cfg, chosen_dg)

            # Resolve destination port object(s) to a list of ports
            if type(r['service']) == list:
                dport = r['service'][0].get('member')
            else:
                dport = r['service'].get('member')
            dst_port = export.resolve_service(dport, pan_cfg, chosen_dg)

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

    # GENERATE STRING BASED ON CURRENT DATE: YYYYMMDD
    dt_today = datetime.datetime.today()
    today = dt_today.strftime('%Y%m%d')

    # GENERATE AND RETURN XSLS BASED ON list of rows
    return flask_excel.make_response_from_array(rows, "xlsx", file_name="{}_{}".format(chosen_dg,today))
