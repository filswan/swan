import json

import requests


class Aria2c:
    '''
    Example :

      client = Aria2c('localhost', '6800')

      # print server version
      print(client.getVer())

      # add a task to server
      client.addUri('http://example.com/file.iso')

      # provide addtional options
      option = {"out": "new_file_name.iso"}
      client.addUri('http://example.com/file.iso', option)
    '''
    IDPREFIX = "nbfs"
    ADD_URI = 'aria2.addUri'
    GET_VER = 'aria2.getVersion'
    STOPPED = 'aria2.tellStopped'
    ACTIVE = 'aria2.tellActive'
    STATUS = 'aria2.tellStatus'

    def __init__(self, host, port, token=None):
        self.host = host
        self.port = port
        self.token = token
        self.serverUrl = "http://{host}:{port}/jsonrpc".format(**locals())

    def _genPayload(self, method, uris=None, options=None, cid=None, IDPREFIX=None):
        cid = IDPREFIX + cid if cid else Aria2c.IDPREFIX
        p = {
            'jsonrpc': '2.0',
            'id': cid,
            'method': method,
            'params': []
        }

        if self.token:
            p['params'].append("token:" + self.token)
        if uris:
            p['params'].append(uris)
        if options:
            p['params'].append(options)
        return p

    @staticmethod
    def _defaultErrorHandler(code, message):
        print("ERROR: {}, {}".format(code, message))
        return None

    def _post(self, action, params, onSuc, onFail=None):
        if onFail is None:
            onFail = Aria2c._defaultErrorHandler
        payloads = self._genPayload(action, *params)
        resp = requests.post(self.serverUrl, data=json.dumps(payloads))
        result = resp.json()
        if "error" in result:
            return onFail(result["error"]["code"], result["error"]["message"])
        else:
            return onSuc(resp)

    def addUri(self, uri, options=None):
        def success(response):
            return response.text

        return self._post(Aria2c.ADD_URI, [[uri, ], options], success)

    def getVer(self):
        def success(response):
            return response.json()['result']['version']

        return self._post(Aria2c.GET_VER, [], success)

    def getStopped(self, offset, number):
        def success(response):
            return response.json()

        return self._post(Aria2c.STOPPED, [offset, number], success)

    def getActive(self, offset, number):
        def success(response):
            return response.json()

        return self._post(Aria2c.ACTIVE, [offset, number], success)

    #   {
    #    "bitfield":"80",
    #    "completedLength":"100352",
    #    "connections":"0",
    #    "dir":"/home/chi/aria2/download",
    #    "downloadSpeed":"0",
    #    "errorCode":"0",
    #    "errorMessage":"",
    #    "files":[
    #       {
    #          "completedLength":"100352",
    #          "index":"1",
    #          "length":"100352",
    #          "path":"/home/chi/aria2/download/file-sample_100kB.doc",
    #          "selected":"true",
    #          "uris":[
    #             {
    #                "status":"used",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             },
    #             {
    #                "status":"waiting",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             },
    #             {
    #                "status":"waiting",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             },
    #             {
    #                "status":"waiting",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             },
    #             {
    #                "status":"waiting",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             },
    #             {
    #                "status":"waiting",
    #                "uri":"https://file-examples-com.github.io/uploads/2017/02/file-sample_100kB.doc"
    #             }
    #          ]
    #       }
    #    ],
    #    "gid":"614a8c08af12cdfe",
    #    "numPieces":"1",
    #    "pieceLength":"1048576",
    #    "status":"complete",
    #    "totalLength":"100352",
    #    "uploadLength":"0",
    #    "uploadSpeed":"0"
    # }

    def getStatus(self, gid: str):
        def success(response):
            return response.json()

        return self._post(Aria2c.STATUS, [gid], success)
