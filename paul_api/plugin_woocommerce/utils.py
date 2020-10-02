import json

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# from json_to_csv import json_to_csv

DEFAULT_TIMEOUT = 20  # seconds


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def flatten_sub_obj(src, key, subkeys=None):
    subobj = src[key]
    if subkeys is None:
        subkeys = subobj.keys()
    return {f"{key}_{subkey}": subobj[subkey] for subkey in subkeys}


def transform_customers(data):
    ROOT_KEYS = {
        "id",
        "date_created",
        "date_modified",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_paying_customer",
    }

    customers = []

    for item in data:
        entry = {k: item[k] for k in ROOT_KEYS}

        entry.update(
            flatten_sub_obj(
                item,
                "shipping",
            )
        )
        entry.update(
            flatten_sub_obj(
                item,
                "billing",
            )
        )

        consent = [
            element["value"]
            for element in item["meta_data"]
            if element["key"] == "mailchimp_woocommerce_is_subscribed"
        ]
        entry["mailchimp_consent"] = True if consent else False

        customers.append(entry)

    return customers


def transform_subscriptions(data):
    ROOT_KEYS = {
        "billing_interval",
        "billing_period",
        "cart_hash",
        "created_via",
        "currency",
        "customer_id",
        "customer_ip_address",
        "customer_note",
        "customer_user_agent",
        "date_completed",
        "date_completed_gmt",
        "date_created",
        "date_modified",
        "date_paid",
        "date_paid_gmt",
        "discount_tax",
        "discount_total",
        "end_date",
        "id",
        "next_payment_date",
        "number",
        "order_key",
        "parent_id",
        "payment_method",
        "payment_method_title",
        "prices_include_tax",
        "resubscribed_from",
        "resubscribed_subscription",
        "shipping_tax",
        "shipping_total",
        "start_date",
        "status",
        "transaction_id",
        "trial_end_date",
        "version",
    }

    subs = []

    for sub in data:
        if sub["line_items"] and len(sub["line_items"]) >= 1:
            for sub_item in sub["line_items"]:
                entry = {k: sub[k] for k in ROOT_KEYS}

                entry["product_id"] = sub_item["product_id"]
                entry["product_name"] = sub_item["name"]
                entry["product_quantity"] = sub_item["quantity"]
                entry["product_price"] = float(sub_item["total"]) + float(sub_item["total_tax"])

                entry.update(
                    flatten_sub_obj(
                        sub,
                        "shipping",
                    )
                )
                entry.update(
                    flatten_sub_obj(
                        sub,
                        "billing",
                    )
                )

                # If there's a wcsg_recipient in any of the meta objects, the subscription is a gift
                if "meta" in sub and sub["meta"]:
                    for meta_obj in sub["meta"]:    
                        if "key" in meta_obj and meta_obj["key"] == "wcsg_recipient":
                            entry["is_gift"] = True
                            entry["gift_recipient_email"] = meta_obj["value"]
                else:
                    entry["is_gift"] = False

                subs.append(entry)

    return subs


def transform_orders(data):
    ROOT_KEYS = {
        "cart_hash",
        "cart_tax",
        "created_via",
        "currency",
        "customer_id",
        "customer_note",
        "date_completed",
        "date_created",
        "date_modified",
        "date_paid",
        "discount_tax",
        "discount_total",
        "id",
        "number",
        "order_key",
        "parent_id",
        "payment_method",
        "payment_method_title",
        "prices_include_tax",
        "shipping_tax",
        "shipping_total",
        "status",
        "total",
        "total_tax",
        "transaction_id",
        "version",
    }

    orders = []

    for order in data:
        if order["line_items"] and len(order["line_items"]) >= 1:
            for order_item in order["line_items"]:
                entry = {k: order[k] for k in ROOT_KEYS}

                entry["product_id"] = order_item["product_id"]
                entry["product_name"] = order_item["name"]
                entry["product_quantity"] = order_item["quantity"]
                entry["product_price"] = float(order_item["total"]) + float(order_item["total_tax"])

                entry.update(
                    flatten_sub_obj(
                        order,
                        "shipping",
                    )
                )
                entry.update(
                    flatten_sub_obj(
                        order,
                        "billing",
                    )
                )

                orders.append(entry)

    return orders


def transform_products(data):
    ROOT_KEYS = {

    }

    products = []

    for product in data:
        entry = {k: product[k] for k in ROOT_KEYS}

        # entry.update(
        #     flatten_sub_obj(
        #         order,
        #         "shipping",
        #     )
        # )
        # entry.update(order["billing"])

        orders.append(entry)

        return orders


