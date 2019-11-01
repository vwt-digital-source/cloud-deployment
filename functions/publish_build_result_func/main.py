import base64
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
        print('Buildstatus {}'.format(buildstatusmessage))
        publisher = pubsub_v1.PublisherClient()

        # Publish to Pub/Sub topic
        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=os.environ['TOPIC_PROJECT_ID'],
            topic=os.environ['TOPIC_NAME'],
        )
        publisher.publish(topic_name, bytes(buildstatusmessage.encode('utf-8')))
