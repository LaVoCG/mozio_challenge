import pytest
import time
import logging
from constants import constants
from http import HTTPStatus
from mozioapi import mozioapi

search_params = {
    "start_address": "44 Tehama Street, San Francisco, CA, USA",
    "end_address": "SFO: San Francisco, CA - San Francisco",
    "mode": "one_way",
    "pickup_datetime": "2023-12-01 15:30",
    "num_passengers": 2,
    "currency": "USD",
    "campaign": "Lauris Voitešonoks"
}

booking_params = {
    "search_id": "",
    "result_id": "",
    # tested using my own email, submitted to github using this non-existent email, to avoid spam bots finding my email.
    "email": "testingemail@gmail.com",
    "phone_number": "+37122345678",
    "first_name": "Lauris",
    "last_name": "Voitešonoks",
    "airline": "AA",
    "flight_number": "123"
}


@pytest.fixture
def client():
    mozioapi.app.config.update({'TESTING': True})
    with mozioapi.app.test_client() as client:
        with mozioapi.app.app_context():
            pass
            yield client
    # return mozioapi.app.test_client()


def test_search(client):
    # Searching
    logging.info(f'Test Started; Calling search endpoint with these data: \n{search_params}')
    response = client.post('/search/', json=search_params,
                           content_type='application/json')
    resp_json = response.get_json()
    search_result = resp_json['data']
    logging.info(f'search_id: {search_params}\n')

    search_id = search_result['search_id']
    assert response.status_code == HTTPStatus.CREATED
    assert resp_json['status'] == constants.STATUS_SUCCESS

    # Search polling
    url = f"/search/{search_id}/poll/"
    more_coming = True
    poll_results = []
    counter = 0
    while more_coming and counter < 10:
        time.sleep(2)
        response = client.get(url, content_type='application/json')
        resp_json = response.get_json()
        result = resp_json['data']

        try:
            more_coming = result['more_coming']
        except KeyError:
            pass

        poll_results.append(result)
        assert response.status_code == HTTPStatus.OK
        assert resp_json['status'] == constants.STATUS_SUCCESS
        counter += 1

    dummy_provider_results = []
    for res in poll_results:
        for row in res['results']:
            for step in row['steps']:
                if step['details']['provider_name'] == "Dummy External Provider":
                    dummy_provider_results.append(row)

    cheapest_result = dummy_provider_results[0]
    for res in dummy_provider_results:
        if float(res['total_price']['total_price']['value']) < float(cheapest_result['total_price']['total_price']['value']):
            cheapest_result = res

    booking_params['result_id'] = cheapest_result['result_id']
    booking_params['search_id'] = search_id
    logging.info(f"cheapest result_id:{cheapest_result['result_id']}\n")

    # Booking
    response = client.post('/reservations/', json=booking_params,
                           content_type='application/json')

    booking_result = response.get_json()
    assert response.status_code == HTTPStatus.CREATED
    assert booking_result['status'] == constants.STATUS_SUCCESS

    # Booking polling
    reservation_status = "pending"
    url = f"/reservations/{search_id}/poll/"
    reservation = {}
    counter = 0
    while reservation_status == "pending" and counter < 10:
        time.sleep(5)
        response = client.get(url, content_type='application/json')
        resp_json = response.get_json()
        reservation = resp_json['data']
        assert response.status_code == HTTPStatus.OK
        assert resp_json['status'] == constants.STATUS_SUCCESS
        try:
            reservation_status = reservation['status']
        except KeyError:
            reservation_status = "error"
        counter += 1
    logging.info(f"reservation number: {reservation['reservations'][0]['id']}\n")
    logging.info(f"confirmation number: {reservation['reservations'][0]['confirmation_number']}\n")

    # Cancellation
    # according to integration guide - reservation id is used instead of confirmation number
    url = f"/reservations/{reservation['reservations'][0]['id']}/"
    response = client.delete(url, content_type='application/json')
    assert response.status_code == HTTPStatus.ACCEPTED
    assert booking_result['status'] == constants.STATUS_SUCCESS
    logging.info(response.get_json())

