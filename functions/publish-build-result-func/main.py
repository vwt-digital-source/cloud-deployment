import base64
from google.cloud import pubsub_v1

def publish_build_result_pubsub(data, context):
    """Background Cloud Function to be triggered by Pub/Sub.
    Args:
         data (dict): The dictionary with data specific to this type of event.
         context (google.cloud.functions.Context): The Cloud Functions event
         metadata.
    """

    if 'data' in data:
        name = base64.b64decode(data['data']).decode('utf-8')
    else:
        name = 'World'
    print('Hello {}!'.format(name))
    publisher = pubsub_v1.PublisherClient()
    topic_name = 'projects/{project_id}/topics/{topic}'.format(
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
        topic='MY_TOPIC_NAME',  # Set this to something appropriate.
    )
    publisher.publish(topic_name, b'My first message!', spam='eggs')


