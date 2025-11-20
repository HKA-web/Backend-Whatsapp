import logging
import re as regex
from datetime import datetime

import pytz
from django.utils import timezone


def convert(value):
    if value is not None:
        if value.isdigit():
            return int(value)
        elif isinstance(value, datetime):
            return value.replace(tzinfo=pytz.UTC, ).astimezone(timezone.get_current_timezone())
        elif value.lower() in ('true',):
            return True
        elif value.lower() in ('false',):
            return False
        else:
            return value


def stringdict(data):
    results = {}
    for key, value in regex.findall(r'''(\w+)=([\'a-z\s\d\,\*\/]+\'|[\d\.]+|(?i:tru|fals)e)''', data):
        results.update({key: convert(value.replace('\'', '')), })
    return results


def dictstring(data):
    results = []
    for key, value in data.items():
        results.append(f'''{key}='{value}' '''.strip() if isinstance(value, str) else f'''{key}={value} '''.strip())
    return ', '.join(results)


def stringproperties(data):
    properties = []
    for message in data.splitlines():
        if '=' in message:
            properties.append(map(str.strip, message.split('=', 1)))
        if ':' in message:
            properties.append(map(str.strip, message.split(':', 1)))
    return {key: convert(value) for (key, value) in dict(properties).items()}