import urlparse
import io
import zlib

from zope.interface import implements

from twisted.web import http
from twisted.web.client import Agent
from twisted.internet import reactor, protocol, defer
from twisted.internet.protocol import connectionDone
from twisted.web.iweb import IBodyProducer
from twisted.web.server import NOT_DONE_YET


class BodyStreamer(protocol.Protocol):
    def __init__(self, streamfunction, finished):
        self._finished = finished
        self._streamfunction = streamfunction

    def dataReceived(self, data):
        self._streamfunction(data)

    def connectionLost(self, reason=connectionDone):
        self._streamfunction = None
        self._finished.callback(None)
        self._finished = None


class BodyGzipStreamer(BodyStreamer):
    def __init__(self, streamfunction, finished):
        BodyStreamer.__init__(self, streamfunction, finished)
        self.encoderGzip = zlib.compressobj(6, zlib.DEFLATED, 16 + zlib.MAX_WBITS)

    def dataReceived(self, data):
        data = self.encoderGzip.compress(data)
        BodyStreamer.dataReceived(self, data)

    def connectionLost(self, reason=connectionDone):
        data = self.encoderGzip.flush()
        # This attempt to write will fail b/c the connection has been lost.
        BodyStreamer.dataReceived(self, data)
        BodyStreamer.connectionLost(self, reason)


class BodyProducer(object):
    implements(IBodyProducer)

    BUF_MAX_SIZE = 64 * 1024 # TODO Use the hardcoded value for buf max size
    length = 0
    bytes_written = 0

    deferred = None
    inp_buf = None
    rf_buf_fn = None
    consumer = None

    def __init__(self, inp_buf, rf_buf_fn, length):
        self.inp_buf = inp_buf
        self.rf_buf_fn = rf_buf_fn
        self.length = length
        self.deferred = defer.Deferred()

    def startProducing(self, consumer):
        self.consumer = consumer
        return self.resumeProducing()

    def resumeProducing(self):
        chunk = self.inp_buf.read()
        n = len(chunk)
        if n != 0:
            self.consumer.write(chunk)
            self.bytes_written += n
            if self.bytes_written > self.BUF_MAX_SIZE:
                self.inp_buf = self.rf_buf_fn()
                self.bytes_written = 0
        else:
            self.deferred.callback(None)

        return self.deferred

    def stopProducing(self):
        self.deferred = None
        self.inp_buf.close()
        self.rf_buf_fn = None
        self.consumer = None

    def pauseProducing(self):
        pass


class HTTPStreamProxyRequest(http.Request):
    gzip = False

    def __init__(self, *args, **kwargs):
        http.Request.__init__(self, *args, **kwargs)

    def reset_buffer(self):
        self.content.seek(0, 0)
        self.content.truncate(0)
        return self.content

    def gotLength(self, length):
        http.Request.gotLength(self, length)
        if isinstance(self.content, file):
            self.content.close()
            self.content = io.BytesIO()
            self.reset_buffer()

    def process(self):
        proxy_url = bytes(urlparse.urljoin(self.channel.proxy_url, self.uri))

        hdrs = self.requestHeaders
        hdrs.setRawHeaders('X-Forwarded-For', [self.getClientIP()])

        accept_encoding = self.getHeader('Accept-Encoding')
        if accept_encoding is not None and 'gzip' in accept_encoding:
            self.gzip = True

        prod = None
        content_length = self.getHeader('Content-Length')
        if content_length is not None:
            hdrs.removeHeader('Content-Length')
            prod = BodyProducer(self.content, self.reset_buffer, int(content_length))
            self.registerProducer(prod, streaming=True)

        proxy_d = self.channel.http_agent.request(method=self.method,
                                                  uri=proxy_url,
                                                  headers=hdrs,
                                                  bodyProducer=prod)
        if prod is not None:
            proxy_d.addBoth(self.proxyUnregister)

        proxy_d.addCallback(self.proxySuccess)
        proxy_d.addErrback(self.proxyError)

        return NOT_DONE_YET

    def proxySuccess(self, response):
        self.responseHeaders = response.headers
        if self.gzip:
            self.responseHeaders.setRawHeaders(b'content-encoding', [b'gzip'])

        self.responseHeaders.setRawHeaders('Strict-Transport-Security', ['max-age=31536000'])

        self.setResponseCode(response.code)

        d_forward = defer.Deferred()

        if self.gzip:
            response.deliverBody(BodyGzipStreamer(self.write, d_forward))
        else:
            response.deliverBody(BodyStreamer(self.write, d_forward))

        d_forward.addBoth(self.forwardClose)

    def proxyError(self, fail):
        # Always apply the HSTS header. Compliant browsers using plain HTTP will ignore it.
        self.responseHeaders.setRawHeaders('Strict-Transport-Security', ['max-age=31536000'])
        self.setResponseCode(502)
        self.forwardClose()

    def proxyUnregister(self, o):
        self.unregisterProducer()
        return o

    def forwardClose(self, *args):
        self.content.close()
        self.finish()


class HTTPStreamChannel(http.HTTPChannel):
    requestFactory = HTTPStreamProxyRequest

    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPChannel.__init__(self, *args, **kwargs)

        self.proxy_url = proxy_url
        self.http_agent = Agent(reactor, connectTimeout=2)


class HTTPStreamFactory(http.HTTPFactory):
    def __init__(self, proxy_url, *args, **kwargs):
        http.HTTPFactory.__init__(self, *args, **kwargs)
        self.proxy_url = proxy_url

    def buildProtocol(self, addr):
        proto = HTTPStreamChannel(self.proxy_url)
        return proto
