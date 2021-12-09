import argparse
import sys
from urllib import request, parse
from urllib.request import urlretrieve
import json
from types import SimpleNamespace
import os
from urllib.parse import urlparse

def MakeJSON(entity):
    return json.dumps(entity, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

def DownloadContent(download_location, xuid, token, media_type):
	if media_type.casefold() == 's':
		DownloadData('screenshots', xuid, download_location, token)
	elif media_type.casefold() == 'v':
		DownloadData('gameclips', xuid, download_location, token)
	else:
		DownloadData('screenshots', xuid, download_location, token)
		DownloadData('gameclips', xuid, download_location, token)

def GetContentEntities(xuid, endpoint, token, continuation_token):
	request_string = ''
	if not continuation_token:
		request_string = f'{{"max":500,"query":"OwnerXuid eq {xuid}","skip":0}}'
	else:
		request_string = f'{{"max":500,"query":"OwnerXuid eq {xuid}","skip":0, "continuationToken": "{continuation_token}"}}'

	screenshot_request = request.Request(f'https://mediahub.xboxlive.com/{endpoint}/search', data = request_string.encode("utf-8"), headers = {'Authorization': token, 'Content-Type': 'application/json'})

	response = request.urlopen(screenshot_request)

	content_entities = None

	if response.getcode() == 200:
		print ('Successfully got content collection.')
		content_entities = json.loads(response.read(), object_hook=lambda d: SimpleNamespace(**d))
	else:
		print('Could not get a successful response from the Xbox Live service.')

	return content_entities

def GetContentEntity(endpoint, xuid, local_id, token):
	request_string = f'{{"max":20,"query":"OwnerXuid eq {xuid} and localId eq \'{local_id}\'","skip":0}}'

	screenshot_request = request.Request(f'https://mediahub.xboxlive.com/{endpoint}/search', data = request_string.encode("utf-8"), headers = {'Authorization': token, 'Content-Type': 'application/json'})

	response = request.urlopen(screenshot_request)

	content_entity = None

	if response.getcode() == 200:
		print ('Successfully got content.')
		content_entity = json.loads(response.read(), object_hook=lambda d: SimpleNamespace(**d))
	else:
		print('Could not get a successful response from the Xbox Live service.')

	return content_entity


def DownloadData(endpoint, xuid, download_location, token, continuation_token = None):
	print(f'Downloading from the {endpoint} endpoint...')

	content_entities = GetContentEntities(xuid, endpoint, token, continuation_token)

	# We just want the local IDs for now to make sure that we know what needs to be
	# downloaded. The URLs here are not used for downloads.
	local_ids = [e.localId for e in content_entities.values] 
	print(f'Obtained {len(local_ids)} content IDs.')

	if not local_ids == None:
		for local_id in local_ids:
			print(f'Currently downloading content with ID: {local_id}')

			entity = GetContentEntity(endpoint, xuid, local_id, token).values[0]

			if entity:
				metadata_path = os.path.join(download_location, entity.contentId + ".json")
				with open(metadata_path, 'w') as metadata_file:
				    metadata_file.write(MakeJSON(entity))
				print(f'Metadata acquisition successful.')

				locator = next((x for x in entity.contentLocators if x.locatorType.casefold() == 'download'))
				locator_ts = next((x for x in entity.contentLocators if x.locatorType.casefold() == 'thumbnail_small'))
				locator_tl = next((x for x in entity.contentLocators if x.locatorType.casefold() == 'thumbnail_large'))

				if locator:
					print(f'Attempting to download content at {locator.uri}...')
					media_path = os.path.join(download_location, os.path.basename(urlparse(locator.uri).path))
					urlretrieve(locator.uri, media_path)

				if locator_ts:
					print(f'Attempting to download small thumbnail at {locator_ts.uri}...')
					media_path = os.path.join(download_location, 'small_' + os.path.basename(urlparse(locator_ts.uri).path))
					urlretrieve(locator_ts.uri, media_path)

				if locator_tl:
					print(f'Attempting to download large thumbnail at {locator_tl.uri}...')
					media_path = os.path.join(download_location, 'large_' + os.path.basename(urlparse(locator_tl.uri).path))
					urlretrieve(locator_tl.uri, media_path)
			else:
				print (f'Could not download entity: {local_id}')
		try:
			DownloadData(endpoint, xuid, download_location, token, content_entities.continuationToken)
		except AttributeError:
			print('No more continuation tokens. Assuming media of requested class is downloaded completely.')
	else:
		print('No content entities to process.')


media_type = 'A'

parser = argparse.ArgumentParser(description = 'Download Xbox Live screenshots and video clips.')

parser.add_argument('DownloadLocation',
                       metavar='dl',
                       type=str,
                       help='Folder where content needs to be downloaded.')

parser.add_argument('XUID',
                       metavar='xuid',
                       type=str,
                       help='Xbox Live numeric user identifier.')

parser.add_argument('Token',
                       metavar='token',
                       type=str,
                       help='XBL 3.0 authorization token.')

parser.add_argument('Media',
                       metavar='media',
                       type=str,
                       help='Type of media to be downloaded. Use S for screenshots, V, for video, or A for all.')

args = parser.parse_args()

if not args.DownloadLocation:
	print('You need to specify a download location.')
	sys.exit()

if not args.XUID:
	print('You need to specify a XUID in order to get screenshots and video clips.')
	sys.exit()

if not args.Token:
	print('You need to specify a XBL 3.0 token in order to get screenshots and video clips.')
	sys.exit()

if not args.Media:
	print('No media parameter specified. Assumed all media needs to be downloaded.')
else:
	media_type = args.Media

DownloadContent(args.DownloadLocation, args.XUID, args.Token, media_type)
print ('Download complete.')


