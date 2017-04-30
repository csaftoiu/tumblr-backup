"""Back-up tumblr blogs, even private ones.

Usage:
    tumblr_backup.py list_blogs
    tumblr_backup.py export_blog <blog_url>
"""
import json
import os.path as P
from urlparse import parse_qs

from docopt import docopt

from tumblpy import Tumblpy


def get_tumblpy():
    keyfile = 'keys.json'

    keys = {}
    if P.exists(keyfile):
        print 'Using saved OAuth keys. If there is an error, remove %s' % keyfile
        keys = json.load(open(keyfile))
    else:
        print 'Must complete OAuth steps first'

    save_keys = lambda: json.dump(keys, open(keyfile, 'w'))

    if not keys.get("OAUTH_CONSUMER_KEY"):
        print("Register an app at https://www.tumblr.com/oauth/apps .")
        print("Then input the given keys here.")
        keys['OAUTH_CONSUMER_KEY'] = raw_input("OAuth consumer key: ")
        keys['OAUTH_SECRET_KEY'] = raw_input("OAuth secret key: ")
        save_keys()

    if not keys.get("OAUTH_TOKEN"):
        t = Tumblpy(keys['OAUTH_CONSUMER_KEY'], keys['OAUTH_SECRET_KEY'])

        auth_props = t.get_authentication_tokens(callback_url='http://example.com/')
        auth_url = auth_props['auth_url']

        keys['OAUTH_TOKEN_SECRET'] = auth_props['oauth_token_secret']

        print 'Visit this URL: %s' % auth_url
        print 'Paste the redirect URL here:'
        redirect_url = raw_input('Redirect URL: ')
        res = parse_qs(redirect_url.split("?", 1)[1])
        keys['OAUTH_TOKEN'] = res['oauth_token'][0].split("#")[0]
        keys['OAUTH_VERIFIER'] = res['oauth_verifier'][0].split("#")[0]
        save_keys()

    if not keys.get('FINAL_OAUTH_TOKEN'):
        t = Tumblpy(keys['OAUTH_CONSUMER_KEY'], keys['OAUTH_SECRET_KEY'],
                    keys['OAUTH_TOKEN'], keys['OAUTH_TOKEN_SECRET'])

        authorized_tokens = t.get_authorized_tokens(keys['OAUTH_VERIFIER'])

        keys['FINAL_OAUTH_TOKEN'] = authorized_tokens['oauth_token']
        keys['FINAL_OAUTH_SECRET'] = authorized_tokens['oauth_token_secret']
        save_keys()

        print 'OAuth complete!'

    return Tumblpy(keys['OAUTH_CONSUMER_KEY'], keys['OAUTH_SECRET_KEY'],
                   keys['FINAL_OAUTH_TOKEN'], keys['FINAL_OAUTH_SECRET'])


def export_blog(t, blog_url):
    print("Exporting %s ..." % blog_url)
    res = {}

    res['blog_url'] = blog_url
    res['info'] = t.get('blog/%s/info' % blog_url)
    res['posts'] = []

    total_posts = t.get('posts', blog_url)['total_posts']
    for offset in range(0, total_posts, 20):
        print "(%d/%d)..." % (offset + 1, total_posts)
        these = t.get('posts', blog_url, params={'offset': offset})
        res['posts'].extend(these['posts'])

    fn = '%s.json' % blog_url
    print("Saving to %s" % fn)
    import json
    json.dump(res, open(fn, 'w'))


if __name__ == "__main__":
    args = docopt(__doc__)
    t = get_tumblpy()
    if args['list_blogs']:
        info = t.get('user/info')
        for blog in info['user']['blogs']:
            print("Title: %s" % blog['title'])
            print("URL:   %s" % blog['url'].replace("http://", "")[:-1])
            print
    elif args['export_blog']:
        export_blog(t, args['<blog_url>'])
