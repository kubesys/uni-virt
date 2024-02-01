'''
 * Copyright (2024, ) Institute of Software, Chinese Academy of Sciences
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 '''

class BadRequest(Exception):
    def __init__(self, message):
        self.reason = 400
        self.message = message

class Forbidden(Exception):
    def __init__(self, message):
        self.reason = 403
        self.message = message
        
class NotFound(Exception):
    def __init__(self, message):
        self.reason = 404
        self.message = message
        
class InternalServerError(Exception):
    def __init__(self, message):
        self.reason = 500
        self.message = message
        
class ConditionException(Exception):
    def __init__(self, code, msg):
        self.code = code
        self.msg = msg

class ExecuteException(Exception):
    def __init__(self, reason, message):
        self.reason = reason
        self.message = message
