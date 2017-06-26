import pickle
import requests, requests_cache
import os
import re
from bs4 import BeautifulSoup
import difflib 
import logging

DMATOPOURL = 'https://raw.githubusercontent.com/akiatoji/nielsen-dma/master/nielsentopo.json'
GEOIPURL = 'http://freegeoip.net/json'
PICKLEFILENAME = '.geo_cache.p'
DMARANKINGURLS = ['https://www.tvb.org/Public/Research/CompetitiveMedia/CableADS/ADS,Wired-CableandBroadcastOnlyPenetrationbyDMA.aspx', 'https://www.tvb.org/Default.aspx?TabID=1593']
LOGLEVEL = logging.INFO
LOGFORMAT = "[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
CACHEDAYS = 21

requests_cache.install_cache('.geo_cache', backend='sqlite', expire_after=86400*CACHEDAYS)  # cache for 21 days
if LOGLEVEL is not None:
    logging.basicConfig(filename='geodmaip.log',level=LOGLEVEL,format=LOGFORMAT)
    
class GeoDMAIP():
    
    def __init__(self):
        self.error = None
        self.cached = None
        self.dmainfomap = self._getDMAMap()
        if self.error is not None:
            logging.warning(self.error)
        
    def _getRankings(self):
        #definitive list: http://www.nielsen.com/content/dam/corporate/us/en/docs/solutions/measurement/television/2016-2017-nielsen-local-dma-ranks.pdf
        #scraping from tvb.org for convenience.
        data = dict()
        for url in DMARANKINGURLS:
            r = requests.get(url)
            if r.status_code == 200:
                break
        soup = BeautifulSoup(r.text, "lxml")

        try:
            pattern = re.compile('DMA Household Universe Estimates: ([\w\s]+)')
            self.dmarankingsasof = pattern.findall(r.text)[0]
        except:
            self.dmarankingsasof = None

        for line in soup.find_all('tr', {'class': re.compile("^dnn(Grid|GridAlt)Item$")}):
            cells = line.find_all('td')
            #rder    DMA Name    % OTA    % Wired Cable    % ADS
            try:
                data[re.sub(' \(.*\)', '', cells[1].text)] = {'rank': int(cells[0].text),
                                       'name': cells[1].text,
                                       'otaperc': cells[2].text,
                                       'cableperc': cells[3].text,
                                       'cableadsperc': cells[4].text,
                                       }
            except:
                pass
        return data

    def _getDMAMap(self):
        data = dict()
        rankings = self._getRankings()

        r = requests.get(DMATOPOURL)
        if not r.from_cache or not os.path.isfile(PICKLEFILENAME):
            # process into a dictionary if the file is recently fetched
            try:  
                for o in r.json()['objects']['nielsen_dma']['geometries']:
                    try:
                        ''' account for slight spelling and punctuation differences in DMA names '''
                        dmaname = re.sub(' \(.*\)', '', o[u'properties'][u'dma1'])  # difflib struggles with parenthesis
                        data[o[u'properties'][u'dma']] = o[u'properties']
                        matches = difflib.get_close_matches(dmaname,rankings.keys())
                        if len(matches) >= 1:
                            o[u'properties'][u'altname'] = matches[0]
                            o[u'properties'][u'metrics'] = rankings[matches[0]]
                        else:
                            self.error = "unable to lookup ranking for %s (tried %s)" % (o['properties']['dma1'], dmaname)
                    except:
                        o[u'properties'][u'altname'] = None
                        o[u'properties'][u'metrics'] = None
                pickle.dump( data, open( PICKLEFILENAME, "wb" ) )
                logging.info("Updated pickle file %s" % PICKLEFILENAME)
                logging.info("Cache set to %d days" % CACHEDAYS)
                self.cached = False

            except:  # malformed json
                self.error = 'error processing DMA json %s' % DMATOPOURL
                if os.path.isfile(PICKLEFILENAME):  # use old data if possible
                    data = pickle.load( open( PICKLEFILENAME, "rb" ) )
                    logging.info("Continuing to use existing pickle file %s" % PICKLEFILENAME)
                    self.cached = True

        else:
            try:
                data = pickle.load( open( PICKLEFILENAME, "rb" ) )
                self.cached = True
            except:
                self.error = 'error opening DMA json %s' % DMATOPOURL
                self.cached = False
        return data
    
    def iplookup(self, s):
        data = dict()
        r = requests.get('%s/%s' % (GEOIPURL, s))
        if r.status_code == 403:
            self.error = 'too many requests, try again in 30 min'
        else:
            data = r.json()
            if data[u'latitude'] == 37.751 and data[u'longitude'] == -97.822:
                # freegeoip returns this when geolocation is not available for that IP
                data[u'longitude'] = data[u'latitude'] = None
                data[u'dmainfo'] = {}
                self.error = 'no geolocation data available for %s' % s
            else:
                try:
                    data[u'dmainfo'] = self.dmainfomap[data['metro_code']]
                    logging.info('"%s" DMA %d: %s (#%d)' % (s, 
                                                          data[u'dmainfo'][u'dma'],
                                                          data[u'dmainfo'][u'dma1'],
                                                          data[u'dmainfo']['metrics']['rank'], 
                                                          )
                                 )
                except:
                    data[u'dmainfo'] = {}
                    logging.info("%s neilson" % (s, data[u'dmainfo']['metrics']['rank'], data[u'dmainfo'][u'dma1']))
        return data
        
    def domainlookup(self, s):
        return self.iplookup(s)
 