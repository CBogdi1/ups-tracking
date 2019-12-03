import datetime
import requests

from enum import Enum

USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36')
TRACK_STATUS_URL = "https://www.ups.com/track/api/Track/GetStatus?loc=en_US"

class TrackingStage(Enum):
    ORDER_RECEIVED = 1
    SHIPPED = 2
    IN_TRANSIT = 3
    IN_DELIVERY = 8
    DELIVERY_ATTEMPTED = 9
    DELIVERED = 10

TRACKING_STAGES = {
    'cms.stapp.orderReceived': TrackingStage.ORDER_RECEIVED.value,
    'cms.stapp.shipped': TrackingStage.SHIPPED.value,
    'cms.stapp.inTransit': TrackingStage.IN_TRANSIT.value,
    'cms.stapp.delivery': TrackingStage.IN_DELIVERY.value,
    'cms.stapp.delAttpted': TrackingStage.DELIVERY_ATTEMPTED.value,
    'cms.stapp.delivered': TrackingStage.DELIVERED.value,
    None: TrackingStage.IN_TRANSIT
}

def get_tracking_status(tracking_id: str):
    payload = {
        "Locale": "en_US",
        "TrackingNumber": [tracking_id]
    }
    headers = {
        'User-Agent': USER_AGENT
    }

    r = requests.post(TRACK_STATUS_URL, json = payload, headers = headers)
    r.raise_for_status()

    return r.json()['trackDetails'][0]['shipmentProgressActivities']

def get_activity_status(activity):
    status = (activity['milestone'] or {}).get('name', 'cms.stapp.inTransit')
    return TRACKING_STAGES[status]

def get_activity_timestamp(activity):
    date_time_obj = ''
    if activity['date'] and activity['time']:
        activity_date = activity['date'] + ' ' + activity['time'].lower().replace(' ', '')
        activity_date = activity_date.replace('a.m.', 'AM').replace('p.m.', 'PM')
        date_time_obj = datetime.datetime.strptime(activity_date, "%m/%d/%Y %I:%M%p")
    return date_time_obj

def get_activity_location(activity):
    location_list = activity['location'].split(",")
    location = {
        'city': '',
        'country': ''
    }

    if len(location_list) == 1:
        location['country'] = location_list[0].strip()
    elif len(location_list) == 2:
        location['city'] = location_list[0].strip()
        location['country'] = location_list[1].strip()

    return location

def get_shipment_progress(activities):
    result = []
    for activity in activities:
        location = get_activity_location(activity)

        result.append({
            'stage': get_activity_status(activity),
            'timestamp': get_activity_timestamp(activity),
            'city': location['city'],
            'country': location['country'],
            'description': activity['activityScan'],
        })
    return result


activities = get_tracking_status('1Z0333056857598209')
shipment_progress = get_shipment_progress(activities)
