#!/usr/bin/python3
# senat.py - Download vote results from website of Czech Senate
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

	# Autoredirect to the correct page if the URL points to single-result
	# search page
	if not page.cssselect('.openingText'):
		linklist = page.cssselect('table.PE_zebra a.hand')
		if len(linklist) != 1:
			raise RuntimeError('Invalid HTML structure')
		return load_vote(html.urljoin(url, linklist[0].attrib['href']))

	# Parse vote results
	keymap = {'A': 'yes', 'N': 'no', '0': 'absent', 'X': 'abstain',
		'T': 'secret'}
	ret = dict([(key, []) for key in keymap.values()])

	for node in page.cssselect('.mainFull table.PE_zebra td'):
		entry = textcontent(node).strip()
		vote = keymap[entry[0].upper()]
		ret[vote].append(entry[1:].strip().replace('\xa0', ' '))

	return (url, VoteResult(**ret))

def load_steno(url, maxcontext = 4):
	"""Parse stenoprotocol of single senate session. Pass stenoprotocol URL as argument."""
	r = requests.get(url)
	page = html.fromstring(r.text)
	content = page.cssselect('.obal_nahled')

	if len(content) != 1:
		raise RuntimeError('Invalid HTML structure')

	linelist = content[0].cssselect('.stenovystoupeni p')
	bookmark = url
	voteset = set()
	docname = None
	doclink = None
	context = []
	ret = []

	for line in linelist:
		# html.HtmlElement.classes is not yet available in lxml-3.4 :-(
		# Find document number and URL for this vote (if any)
		doctitle = line.xpath("preceding::p[contains(concat(' ',normalize-space(@class),' '),' stenotisk ')][1]")
		if doctitle:
			doctitle = doctitle[0]
			docname = textcontent(doctitle)
			doclist = doctitle.xpath('descendant::a')
			if len(doclist) != 1:
				raise RuntimeError('Weird link to document "{0}"'.format(docname))
			doclink = html.urljoin(url, doclist[0].attrib['href'])

		# Try to find any vote links and load them
		context.append(line)
		votelist = line.cssselect('a.stenohlasovani')

		for vote in votelist:
			link = html.urljoin(url, vote.attrib.get('href'))

			# Skip duplicate vote links
			if link in voteset:
				continue

			voteset.add(link)

			# Find the nearest preceding bookmark (if any)
			anchors = vote.xpath('preceding::a[@name][1]')
			if anchors:
				bookmark = html.urljoin(url, '#'+anchors[0].attrib['name'])
			vote = load_vote(link)
			ret.append(VoteInfo(len(ret)+1, vote[0], bookmark,
				context[-1-maxcontext:-1], vote[1], docname,
				doclink))
			context = []
	return ret

# When called directly from command line, download all stenoprotocol URLs
# passed as arguments and print vote results in plaintext and JSON format,
# one argument at a time.
if __name__ == '__main__':
	import sys
	for arg in sys.argv[1:]:
		votelist = load_steno(arg)
		for item in votelist:
			print(item)
			print('----------\n')
		print(votes2json(votelist))
