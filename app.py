from flask import Flask, jsonify, abort, request, make_response, url_for, send_file
import json
import sys
import calc_pops
from io import BytesIO

app = Flask(__name__)


@app.route('/rst/calcpops', methods=['POST', 'GET'])
def calcpops_radius():
    print('Start')
    inp_address = request.args.get('address')
    inp_radius = request.args.get('radius')
    inp_area = request.args.get('area')

    pops_data = calc_pops.PopsDataObj()
    pops_data.compile_data(inp_address, inp_radius, inp_area)
    pops_data.compile_xls(BytesIO())

    return send_file(
        pops_data.xls_output,
        attachment_filename=pops_data.filename,
        as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
