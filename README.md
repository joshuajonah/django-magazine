# django-magazine

A stub semi-pluggable Django app for managing a simple magazine.

Magazines consist of Issues, each of which contains one or more Articles, which
are by one or more Authors.

This app uses [South](http://south.aeracode.org/) for managing database changes,
so you'll need that to use it. Also, don't use it right now - it's not remotely
finished.

This app depends on [Bleach](https://github.com/jsocol/bleach), for cleaning up
submitted HTML (particularly content pasted in from Microsoft Word.

This app also depends on [lxml](http://lxml.de/), for additional HTML clean-up
(Bleach gets me most the way there, but not quite all the way).

This app requires [Django 1.3](https://docs.djangoproject.com/en/dev/releases/1.3/),
since it depends on the new [`{% with %}`](https://docs.djangoproject.com/en/1.3/ref/templates/builtins/#with)
tag behaviour, and the new [`{% include %}`](https://docs.djangoproject.com/en/1.3/ref/templates/builtins/#include)
behaviour.
