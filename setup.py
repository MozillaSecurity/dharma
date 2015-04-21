from setuptools import setup

setup(
	name = 'dharma',
	packages = ['dharma'],
	version = '1.0',
	description = 'A generation-based, context-free grammar fuzzer.',
	author = 'Mozilla Security',
	author_email = 'fuzzing@mozilla.com',
	url = 'https://github.com/mozillasecurity/dharma',
	download_url = 'https://github.com/mozillasecurity/dharma/tarball/1.0',
	keywords = ['fuzzer', 'security', 'fuzzing', 'testing'],
	classifiers = [ # https://pypi.python.org/pypi?%3Aaction=list_classifiers
		'Intended Audience :: Developers',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
		'Topic :: Software Development :: Testing',
	]
)
