import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from datetime import datetime
import boto3

session = boto3.session.Session()

USERNAME = ''
ICON_EMOJI = ''
WEBHOOK_URL = ""
CHANNEL = ""


class CloudWatchAlarmParser:
    def __init__(self, msg):
        try:
            self.msg = json.loads(msg["Message"])
        except:
            self.msg = msg

        print("msg : ", self.msg)
        self.timestamp_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        self.trigger = self.msg["Trigger"]

        if self.msg['NewStateValue'] == "ALARM":
            self.color = "danger"
        elif self.msg['NewStateValue'] == "OK":
            self.color = "good"

    def __url(self):
        return ("https://console.aws.amazon.com/cloudwatch/home?"
                + urlencode({'region': session.region_name})
                + "#alarmsV2:alarm/"
                + self.msg["AlarmName"]
                )

    def slack_data(self):
        _message = {
            'text': '<!here|here>',
            'attachments': [
                {
                    'title': ":aws: AWS CloudWatch Notification :alarm:",
                    'ts': datetime.strptime(
                        self.msg['StateChangeTime'],
                        self.timestamp_format
                    ).timestamp(),
                    'color': self.color,
                    'fields': [
                        {
                            "title": "Alarm Name",
                            "value": self.msg["AlarmName"],
                            "short": True
                        },
                        {
                            "title": "Alarm Description",
                            "value": self.msg["AlarmDescription"],
                            "short": False
                        },
                        {
                            "title": "Trigger",
                            "value": " ".join([
                                self.trigger["Statistic"],
                                self.trigger["MetricName"],
                                self.trigger["ComparisonOperator"],
                                str(self.trigger["Threshold"]),
                                "for",
                                str(self.trigger["EvaluationPeriods"]),
                                "period(s) of",
                                str(self.trigger["Period"]),
                                "seconds."
                            ]),
                            "short": False
                        },
                        {
                            'title': 'Old State',
                            'value': self.msg["OldStateValue"],
                            "short": True
                        },
                        {
                            'title': 'Current State',
                            'value': self.msg["NewStateValue"],
                            'short': True
                        },
                        {
                            'title': 'Link to Alarm',
                            'value': self.__url(),
                            'short': False
                        }
                    ]
                }
            ]
        }
        return _message


def lambda_handler(event, context):
    sns_message = {}

    start_data = {
        'channel': CHANNEL,
        'text': '새로운 경보가 있습니다.',
        'icon_emoji': ICON_EMOJI,
        'username': USERNAME
    }

    request = Request(
        WEBHOOK_URL,
        data=json.dumps(start_data).encode(),
        headers={'Content-Type': 'application/json'}
    )
    response = urlopen(request)

    try:
        sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    except:
        sns_message = event

    slack_data = {}
    try:
        slack_data = CloudWatchAlarmParser(sns_message).slack_data()
    except:
        print(event)
        slack_data["text"] = "분명 문제가 일어났는데,,,, json 파싱하다가 에러가 났나봐요.\n"
        slack_data["text"] += str(event)

    slack_data["channel"] = CHANNEL
    slack_data["icon_emoji"] = ICON_EMOJI
    slack_data["username"] = USERNAME

    request = Request(
        WEBHOOK_URL,
        data=json.dumps(slack_data).encode(),
        headers={'Content-Type': 'application/json'}
    )

    response = urlopen(request)
    return {
        'statusCode': response.getcode(),
        'body': response.read().decode()
    }


if __name__ == "__main__":
    print(lambda_handler(None, None))
