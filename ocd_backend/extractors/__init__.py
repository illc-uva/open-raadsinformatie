import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from ocd_backend.settings import USER_AGENT
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class BaseExtractor(object):
    """The base class that other extractors should inherit."""

    def __init__(self, source_definition):
        """
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        """
        self.source_definition = source_definition

    def run(self):
        """Starts the extraction process.

        This method must be implemented by the class that inherits the
        :py:class:`BaseExtractor` and should return a generator that
        yields one item per value. Items should be formatted as tuples
        containing the following elements (in this order):

        - the content-type of the data retrieved from the source (e.g.
          ``application/json``)
        - the data in it's original format, as retrieved from the source
          (as a string)
        """
        raise NotImplementedError

    def interval_generator(self):
        """Returns a generator with date intervals

        The intervals are generated between the 'start_date' and 'end_date'
        specified in the source configuration. The default is one month ago
        from now, which can be changed by specifying 'months_interval'.
        """

        months = 1  # Max 1 months intervals by default
        if 'months_interval' in self.source_definition:
            months = self.source_definition['months_interval']
        days = (months / 2.0) * 30

        if (months / 2.0) < 1.0:
            interval_delta = relativedelta(days=days)
        else:
            interval_delta = relativedelta(months=months)

        current_start = datetime.today() - interval_delta

        if 'start_date' in self.source_definition:
            current_start = parse(self.source_definition['start_date'])

        end_date = datetime.today() + interval_delta

        if 'end_date' in self.source_definition:
            end_date = parse(self.source_definition['end_date'])

        while True:
            current_end = current_start + interval_delta

            # If next current_end exceeds end_date then stop at end_date
            if current_end > end_date:
                current_end = end_date
                log.debug("Next interval exceeds %s, months_interval not used"
                          % end_date)

            yield current_start, current_end

            current_start = current_end + relativedelta(seconds=1)

            # Stop while loop if exceeded end_date
            if current_start > end_date:
                break


class CustomRetry(Retry):
    """A subclass of the Retry class but with extra logging"""
    def increment(self, method=None, url=None, response=None, error=None,
                  _pool=None, _stacktrace=None):
        res = super(CustomRetry, self).increment(method, url, response,
                                                 error, _pool, _stacktrace)
        log.info("Retrying url: %s" % url)
        return res


class HttpRequestMixin(object):
    """A mixin that can be used by extractors that use HTTP as a method
    to fetch data from a remote source. A persistent
    :class:`requests.Session` is used to take advantage of
    HTTP Keep-Alive.
    """

    @property
    def http_session(self):
        """Returns a :class:`requests.Session` object. A new session is
        created if it doesn't already exist."""
        http_session = getattr(self, '_http_session', None)
        if not http_session:
            requests.packages.urllib3.disable_warnings()
            session = requests.Session()
            session.headers['User-Agent'] = USER_AGENT

            http_retry = CustomRetry(total=12, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('http://', http_adapter)

            http_retry = CustomRetry(total=12, status_forcelist=[500, 503],
                                     backoff_factor=.4)
            http_adapter = HTTPAdapter(max_retries=http_retry)
            session.mount('https://', http_adapter)

            self._http_session = session

        return self._http_session
