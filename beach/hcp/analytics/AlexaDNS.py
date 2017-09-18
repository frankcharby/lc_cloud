# Copyright 2015 refractionPOINT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from beach.actor import Actor
import urllib.request, urllib.error, urllib.parse
from zipfile import ZipFile
from io import StringIO
import tld
import tld.utils

class AlexaDNS ( Actor ):
    def init( self, parameters, resources ):
        self.domain = 'https://statvoo.com/dl/top-1million-sites.csv.zip'
        self.keepN = parameters.get( 'keep_n', 100000 )
        self.topMap = {}
        self.topList = []
        self.refreshDomains()
        self.handle( 'get_list', self.getList )
        self.handle( 'is_in_top', self.isInTop )

    def deinit( self ):
        pass

    def refreshDomains( self ):
        response = urllib.request.urlopen( urllib.request.Request( self.domain, 
                                                     headers = { 'User-Agent': 'LimaCharlie' } ) ).read()
        z = ZipFile( StringIO( response ) )
        content = z.read( z.namelist()[ 0 ] )
        newMap = {}
        newList = []
        for d in content.split( '\n' ):
            if '' == d: continue
            n, dns = d.split( ',' )
            if int( n ) > self.keepN: continue
            newMap[ dns ] = int( n )
            newList.append( dns )
        self.topMap = newMap
        self.topList = newList
        self.log( "updated Alexa top list with %d domains." % len( self.topList ) )

        try:
            tld.update_tld_names()
        except:
            pass

        self.delay( 60 * 60 * 24, self.refreshDomains )

    def getList( self, msg ):
        topN = msg.data.get( 'n', 1000000 )
        return ( True, { 'domains' : self.topList[ : topN ] } )

    def isInTop( self, msg ):
        domain = msg.data[ 'domain' ]
        try:
            domain = tld.get_tld( domain, fix_protocol = True )
        except:
            pass
        return ( True, { 'n' : self.topMap.get( domain, None ) } )