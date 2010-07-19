from Products.Five.browser import BrowserView
from collective.transcode.star.interfaces import ICallbackView, ITranscodeTool
from zope.interface import implements
from zope.component import getUtility
from crypto import encrypt, decrypt
from base64 import b64encode, b64decode
import logging
from collective.flowplayer.browser.view import File as FlowView

log = logging.getLogger('collective.transcode')

class File(FlowView):
    def href(self):
        tt = getUtility(ITranscodeTool)
        try:
            mp4 = tt[self.context.UID()]['file']['mp4']
            return '%s/%s' % (mp4['address'],mp4['path'])
        except:
            return FlowView.href(self)

class CallbackView(BrowserView):
    """
        Handle callbacks and errbacks from transcode daemon
    """
    implements(ICallbackView)
    def callback_xmlrpc(self, result):
        """
           Handle callbacks
        """
        tt = getUtility(ITranscodeTool)
        secret = tt.secret()
        try:
            result = eval(decrypt(b64decode(result['key']), secret), {"__builtins__":None},{})
            assert result.__class__ is dict
        except Exception, e:
            log.error("Unauthorized callback %s" % result)
            return

        if result['path']:
            tt.callback(result)
        else:
            tt.errback(result)


class ServeDaemonView(BrowserView):
    """
        Handle callbacks from transcode daemon
    """
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        try: 
            tt = getUtility(ITranscodeTool)
            key = self.request['key']
            input = decrypt(b64decode(key), tt.secret())
            (uid, fieldName, profile) = eval(input, {"__builtins__":None},{})
            obj = self.context.uid_catalog(UID=uid)[0].getObject()
            if not fieldName:
                fieldName = obj.getPrimaryField().getName()
            field = obj.getField(fieldName)
            if tt[uid][fieldName][profile]['status']!='pending':
                log.error('status not pending')
                raise
            return field.download(obj)
        except Exception, e:
            log.error('Unauthorized file request: %s' % e)
            return
