#!/usr/bin/python3
# parlament.py - Data structures and functions for analysing vote results
# Copyright (C) 2015 Martin 'next_ghost' Doucha
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from lxml import html
import json

def textcontent(node):
	"""Helper function which removes HTML markup"""
	return html.tostring(node, method='text', with_tail=False, encoding='unicode')

class VoteResult:
	"""Detailed results of a vote. Just lists of name organized by how they voted."""
	def __init__(self, yes=[], no=[], abstain=[], secret=[], absent=[]):
		self.yes = yes
		self.no = no
		self.abstain = abstain
		self.secret = secret
		self.absent = absent

	def __str__(self):
		tmp = []
		data = (('Pro', self.yes), ('Proti', self.no),
			('Zdrželi se', self.abstain), ('Tajně', self.secret))
		for item in data:
			if item[1]:
				tmp.append('{0} ({1})'.format(item[0], len(item[1])))
				tmp.extend(['- ' + name for name in item[1]])
				tmp.append('')
		return '\n'.join(tmp)

class VoteInfo:
	"""Information about a vote including links, context and results."""
	def __init__(self, order, resultlink, stenolink, context, result,
		topic=None, doclinks=[]):

		self.order = order
		self.resultlink = resultlink
		self.stenolink = stenolink
		self.context = context
		self.result = result
		self.topic = topic
		self.doclinks = doclinks

	def __str__(self):
		tmp = []
		tmp.append('Hlasování {0}: {1}'.format(self.order, self.resultlink))
		tmp.append('Stenozáznam: {0}'.format(self.stenolink))
		if self.topic:
			tmp.append('Téma: {0}'.format(self.topic))

		for (title, link) in self.doclinks:
			tmp.append('Dokument {0}: {1}'.format(title, link))

		tmp.extend([textcontent(line).strip() for line in self.context])
		tmp.append('')
		tmp.append(str(self.result))
		return '\n'.join(tmp)

class JSONVoteEncoder(json.JSONEncoder):
	"""JSON encoder class with support for VoteResult and VoteInfo classes."""
	def default(self, o):
		if isinstance(o, VoteResult):
			return o.__dict__
		if isinstance(o, VoteInfo):
			tmp = dict(o.__dict__)
			tmp['context'] = [textcontent(x).strip() for x in o.context]
			return tmp
		return json.JSONEncoder.default(self, o)

def votes2json(o):
	"""Encode data structures containing VoteInfo and VoteResult objects into JSON."""
	return json.dumps(o, cls=JSONVoteEncoder, sort_keys=True,
		ensure_ascii=False)

# Just some testing output to make sure it works
if __name__ == '__main__':
	from lxml.html import builder as E
	res = VoteResult(['foo','bar'],['baz'],[],['quux','meh','engfeh'])
	tmp = VoteInfo(1, 'http://foo.cz/result', 'http://foo.cz/steno',
		[E.P('Kontext kontext.'), E.P('Kontext.')], res,
		'Dokument 123456', 'http://foo.cz/doc')
	print(str(tmp))
	print(json.dumps(tmp, cls=JSONVoteEncoder, indent=2, sort_keys=True))
