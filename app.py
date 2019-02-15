from flask import Flask, jsonify, abort, request, make_response, url_for, send_file
import json
import sys
import calc_pops
from io import BytesIO

app = Flask(__name__)


@app.route('/calcpops-area', methods=['POST', 'GET'])
def calcpops_area():
    # inp_json = json.loads(str(request.data, 'utf-8'))
    # print(request.data, file=sys.stderr)
    # inp_address, inp_radius = inp_json['address'], inp_json['radius']
    # print(request.data, file=sys.stderr)
    pass


@app.route('/calcpops', methods=['POST', 'GET'])
def calcpops_radius():
    inp_address = request.args.get('address')
    inp_radius = request.args.get('radius')
    inp_area = request.args.get('area')
    print('inp_area: ', inp_area)
    print('inp_area_type: ', type(inp_area))
    return send_file(
        BytesIO(), attachment_filename='non.txt', as_attachment=True)

    pops_data = calc_pops.PopsDataObj(inp_address, inp_radius, inp_area)
    pops_data.compile_data()
    pops_data.compile_xls(BytesIO())

    return send_file(
        pops_data.xls_output,
        attachment_filename=pops_data.filename,
        as_attachment=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
