import argparse
import sys
from pathlib import Path
import yaml
import requests


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='Save Datasources',
        description=('Load datasources from Grafana and save them to a file '
                     'which will be used if Grafana volumes are deleted.')
    )
    parser.add_argument('--host', '-H', type=str, default='localhost')
    parser.add_argument('--port', '-P', type=int, default=3000)
    parser.add_argument('--user', '-u', type=str, default='admin')
    parser.add_argument('--password', '-p', type=str, default='admin')
    args = parser.parse_args()

    url = 'http://{}:{}@{}:{}/api/datasources'.format(
        args.user, args.password, args.host, args.port
    )

    basedir = Path(__file__).parent.parent
    config_path = basedir / 'provisioning/datasources/automatic.yml'
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print('Error while retrieving datasources: {}'.format(e))
        sys.exit(1)

    config = {
        'apiVersion': 1,
        'datasources': response.json()
    }
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
