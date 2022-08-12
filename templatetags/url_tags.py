# from django import template
# from furl import furl

# register = template.Library()


# @register.simple_tag()
# def arurl_add(url, **kwargs):
#     arurl = furl(url)
#     return arurl.add(args=kwargs).url


# @register.simple_tag()
# def arurl_get(url, key):
#     arurl = furl(url)
#     return arurl.args[key] if arurl.args.get(key) else ''


# @register.simple_tag()
# def arurl_update(url, **kwargs):
#     arurl = furl(url)
#     for key, value in kwargs.items():
#         arurl.args[key] = value
#     return arurl.url


# @register.simple_tag()
# def arurl_remove(url, params=[]):
#     arurl = furl(url)
#     return arurl.remove(params).url
