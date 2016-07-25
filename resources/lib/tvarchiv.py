# -*- coding: UTF-8 -*-
# /*
# *      Copyright (C) 2016 Jose Riha
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */
import urllib
import util
import urllib2
import re
import resolver
from provider import ContentProvider


class TvArchivContentProvider(ContentProvider):
    urls = {'Filmy': 'http://www.tv-archiv.sk/', 'Seriály': 'http://www.tv-archiv.sk/'}

    def __init__(self, username=None, password=None, filter=None, quickparser=False):
        ContentProvider.__init__(self, 'tv-archiv.sk', self.urls['Filmy'],
                                 username, password, filter)

    def __del__(self):
        util.cache_cookies(self.cache)

    def capabilities(self):
        return ['resolve', 'categories', 'search']

    def categories(self):
        result = []
        for name, url in self.urls.items():
            item = self.dir_item()
            item['title'] = name
            item['url'] = url+'|'+name
            result.append(item)
        return result

    def search(self, keyword):
        return self.list_search_results(self.movie_url(
            '/program-search/?search=' + urllib.quote_plus(keyword)))

    def list_search_results(self, url):
        page = util.parse_html(url)

    def list_years(self, url):
        result=[]
        page = util.parse_html(url)
        for link in page.select('div.button-style2.chars-video')[0].select('a'):
            item = self.dir_item()
            item['title'] = link.text
            item['url'] = '#year#'+self._url(link['href'])
            result.append(item)
        return result

    def list_shows(self, url):
        result=[]
        page = util.parse_html(url)
        for showdata in page.select('div.3u'):
            item = self.dir_item()
            item['title'] = showdata.section.text.replace('\n','').replace('\t','')
            image=showdata.section.div['style']
            try:
                image=re.search(r'.*url\("([^"]+)"\).*',image).group(1)
            except:
                image=''
            episodesurl = showdata.section.div['onclick']
            episodesurl = episodesurl.split('=')[-1]
            episodesurl = episodesurl.replace("'",'')
            episodesurl = episodesurl.replace(";",'')

            item['url'] = '#episodes#'+self._url(episodesurl)
            item['img'] = self._url(image)
            result.append(item)
        return sorted(result, key=lambda n:n['title'])

    def list_episodes(self, url):
        result=[]
        page = util.parse_html(url)
        for episodedata in [x for x in page.select('ul.style1 a')]:
            if x.get('class'):
                if not x.get('class')[0] in 'active':
                    continue
            item = self.video_item()
            item['title'] = episodedata.text.replace('\n','').replace('\t','')
            item['url'] = self._url(episodedata['href'])
            result.append(item)
        return result

    def list(self, url):
        if 'Filmy' in url:
            return self.list_years('http://www.tv-archiv.sk/cele-videa?rok=2016')
        if 'Seriály' in url:
            return self.list_shows('http://www.tv-archiv.sk/#filter')
        if url.startswith('#year#'):
            return self.list_movies(url[6:])
        if url.startswith('#episodes#'):
            return self.list_episodes(url[10:])

    def movie_url(self, url):
        return self.urls['Filmy'] + url

    def series_url(self, url):
        return self.urls['Seriály'] + url

    def list_movies(self, url):
        result = []
        page = util.parse_html(url)
        for moviedata in page.select('div.3u'):
            item = self.video_item()
            item['title'] = moviedata.section.h3.text
            item['title'] = item['title'].replace('\t','')
            item['title'] = item['title'].replace('\n','')
            item['url'] = self._url(moviedata.section.a['href'])
            images = moviedata.section.a.div['onmouseenter'].splitlines()
            imagefile=[x for x in images if '.jpg' in x][-1]
            imagefile = imagefile.replace("\t",'')
            imagefile = imagefile.replace("'",'')
            item['img'] = self._url(imagefile)
            result.append(item)
        return sorted(result, key=lambda n:n['title'])

    def resolve(self, item, captcha_cb=None, select_cb=None):
        streams = []
        page = util.parse_html(item['url'])
        pattern = r'\+?"([^"])"\+?'
        link = re.sub(pattern,lambda n:n.group(1),page.find('script',text=re.compile(r'"."')).text)
	link = re.search(r'''(http://[^'"]+)''',link).group(1)
	link = link.replace('\n','')
        if u'mp4' in link:
	    return {'url':link, 'subs':''}
        else:
            result=resolver.findstreams([str(link)])
            return result[0]
