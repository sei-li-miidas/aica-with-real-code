from datetime import datetime
from json import JSONEncoder


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            # Format datetime object to 'YYYY-MM-DD' string
            return obj.strftime("%Y-%m-%d")
        return JSONEncoder.default(self, obj)
