
def generate_config(context):

    resources = []
    outputs = []

    for logsink in logsinks.get('logsinks', []):  # noqa: F821
        logsink_def = {
            'name': logsink['logsinkId'],
            'type': 'gcp-types/logging-v2:{}.sinks'.format(logsink['sourceType']),
            'properties': {
                'sink': logsink['logsinkId'],
                'description': logsink['description'],
                'parent': '{}/{}'.format(logsink['sourceType'], logsink['sourceId']),
                'folder': logsink['sourceId'],
                'filter': logsink.get('filter', ''),
                'uniqueWriterIdentity': True,
                'destination': logsink['destination'],
                'disabled': logsink.get('disabled', "False") == 'True',
                'includeChildren': logsink['includeChildren'] == 'True',
                'bigqueryOptions': {
                    'usePartitionedTables': logsink['usePartitionedTables'] == 'True'
                }
            }
        }
        resources.append(logsink_def)

        outputs.append({
            'name': 'writerIdentity',
            'value': '$(ref.{}.writerIdentity)'.format(logsink['logsinkId'])
        })

    return {'resources': resources, 'outputs': outputs}
