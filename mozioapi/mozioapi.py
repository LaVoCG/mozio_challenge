import http
import re
import requests
from flask import Flask, json, jsonify, request
from constants import constants
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from jsonschema import validate, ValidationError
from http import HTTPStatus


app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["1 per second"],
    storage_uri="memory://",
)

search_input_schema = {
    "type": "object",
    "properties": {
        "start_address": {"type": "string"},
        "end_address": {"type": "string"},
        "mode": {"type": "string", "enum": ["one_way", "round_trip"]},
        "pickup_datetime": {
            "type": "string",
            # pattern for YYYY-MM-DD HH:mm date format
            "pattern": "[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]"
        },
        "num_passengers": {"type": "integer"},
        "currency": {"type": "string"}
    },
    "required": ["start_address", "end_address", "mode", "pickup_datetime", "num_passengers", "currency"]
}

reservations_input_schema = {
    "type": "object",
    "properties": {
        "result_id": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone_number": {"type": "string"},
        "first_name": {"type": "string"},
        "last_name": {"type": "string"},
        "airline": {"type": "string"},
        "flight_number": {"type": "string"}
    },
    "required": ["result_id", "email", "phone_number", "first_name", "last_name", "airline", "flight_number"]
}

def set_headers():
    return {"Api-Key": constants.API_KEY, "Content-Type": "application/json"}


@app.route('/search/', methods=['POST'])
def api_search():
    """
    This method calls and Mozio API endpoint to perform an

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the resulting data from mozio api call of /v2/search endpoint
    """
    post_data = request.json
    try:
        validate(instance=post_data, schema=search_input_schema)
    except ValidationError as e:
        return jsonify({"status": constants.STATUS_ERROR, "errors": e.message})

    url = f"{constants.BASE_URL}/search/"
    headers = set_headers()
    response = requests.post(url, headers=headers, json=post_data)
    if response.status_code != HTTPStatus.CREATED:
        return jsonify({"status": constants.STATUS_ERROR, "data": json.loads(response.content),
                        "errors": "api_search_poll external API returned unsuccessful response"})
    return jsonify({"status": constants.STATUS_SUCCESS, "message": "api_search completed",
                    "data": json.loads(response.content)}), HTTPStatus.CREATED


@app.route('/search/<search_id>/poll/', methods=['GET'])
@limiter.limit("10/second", override_defaults=True)
def api_search_poll(search_id):
    """
        This method calls and Mozio API endpoint to perform an

        Returns:
            A Flask Response object of type application/json.  The result
            object contains the resulting data from mozio api call of /v2/search endpoint
    """
    if search_id == '':
        return jsonify({"status": constants.STATUS_ERROR, "errors": constants.ERROR_INVALID_SEARCH_ID})
    url = f"{constants.BASE_URL}/search/{search_id}/poll/"

    headers = set_headers()
    response = requests.get(url, headers=headers)
    if response.status_code != HTTPStatus.OK:
        return jsonify({"status": constants.STATUS_ERROR, "data": json.loads(response.content),
                        "errors": "api_search_poll external API returned unsuccessful response"})
    return jsonify({"status": constants.STATUS_SUCCESS, "message": "api_search_poll completed",
                    "data": json.loads(response.content)}), HTTPStatus.OK


@app.route('/reservations/', methods=['POST'])
def api_reservations():

    post_data = request.json
    try:
        validate(instance=post_data, schema=reservations_input_schema)
    except ValidationError as e:
        return jsonify({"status": constants.STATUS_ERROR, "errors": e.message})

    url = f"{constants.BASE_URL}/reservations/"
    headers = set_headers()
    response = requests.post(url, headers=headers, json=post_data)
    if response.status_code != HTTPStatus.CREATED:
        return jsonify({"status": constants.STATUS_ERROR, "data": json.loads(response.content),
                        "errors": "api_reservations external API returned non valid response"})
    return jsonify({"status": constants.STATUS_SUCCESS, "message": "api_reservations completed",
                    "data": json.loads(response.content)}), HTTPStatus.CREATED


@app.route('/reservations/<search_id>/poll/', methods=['GET'])
@limiter.limit("10/second", override_defaults=False)
def api_reservations_poll(search_id):
    if search_id == '':
        return jsonify({"status": constants.STATUS_ERROR, "errors": constants.ERROR_INVALID_SEARCH_ID})
    url = f"{constants.BASE_URL}/reservations/{search_id}/poll/"

    headers = set_headers()
    response = requests.get(url, headers=headers)
    if response.status_code != HTTPStatus.OK:
        return jsonify({"status": constants.STATUS_ERROR, "data": json.loads(response.content),
                        "errors": "api_reservations_poll external API returned non valid response"})

    return jsonify({"status": constants.STATUS_SUCCESS, "message": "api_reservations_poll completed",
                    "data": json.loads(response.content)}), HTTPStatus.OK


@app.route('/reservations/<reservation_id>/', methods=['DELETE'])
def api_reservations_delete(reservation_id):
    if reservation_id == '':
        return jsonify({"status": constants.STATUS_ERROR, "errors": constants.ERROR_INVALID_SEARCH_ID})
    url = f"{constants.BASE_URL}/reservations/{reservation_id}/"

    headers = set_headers()
    response = requests.delete(url, headers=headers)
    if response.status_code != HTTPStatus.ACCEPTED:
        return jsonify({"status": constants.STATUS_ERROR, "data": json.loads(response.content),
                        "errors": "api_reservations_delete external API returned non valid response"})

    return jsonify({"status": constants.STATUS_SUCCESS, "message": "api_reservations_delete completed",
                    "data": json.loads(response.content)}), HTTPStatus.ACCEPTED


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
