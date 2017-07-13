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
import traceback
import hashlib
import hmac
import time
import ipaddress
import uuid
from sets import Set
CassDb = Actor.importLib( 'utils/hcp_databases', 'CassDb' )
CassPool = Actor.importLib( 'utils/hcp_databases', 'CassPool' )
rpcm = Actor.importLib( 'utils/rpcm', 'rpcm' )
rList = Actor.importLib( 'utils/rpcm', 'rList' )
rSequence = Actor.importLib( 'utils/rpcm', 'rSequence' )
AgentId = Actor.importLib( 'utils/hcp_helpers', 'AgentId' )

class EnrollmentManager( Actor ):
    def init( self, parameters, resources ):
        self.enrollmentKey = parameters.get( 'enrollment_token', 'DEFAULT_HCP_ENROLLMENT_TOKEN' )
        self._db = CassDb( parameters[ 'db' ], 'hcp_analytics', consistencyOne = True )
        self.db = CassPool( self._db,
                            rate_limit_per_sec = parameters[ 'rate_limit_per_sec' ],
                            maxConcurrent = parameters[ 'max_concurrent' ],
                            blockOnQueueSize = parameters[ 'block_on_queue_size' ] )

        self.db.start()

        self.installers = Set()

        self.schedule( 3600, self.loadRules )

        self.handle( 'enroll', self.enroll )
        self.handle( 'authorize', self.authorize )
        self.handle( 'reload', self.loadRules )

    def deinit( self ):
        pass

    def loadRules( self, msg = None ):
        newRules = []
        for row in self.db.execute( 'SELECT oid, iid FROM hcp_installers' ):
            self.installers.add( ( row[ 0 ], row[ 1 ] ) )

    def getTokenFor( self, aid ):
        h = hmac.new( self.enrollmentKey, aid.asString(), hashlib.sha256 )
        return h.digest()

    def enroll( self, msg ):
        req = msg.data

        aid = AgentId( req[ 'aid' ] )

        if ( aid.org_id, aid.ins_id ) not in self.installers:
            return ( True, { 'aid' : None } )

        extIp = req[ 'public_ip' ]
        intIp = req[ 'internal_ip' ]
        hostName = req[ 'host_name' ]

        aid.sensor_id = uuid.uuid4()

        self.db.execute( 'INSERT INTO sensor_states ( sid, oid, iid, plat, arch, enroll ) VALUES ( %s, %s, %s, %s, %s, dateOf( now() ) )', 
                         ( aid.sensor_id, aid.org_id, aid.ins_id, aid.platform, aid.architecture ) )

        self.db.execute( 'INSERT INTO org_sensors ( oid, iid, sid ) VALUES ( %s, %s, %s )', 
                         ( aid.org_id, aid.ins_id, aid.sensor_id ) )

        enrollmentToken = self.getTokenFor( aid )

        return ( True, { 'aid' : aid, 'token' : enrollmentToken } )

    def authorize( self, msg ):
        req = msg.data

        aid = AgentId( req[ 'aid' ] )
        token = req[ 'token' ]

        isAuthorized = False

        expectedEnrollmentToken = self.getTokenFor( aid )
        
        if hmac.compare_digest( token, expectedEnrollmentToken ):
            isAuthorized = True

        return ( True, { 'is_authorized' : isAuthorized } )