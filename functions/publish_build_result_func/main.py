import base64
import os
import logging

from google.cloud import pubsub_v1
from google.api_core import exceptions as gcp_exceptions

logging.getLogger().setLevel(logging.INFO)


def publish_build_result_func(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """

    if 'data' in data:
        build_status_message = base64.b64decode(data['data']).decode('utf-8')
        logging.info('Build status: {}'.format(build_status_message))
        publisher = pubsub_v1.PublisherClient()

        # Publish to Pub/Sub topic
        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=os.environ['TOPIC_PROJECT_ID'],
            topic=os.environ['TOPIC_NAME'],
        )

        try:
            publisher.publish(topic_name, bytes(build_status_message.encode('utf-8')))
        except gcp_exceptions.PermissionDenied:
            logging.error(
                "The function does not have permission to publish a message towards " +
                f"topic '{topic_name}'")
            pass
        except Exception as e:
            logging.error(f"Failed to publish build status: {str(e)}")
            raise e
