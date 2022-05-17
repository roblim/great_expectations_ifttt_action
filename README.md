# great_expectations IFTTT Action
Connect Great Expectations to the IoT with the IFTTT Webhooks service.

## Overview

Validate Data Using a Great Expectations -> Trigger IFTTT Webhook -> Do Something in Physical World 

## Prerequisites
1. Completed the Great Expectations [Getting Started Tutorial](https://docs.greatexpectations.io/docs/tutorials/getting_started/tutorial_overview)
2. Have a working installation of Great Expectations
3. [Configured a Data Context](https://docs.greatexpectations.io/docs/tutorials/getting_started/tutorial_setup#create-a-data-context)
4. [Configured an Expectations Suite](https://docs.greatexpectations.io/docs/tutorials/getting_started/tutorial_create_expectations) 
5. [Configured a Checkpoint](https://docs.greatexpectations.io/docs/guides/validation/checkpoints/how_to_create_a_new_checkpoint)
6. An active [IFTTT](https://ifttt.com/) account

## Steps
### Configure IFTTT:
1. Log in to [IFTTT](https://ifttt.com/) and create a new [Webhook Applet](https://ifttt.com/maker_webhooks). When asked to choose a trigger (the "If This" part), select "Receive a web request with a JSON payload" then provide an event name (e.g. "ge_validation").
2. Optionally, add Queries or Filters to fetch additional data or add conditional logic using the webhook payload (paid Pro+ features). 
3. Next, configure one or more actions (the "Then That" part) using one of the many IFTTT [integrations](https://ifttt.com/explore/services) (e.g. use the Philips Hue integration to flash all your lights red).
4. Once your applet is created, visit the [IFTTT Webhooks](https://ifttt.com/maker_webhooks) page and click the Documentation button to retrieve your webhook key. Make note of this key and the applet event name you selected earlier - they will be used to configure Great Expectations.

### Configure Great Expectations:
1. Clone this repo locally using `git clone git@github.com:roblim/great_expectations_ifttt_action.git`.
2. Copy the `ifttt_action.py` module to the `plugins` directory of your Great Expectations project (default `great_expectations/plugins`). This will allow Great Expectations' plugin system to find and use the custom `IFTTTNotificationAction` class.
3. Select a Checkpoint to trigger your IFTTT applet and open its configuration yml file. Find the `action_list` key and add a new entry for the `IFTTTNotificationAction`. Change the `notify_on` key based on when you would like the applet to be triggered (after all validations, only failures, or only successful). Repeat for other Checkpoints if desired:

```yaml
  - name: my_ifttt_webhook_action
    action:
      class_name: IFTTTNotificationAction
      module_name: ifttt_action
      webhook_key: ${IFTTT_WEBHOOK_KEY}
      event_name: ${APPLET_EVENT_NAME}
      notify_on: all  # failure, or success
```

### Test Things Out

Check if everything is working by running your Checkpoint. One of the quickest ways is using the Great Expectation CLI tool:
`great_expectations run checkpoint <ENTER CHECKPOINT NAME HERE>`. After the Checkpoint completes validating your data, the above configured `IFTTTNotificationAction` will make a POST request to your IFTTT webhook with the following payload structure:

```json
{
    "success": true,
    "checkpoint": "room_temperature",
    "expectation_suite_name": "normal_values",
    "data_asset_name": "123_bush_street_sensor_data",
    "run_id": {
      "run_name": "some_run_name",
      "run_time": "some_run_time"
    },
    "batch_id": "some_id",
    "successful_expectations_count": 10,
    "evaluated_expectations_count": 10
}
```

You can use information found in the payload to modify the behavior of your IFTTT applet or other downstream actions or events.
