#!/usr/bin/env python
"""codify-files.py

Have files you want accessible in the binary of your C program?
Codify them with this helper.

Usage:
  codify-files.py <pack-name> <resource>... [options]
  codify-files.py (-h | --help)
  codify-files.py --version

Options:
  -h --help                  Show this screen.
  --version                  Show version.
  --outdir=<outdir>          Where to output the files [default: .]
  --include-prefix=<prefix>  Suffix of outdir that won't be in your project's include path [default: ]
"""
from docopt import docopt
import jinja2, os

HEADER_TEMPLATE="""#ifndef CODIFY_MY_RESOURCE_{{ pack_name|upper }}
#define CODIFY_MY_RESOURCE_{{ pack_name|upper }}

#include <cstdlib>
#include <stdint.h>

{% for resource in resources %}
extern uint8_t {{ resource.name }}[];
const size_t {{ resource.name }}_size={{ resource.bytes|length }};
{% endfor %}

#endif

"""

SOURCE_TEMPLATE="""#include "{% if include_prefix %}{{include_prefix}}/{% endif %}{{pack_name}}.h"

{% for resource in resources %}
uint8_t {{resource.name}}[] = { {% for byte in resource.bytes %}{{byte|to_hex_literal}}, {%endfor%} };
{% endfor %}

"""

def to_hex_literal(my_char): return hex(ord(my_char))

def codify(pack_name, resources, include_prefix=""):
	resources = [
		{
			'name':os.path.basename(d['path']).replace(".","_").replace("-","_"),
			'bytes':d['data'], 
		}
		for d in resources
	]
	context = {
		'pack_name':pack_name,
		'resources':resources,
		'include_prefix':include_prefix
	}

	templates = {'header':HEADER_TEMPLATE, 'source':SOURCE_TEMPLATE}
	env = jinja2.Environment(loader=jinja2.DictLoader(templates))
	env.trim_blocks=True # remove first newline after template tags
	env.filters.update({
		"to_hex_literal":to_hex_literal
		})

	header = env.get_template('header').render(context)
	source = env.get_template('source').render(context)

	return header,source


if __name__ == '__main__':
	arguments = docopt(__doc__, version='Codify My Resource 0.1')

	def read_all_bytes(path):
		with open(path) as f:
			return f.read()

	pack_name = arguments['<pack-name>']
	resources = [
		{'path':path, 'data':read_all_bytes(path) }
		for path in arguments['<resource>']
	]
	include_prefix = arguments['--include-prefix']

	header, source = codify(pack_name, resources, include_prefix)

	outfile_stem = os.path.join(arguments['--outdir'], pack_name)

	with open(outfile_stem + ".h",   "w") as f: f.write(header)
	with open(outfile_stem + ".cpp", "w") as f: f.write(source)