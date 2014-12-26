import json
import requests
import pprint
import urllib
import os.path
import sys
import os


def json_get(url, params):
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise RuntimeError("code %d" % resp.status_code)

    resp = json.loads(resp.text)

    return resp


def all_images(username):
    found_images = True
    max_id = None
    while found_images:
        p = {}
        if max_id is not None:
            p['max_id'] = max_id
        items = json_get('http://instagram.com/%s/media/' % username, params=p)['items']

        found_images = len(items) > 0

        for item in items:
            # pprint.pprint(item)

            img_id = item['id']
            img_caption = None
            if 'caption' in item and item['caption'] is not None:
                img_caption = item['caption']['text']
            img_url = item['images']['standard_resolution']['url']

            yield (img_id, img_url, img_caption)

            max_id = img_id


def save_images(username, abs_write_dir):
    for _id, _url, _caption in all_images(username):
        id_encoded = urllib.quote_plus(_id)
        caption_encoded = ''
        if _caption is not None:
            caption_encoded = urllib.quote_plus(_caption.encode('utf8'))
        filename = '%s%s.jpg' % (caption_encoded, id_encoded)

        write_fn = os.path.join(abs_write_dir, filename)

        if not os.path.exists(write_fn):
            jpg_resp = requests.get(_url)
            if jpg_resp.status_code != 200:
                print 'failed %d on %s' % (jpg_resp.status_code, _url)
                continue

            fh = open(write_fn, 'w')

            fh.write(jpg_resp.content)

            fh.close()

            print 'got & wrote file %s (from %s)' % (filename, _url)


if __name__ == '__main__':
    username = sys.argv[1]
    path = sys.argv[2]

    save_images(username, path)