def transform_old_memberships(data_memberships, data_users, data_customers):
    ROOT_KEYS = {
        "billing_interval",
        "billing_period",
        "cart_hash",
        "created_via",
        "currency",
        "customer_id",
        "customer_ip_address",
        "customer_note",
        "customer_user_agent",
        "date_completed",
        "date_completed_gmt",
        "date_created",
        "date_modified",
        "date_paid",
        "date_paid_gmt",
        "discount_tax",
        "discount_total",
        "end_date",
        "id",
        "next_payment_date",
        "number",
        "order_key",
        "parent_id",
        "payment_method",
        "payment_method_title",
        "prices_include_tax",
        "resubscribed_from",
        "resubscribed_subscription",
        "shipping_tax",
        "shipping_total",
        "start_date",
        "status",
        "transaction_id",
        "trial_end_date",
        "version",
    }
    subscriptions = []

    for user in data_users:
        null_values = [
            "billing_interval",
            "billing_period",
            "cart_hash",
            "created_via",
            "currency",
            "customer_id",
            "customer_ip_address",
            "customer_note",
            "customer_user_agent",
            "date_completed",
            "date_completed_gmt",
            "date_created",
            "date_modified",
            "date_paid",
            "date_paid_gmt",
            "discount_tax",
            "discount_total",
            "end_date",
            "id",
            "next_payment_date",
            "number",
            "order_key",
            "parent_id",
            "payment_method",
            "payment_method_title",
            "prices_include_tax",
            "resubscribed_from",
            "resubscribed_subscription",
            "shipping_tax",
            "shipping_total",
            "start_date",
            "status",
            "transaction_id",
            "trial_end_date",
            "version",
        ]

        subscription = []

    return subscriptions 

def fetch_all(endpoints):
    base_url = "https://dev.dor.ro/wp-json/wc/"

    http = requests.Session()

    retries = Retry(
        total=10, backoff_factor=4, status_forcelist=[429, 500, 502, 503, 504]
    )

    # mount timeout adapter so that all calls have the same timeout
    adapter = TimeoutHTTPAdapter(timeout=10, max_retries=retries)
    http.mount("https://", adapter)
    http.mount("http://", adapter)

    # the request will raise an exception on 4XX and 5XX
    assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
    http.hooks["response"] = [assert_status_hook]

    params = {"consumer_key": KEY, "consumer_secret": SECRET, "per_page": 50}

    for ep in endpoints:
        ep_name = ep["name"]
        page = ep.get("page") or 1
        data = []
        version = ep["version"]
        mk_url = ep.get("mk_url") or (lambda pg: f"{base_url}{version}/{ep_name}?page={pg}")

        print(f"fetching endpoint {ep_name}...")

        while True:
            if page % 500 == 0:
                with open(f"partial_{page}_{first_file(ep)}", "w") as f:
                    f.write(json.dumps(data, indent=4))
            #url = f"{base_url}{version}/{ep_name}/plans?page={page}"
            url = mk_url(page)
            print(f"from {url}")
            try:
                response = http.get(url, params=params)
            except requests.exceptions.HTTPError as err:
                print(f"{version} {ep_name} {err}")
                break
            except Exception as err:
                print(f"{version} {ep_name} {err}")
                break

            try:
                response_json = response.json()
            except ValueError:
                print(f"{url} did not return a valid JSON")
                break

            print(f"{ep_name}, page {page}:  {len(response_json)}")
            #print(f"json: {json.dumps(response_json, indent=4)}")
            #break

            if len(response_json) > 1:
                data.extend(response_json)
                page += 1
            else:
                break

        # print(f"GOT JSON for {ep_name}")
        # print(json.dumps(data, indent=4))
        print(f"done fetching {ep_name}")
        with open(first_file(ep), "w") as f:
            f.write(json.dumps(data, indent=4))

def fancy_filter(in_file, out_file, fun):
    with open(in_file, "r") as f:
        data = json.loads(f.read())

    customers = fun(data)
    with open(out_file, "w") as f:
        f.write(json.dumps(customers, indent=4))


def first_file(endpoint):
    return f"{endpoint['version']}_{endpoint['name']}.json"


def processed_file(endpoint):
    return f"FINAL_{endpoint['name']}.json"


def csv_file(endpoint):
    return f"FINAL_{endpoint['name']}.csv"


def do_transforms(endpoints):
    for ep in endpoints:
        if "transform" not in ep:
            continue
        src = first_file(ep)
        dst = processed_file(ep)

        fancy_filter(src, dst, ep["transform"])
        json_to_csv(dst, csv_file(ep))

def get_data(filename):
    with open(filename, "r") as f:
        data = json.loads(f.read())

    return data

def list_to_dict(data, field):
    new_data = {x[field]: x for x in data}

    return new_data


base_url = "https://dev.dor.ro/wp-json/wc/"
ENDPOINTS = [
    {
        "name": "orders",
        "version": "v1",
        "transform": transform_orders,
    },
    {
        "name": "subscriptions",
        "version": "v1",
        "transform": transform_subscriptions
    },
    # {
    #     "name": "customers",
    #     "version": "v3",
    #     "transform": transform_customers,
    # },
    # {
    #     "name": "users",
    #     "version": "v2",
    #     "mk_url":  lambda pg: f"https://dev.dor.ro/wp-json/wp/v2/users?page={pg}"
    # },
    # {
    #     "name": "membership_plans",
    #     "version": "v3",
    #     "mk_url": lambda pg: f"{base_url}v3/memberships/plans?page={pg}"
    # },
    # {
    #     "name": "membership_members",
    #     "version": "v3",
    #     "mk_url": lambda pg: f"{base_url}v3/memberships/members?page={pg}"
    # },
    # {
    #     "name": "products",
    #     "version": "v3",
    # },
]


def run_sync(endpoint_url, key, secret):
    '''
    Do the actual sync.

    Return success (bool), updates(json), errors(json)
    '''
    success = True
    updates = {
        'Utilizatori': {
            'new_rows': 15,
            'updated_rows': 4555
        }
    }
    errors = {
        'Abonamente': {
            'errors_number': 15,
            'errors': {}
        }
    }
    return success, updates, errors
