import json
import logging
from typing import Optional, Union

import requests
from great_expectations.checkpoint.actions import ValidationAction
from great_expectations.core import ExpectationSuiteValidationResult
from great_expectations.core.id_dict import BatchKwargs
from great_expectations.data_context.data_context import DataContext
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
    GeCloudIdentifier,
    ValidationResultIdentifier,
)

logger = logging.getLogger(__name__)


class IFTTTNotificationAction(ValidationAction):
    def __init__(
        self,
        data_context: DataContext,
        webhook_key: str,
        event_name: str,
        notify_on: Optional[str] = "all",
    ):
        super().__init__(data_context)
        self.webhook_key = webhook_key
        self.event_name = event_name
        self.notify_on = notify_on
        assert (
            webhook_key and event_name
        ), "Both webhook_key and event_name must be defined in action config."

    @property
    def webhook(self):
        return f"https://maker.ifttt.com/trigger/{self.event_name}/json/with/key/{self.webhook_key}"

    def _run(
        self,
        validation_result_suite: ExpectationSuiteValidationResult,
        validation_result_suite_identifier: Union[
            ValidationResultIdentifier, GeCloudIdentifier
        ],
        data_asset=None,
        payload=None,
        expectation_suite_identifier: Optional[ExpectationSuiteIdentifier] = None,
        checkpoint_identifier=None,
    ):
        logger.debug("IFTTTNotificationAction.run")

        if validation_result_suite is None:
            logger.warning(
                f"No validation_result_suite was passed to {type(self).__name__} action. Skipping action."
            )
            return

        if not isinstance(
            validation_result_suite_identifier,
            (ValidationResultIdentifier, GeCloudIdentifier),
        ):
            raise TypeError(
                "validation_result_suite_id must be of type ValidationResultIdentifier or GeCloudIdentifier, "
                "not {}".format(type(validation_result_suite_identifier))
            )

        validation_success = bool(validation_result_suite.success)

        if (
            self.notify_on == "all"
            or self.notify_on == "success"
            and validation_success
            or self.notify_on == "failure"
            and not validation_success
        ):
            session = requests.Session()

            expectation_suite_name = validation_result_suite.meta.get(
                "expectation_suite_name", "__no_expectation_suite_name__"
            )
            run_id = validation_result_suite.meta.get("run_id", "__no_run_id__")
            batch_id = BatchKwargs(
                validation_result_suite.meta.get("batch_kwargs", {})
            ).to_id()
            successful_expectations = validation_result_suite.statistics[
                "successful_expectations"
            ]
            evaluated_expectations = validation_result_suite.statistics[
                "evaluated_expectations"
            ]
            if "batch_kwargs" in validation_result_suite.meta:
                data_asset_name = validation_result_suite.meta["batch_kwargs"].get(
                    "data_asset_name", "__no_data_asset_name__"
                )
            elif "active_batch_definition" in validation_result_suite.meta:
                data_asset_name = (
                    validation_result_suite.meta[
                        "active_batch_definition"
                    ].data_asset_name
                    if validation_result_suite.meta[
                        "active_batch_definition"
                    ].data_asset_name
                    else "__no_data_asset_name__"
                )
            else:
                data_asset_name = "__no_data_asset_name__"

            json_payload = {
                "success": validation_success,
                "checkpoint": checkpoint_identifier,
                "expectation_suite_name": expectation_suite_name,
                "data_asset_name": data_asset_name,
                "run_id": run_id.to_json_dict(),
                "batch_id": batch_id,
                "successful_expectations_count": int(successful_expectations),
                "evaluated_expectations_count": int(evaluated_expectations),
            }

            try:
                response = session.post(
                    url=self.webhook,
                    data=json.dumps(json_payload),
                    headers={"Content-Type": "application/json"},
                )
            except requests.ConnectionError:
                logger.warning(
                    "Failed to connect to IFTTT webhook at {url} "
                    "after {max_retries} retries.".format(
                        url=self.webhook, max_retries=10
                    )
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
                    return {
                        "IFTTT_notification_result": "IFTTT notification succeeded."
                    }

        return {"IFTTT_notification_result": "No IFTTT notification sent."}
