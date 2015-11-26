#!/usr/bin/python3
# psp.py - Download vote results from website of Lower House of Czech Parliament
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
from parlament import *
import requests

def load_vote(url):
	"""Parse single vote page. Pass URL as argument."""
	r = requests.get(url)
	page = html.fromstring(r.text)
	content = page.xpath("//div[@id='main-content']")

	if len(content) != 1:
		raise RuntimeError('Invalid HTML structure')

	# Parse vote results
	content = content[0]
	keymap = (('yes','li span.flag.yes + a'), ('no','li span.flag.no + a'),
		('absent','li span.flag.not-logged-in + a, li span.flag.excused + a'),
		('abstain','li span.flag.refrained + a'))
	ret = dict()

	for (key, css) in keymap:
		ret[key] = [textcontent(n).strip() for n in content.cssselect(css)]
	return VoteResult(**ret)

def load_steno_page(url, maxcontext = 4, context = [], docname = None, doclinks = []):
	"""Parse one page of lower house session stenoprotocol. Pass page URL as argument."""
	r = requests.get(url)
	page = html.fromstring(r.text)
	content = page.xpath("//div[@id='main-content']")

	if len(content) != 1:
		raise RuntimeError('Invalid HTML structure')

	content = content[0]
	linelist = content.xpath('p')
	bookmark = url
	voteset = set()
	ret = []

	for line in linelist:
		# Blank paragraph, ignore
		if len(textcontent(line).strip()) == 0:
			continue

		# Speech and possible vote link
		if line.attrib.get('align') == 'justify':
			context.append(line)
			linklist = line.xpath('descendant::a[@id]')

			for node in linklist:
				# Link to vote page
				if node.attrib['id'][0].lower() == 'h':
					votenum = int(node.attrib['id'][1:])

					if votenum in voteset:
						continue

					link = html.urljoin(url, node.attrib['href'])
					vote = load_vote(link)
					ret.append(VoteInfo(votenum, link,
						bookmark,
						context[-1-maxcontext:-1],
						vote, docname, doclinks))
					context = []
				# Only a bookmark
				else:
					bookmark = html.urljoin(url, '#'+node.attrib['id'])
		# Topic/document headline
		elif line.attrib.get('align') == 'center':
			doclist = line.xpath('descendant::a')
			docname = textcontent(line).strip().replace('\n', ' ')
			doclinks = []
			context = []

			for link in doclist:
				title = textcontent(link)
				tmplink = html.urljoin(url, link.attrib['href'])
				doclinks.append((title, tmplink))

	# Create argument list for loading next stenoprotocol page
	navlist = content.cssselect('.document-nav a.next')
	if navlist:
		nextargs = {'url': html.urljoin(url, navlist[0].attrib['href']),
			'context': context[-maxcontext:],
			'maxcontext': maxcontext, 'docname': docname,
			'doclinks': doclinks}
	else:
		nextargs = None

	return (ret, nextargs)

def load_steno(url, maxcontext = 4):
	"""Parse stenoprotocol of one entire lower house session. Pass first stenoprotocol page URL as argument."""
	(ret, nextargs) = load_steno_page(url, maxcontext)
	while nextargs:
		(tmp, nextargs) = load_steno_page(**nextargs)
		ret.extend(tmp)
	return ret

# When called directly from command line, download all stenoprotocol URLs
# passed as arguments and print vote results in plaintext and JSON format,
# one lower house session at a time.
if __name__ == '__main__':
	import sys
	for arg in sys.argv[1:]:
		votelist = load_steno(arg)
		for item in votelist:
			print(item)
			print('----------\n')
		print(votes2json(votelist))
