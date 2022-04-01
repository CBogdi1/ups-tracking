from pprint import pprint

import requests
import ipdb


class UPSHttpClient(object):
    USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36"
    )
    TRACK_STATUS_URL = "https://www.ups.com/track/api/Track/GetStatus?loc=en_US"

    def get_tracking_status(self, tracking_id: str):
        payload = {"Locale": "en_US", "TrackingNumber": [tracking_id]}
        headers = {"User-Agent": self.USER_AGENT}

        # ipdb.set_trace()

        r = requests.post(self.TRACK_STATUS_URL, json=payload, headers=headers)
        r.raise_for_status()

        return r.json()["trackDetails"][0]["shipmentProgressActivities"]


class ShipmentProgressItem(object):
    def __init__(self, **kwargs):
        self.args = kwargs

    @property
    def location(self):
        return self.args.get("location", default="")


class UPSTrackingService(object):
    def __init__(self, client: UPSHttpClient):
        self.client = client

    @classmehtod
    def make_service(cls):
        return cls(UPSHttpClient())

    def get_shipment_progress(self, tracking_id: str):
        result = self.client.get_tracking_status(tracking_id)
        return (ShipmentProgressItem(**item) for item in result)
