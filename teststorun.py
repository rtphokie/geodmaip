'''
Created on Jun 25, 2017

@author: Tony Rice
'''
import unittest
import logging
from pprint import pprint
from geodmaip import GeoDMAIP   


class Test(unittest.TestCase):

    def test_00_Rankings(self):
        GeoDMAIP.LOGLEVEL = logging.DEBUG
        uut = GeoDMAIP()

        data = uut._getRankings()
        #Testing note: this values can change
        self.assertAlmostEqual(data['Savannah']['rank']/10.0, 9.1, 1)
        self.assertAlmostEqual(data[u'Milwaukee']['rank']/10.0, 3.5, 1)
        self.assertTrue(data[u'New York']['rank'], 1)

    def test_00_Neilson(self):
        GeoDMAIP.LOGLEVEL = logging.DEBUG
        uut = GeoDMAIP()

        tocheck = {'Bakersfield': 800,
                   'Cleveland': 510,
                   'Waco': 625,
                   'Raleigh': 560,
                   'Portland': 820,
                   }
        for city in tocheck.keys():
            citydata = uut.dmainfomap[tocheck[city]]
            self.assertTrue(city in citydata[u'dma1'], 'for %d: expected %s, got %s' % (tocheck[city], city, citydata['dma1'],))

    def test_01_LookupIP(self):
        GeoDMAIP.LOGLEVEL = logging.DEBUG
        uut = GeoDMAIP()
        d = uut.iplookup ('108.209.28.133')

        self.assertTrue('Raleigh' in d[u'dmainfo'][u'dma1'])
        self.assertAlmostEqual(d[u'dmainfo'][u'metrics'][u'rank']/10.0, 2.4, 1)

    def test_02_LookupDomains(self):
        GeoDMAIP.LOGLEVEL = logging.DEBUG
        uut = GeoDMAIP()
        tocheck = {'nando.net': u'Sacramento',
                   'chron.com': 'San Antonio',
                   'whatsupin.space': 'New York',
                   'nasa.gov': 'Washington, DC',
                   'amsmeteors.org': 'San Antonio',
                   'delta.com': 'Washington, DC',
                   'ametsoc.com': 'Atlanta'}
        for domain in tocheck.keys():
            data = uut.domainlookup(domain)
            self.assertNotEqual(data[u'dmainfo'],{}, 'neilson lookup for %s failed' % domain)
            self.assertTrue(tocheck[domain] in data[u'dmainfo'][u'dma1'], 'expected %s, got %s' % (tocheck[domain], data['neilson']['dma1'],))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()