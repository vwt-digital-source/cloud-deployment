import base64
import logging
import os
from google.cloud import pubsub_v1


def publish_build_result_func(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """

    if 'data' in data:
        buildstatusmessage = base64.b64decode(data['data']).decode('utf-8')
        logging.debug('Buildstatus {}'.format(buildstatusmessage))
        publisher = pubsub_v1.PublisherClient()
        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=os.environ['PUBLISH_PROJECT_ID'],
            topic=os.environ['PUBLISH_TOPIC_NAME'],
        )
        publisher.publish(topic_name, bytes(json.dumps(buildstatusmessage).encode('utf-8')))
