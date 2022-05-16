import logging
import requests

from great_expectations.checkpoint.actions import ValidationAction

logger = logging.getLogger(__name__)


class IFTTTNotificationAction(ValidationAction):
    def __init__(self, data_context, webhook, action_if_pass=None, action_if_fail=None):
        super().__init__(data_context)
        self.webhook = webhook
        self.action_if_pass = action_if_pass
        self.action_if_fail = action_if_fail
        assert webhook, "No webhook found in action config."

    def _run(
        self,
        validation_result_suite,
        validation_result_suite_identifier,
        data_asset=None,
        payload=None,
    ):
        if validation_result_suite.success == True:
            self.webhook = self.webhook.replace("{action}", self.action_if_pass)
        else:
            self.webhook = self.webhook.replace("{action}", self.action_if_fail)

        logger.debug("IFTTTNotificationAction.run")

        session = requests.Session()

        try:
            response = session.post(url=self.webhook)
        except requests.ConnectionError:
            logger.warning(
                "Failed to connect to IFTTT webhook at {url} "
                "after {max_retries} retries.".format(url=self.webhook, max_retries=10)
            )
        except Exception as e:
            logger.error(str(e))
        else:
            if response.status_code != 200:
                logger.warning(
                    "Request to IFTTT webhook at {url} "
                    "returned error {status_code}: {text}".format(
                        url=self.webhook,
                        status_code=response.status_code,
                        text=response.text,
                    )
                )
            else:
                return {"IFTTT_notification_result": "IFTTT notification succeeded."}
        return {"IFTTT_notification_result": "No IFTTT notification sent."}
