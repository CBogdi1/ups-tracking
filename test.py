import datetime
from collections import OrderedDict
from enum import IntEnum
from contextlib import suppress
from pprint import pprint
from dataclasses import dataclass
from typing import Optional

import requests
import pycountry


class TrackingStage(IntEnum):
    ORDER_RECEIVED = 1
    SHIPPED = 2
    IN_TRANSIT = 3
    IN_DELIVERY = 8
    DELIVERY_ATTEMPTED = 9
    DELIVERED = 10

    @classmethod
    def get_sorted_stages(cls):
        return OrderedDict(sorted(cls.__members__.items(),
                                  key=lambda x: x[1].value))


class TrackingActivity:
    STAGES_MAP = {
        'cms.stapp.orderReceived': TrackingStage.ORDER_RECEIVED,
        'cms.stapp.shipped': TrackingStage.SHIPPED,
        'cms.stapp.inTransit': TrackingStage.IN_TRANSIT,
        'cms.stapp.delivery': TrackingStage.IN_DELIVERY,
        'cms.stapp.delAttpted': TrackingStage.DELIVERY_ATTEMPTED,
        'cms.stapp.delivered': TrackingStage.DELIVERED
    }

    DEFAULT_STAGE = TrackingStage.IN_TRANSIT

    @classmethod
    def get_stage(cls, stage_id):
        if stage_id is None:
            return cls.DEFAULT_STAGE

        try:
            return cls.STAGES_MAP[stage_id]
        except KeyError:
            raise ValueError('Invalid stage ID: %s' % stage_id)

@dataclass
class Location:
    country: str
    city: Optional[str]

class UpsException(Exception):
    pass


class UpsRequestException(UpsException):
    pass


class UpsInvalidTrackingId(UpsException):
    pass


class UpsTrackingClient:
    USER_AGENT = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36')
    TRACK_STATUS_URL = "https://www.ups.com/track/api/Track/GetStatus?loc=en_US"
    DATE_TIME_FORMAT = "%m/%d/%Y %I:%M%p"

    def _get_activity_status(self, activity):
        status = (activity['milestone'] or {}).get('name')
        return TrackingActivity.get_stage(status)

    def _get_activity_timestamp(self, activity):
        date_time_obj = None
        if activity['date'] and activity['time']:
            activity_time = activity['time'].lower().replace(' ', '')
            activity_time = activity_time.replace('a.m.', 'AM').replace('p.m.', 'PM')
            activity_date = f'{activity["date"]} {activity_time}'
            date_time_obj = datetime.datetime.strptime(activity_date, self.DATE_TIME_FORMAT)
        return date_time_obj

    @staticmethod
    def normalize_country_name(name):
        name = name.strip()
        with suppress(LookupError):
            name = pycountry.countries.lookup(name).name
        return name

    def _get_activity_location(self, activity):
        location = {
            'city': None,
            'country': None
        }
        location_str = activity.get('location')
        if not location_str:
            return location

        location_list = location_str.rsplit(",", 1)
        location['country'] = self.normalize_country_name(location_list[-1])

        if len(location_list) == 2:
            location['city'] = location_list[0].strip().capitalize()

        return Location(**location)

    def get_tracking_activities(self, tracking_id):
        payload = {
            "Locale": "en_US",
            "TrackingNumber": [tracking_id]
        }
        headers = {
            'User-Agent': self.USER_AGENT
        }

        try:
            r = requests.post(self.TRACK_STATUS_URL, json=payload, headers=headers)
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UpsRequestException('An error happend while scrapping UPS tracking page. %s' % tracking_id) from e

        try:
            return r.json()['trackDetails'][0]['shipmentProgressActivities']
        except (KeyError, TypeError) as e:
            raise UpsInvalidTrackingId(tracking_id)

    def get_shipment_progress(self, activities):
        return [{
                    'stage': self._get_activity_status(activity),
                    'timestamp': self._get_activity_timestamp(activity),
                    'location': self._get_activity_location(activity),
                    'description': activity['activityScan'],
                }
                for activity in activities]

    def get_result(self, tracking_id):
        activities = self.get_tracking_activities(tracking_id)
        return self.get_shipment_progress(activities)

client = UpsTrackingClient()
activities = client.get_result('1Z0333056857598209')
pprint(activities)
