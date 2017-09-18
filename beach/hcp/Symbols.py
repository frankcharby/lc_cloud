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

try:
    from beach.actor import Actor
except:
    pass
import os
import json

class Symbols( object ):
    def __init__(self):
        self.lookups = {}
        self.reload()

    def reload( self ):
        class _unnamedSymbolGroup( object ):
            pass

        try:
            tmpTags = Actor.readRelativeFile( 'rp_hcp_tags.json' )
        except:
            tmpTags = open( os.path.join( os.path.abspath( os.path.dirname( __file__ ) ), 'rp_hcp_tags.json' ), 'rb' ).read()
        tmpTags = json.loads( tmpTags.decode('utf-8') )
        for group in tmpTags[ 'groups' ]:
            gName = group[ 'groupName' ]
            for definition in group[ 'definitions' ]:
                tName = str( definition[ 'name' ] )
                tValue = str( definition[ 'value' ] )
                fullName = '%s.%s' % ( gName, tName )

                self.lookups[ tValue ] = fullName
                self.lookups[ fullName ] = tValue

                if not hasattr( self, gName ):
                    setattr( self, gName, _unnamedSymbolGroup() )
                setattr( getattr( self, gName ), tName, tValue )
