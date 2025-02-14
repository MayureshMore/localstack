"""Handler for routing internal localstack resources under /_localstack."""
import logging
from werkzeug.exceptions import NotFound
from localstack import constants
from localstack.http import Response
from localstack.runtime import events
from localstack.services.internal import LocalstackResources
from ..api import RequestContext
from ..chain import Handler, HandlerChain
LOG = logging.getLogger(__name__)

class LocalstackResourceHandler(Handler):
    """
    Adapter to serve LocalstackResources as a Handler.
    """
    resources: LocalstackResources

    def __init__(self, resources: LocalstackResources=None) -> None:
        """Auto-generated docstring for function __init__."""
        from localstack.services.internal import get_internal_apis
        self.resources = resources or get_internal_apis()

    def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        """Auto-generated docstring for function __call__."""
        try:
            response.update_from(self.resources.dispatch(context.request))
            chain.stop()
        except NotFound:
            path = context.request.path
            if path.startswith(constants.INTERNAL_RESOURCE_PATH + '/'):
                LOG.warning('Unable to find resource handler for path: %s', path)
                chain.respond(404)

class RuntimeShutdownHandler(Handler):

    def __call__(self, chain: HandlerChain, context: RequestContext, response: Response):
        """Auto-generated docstring for function __call__."""
        if events.infra_stopped.is_set():
            chain.respond(503)
        elif events.infra_stopping.is_set():
            if context.is_internal_call:
                return
            if context.request.path.startswith('/_localstack'):
                return
            chain.respond(503)