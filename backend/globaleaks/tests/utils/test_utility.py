import StringIO
import re
import sys

from datetime import datetime
from twisted.python.failure import Failure
from twisted.trial import unittest

from globaleaks.utils import utility


class TestUtility(unittest.TestCase):
    def test_msdos_encode(self):
        strs = [
            ('This is \n news', 'This is \r\n news'),
            ('No\r\nreplace', 'No\r\nreplace'),
            ('No\r\n\nreplace', 'No\r\n\r\nreplace'),
            ('No', 'No'),
            ('\nNo\n\n', '\r\nNo\r\n\r\n'),
            ('\r\nNo\n\n', '\r\nNo\r\n\r\n'),
        ]

        for (i, o) in strs:
            self.assertEqual(utility.msdos_encode(i), o)

    def test_log_encode_html_str(self):
        self.assertEqual(utility.log_encode_html("<"), '&lt;')
        self.assertEqual(utility.log_encode_html(">"), '&gt;')
        self.assertEqual(utility.log_encode_html("'"), '&#39;')
        self.assertEqual(utility.log_encode_html("/"), '&#47;')
        self.assertEqual(utility.log_encode_html("\\"), '&#92;')

        self.assertEqual(utility.log_encode_html("<>'/\\"), '&lt;&gt;&#39;&#47;&#92;')

    def test_log_remove_escapes(self):
        for c in map(chr, range(32)):
            self.assertNotEqual(utility.log_remove_escapes(c), c)

        for c in map(chr, range(127, 140)):
            self.assertNotEqual(utility.log_remove_escapes(c), c)

        start = ''.join(map(chr, range(32))) + ''.join(map(chr, range(127, 140)))

        end = ''
        for c in map(chr, range(32)):
            end += utility.log_remove_escapes(c)

        for c in map(chr, range(127, 140)):
            end += utility.log_remove_escapes(c)

        self.assertEqual(utility.log_remove_escapes(start), end)

    def test_uuid4(self):
        self.assertIsNotNone(re.match(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
                                      utility.uuid4()))

    def test_randint(self):
        self.assertEqual(utility.randint(0), 0)
        self.assertEqual(utility.randint(0, 0), 0)
        self.assertEqual(utility.randint(9, 9), 9)

        number = self.assertTrue(utility.randint(1, 2))
        self.assertTrue(0 < number < 3)

    def test_randbits(self):
        self.assertEqual(len(utility.randbits(4)), 0)
        self.assertEqual(len(utility.randbits(8)), 1)
        self.assertEqual(len(utility.randbits(9)), 1)
        self.assertEqual(len(utility.randbits(16)), 2)

    def test_choice(self):
        population = [0, 1, 2, 3, 4, 5]
        self.assertTrue(utility.choice(population) in population)

    def test_shuffle(self):
        ordered = [0, 1, 2, 3, 4, 5]
        shuffle = utility.shuffle(ordered)
        self.assertEqual(len(ordered), len(shuffle))
        for i in ordered:
            self.assertTrue(i in shuffle)

    def test_datetime_null(self):
        self.assertEqual(utility.datetime_null(), datetime.utcfromtimestamp(0))

    def test_get_expiration(self):
        date = utility.get_expiration(15)
        self.assertEqual(date.hour, 00)
        self.assertEqual(date.minute, 00)
        self.assertEqual(date.second, 00)

    def test_is_expired(self):
        self.assertTrue(utility.is_expired(utility.datetime_null()))
        self.assertTrue(utility.is_expired(utility.datetime_now()))

    def test_datetime_to_ISO8601_to_datetime_to_dot_dot_dot(self):
        a = utility.datetime_null()
        b = utility.datetime_to_ISO8601(a)
        c = utility.ISO8601_to_datetime(b)
        d = utility.datetime_to_ISO8601(c)
        self.assertTrue(a, c)
        self.assertTrue(b, d)

    def test_datetime_to_pretty_str(self):
        self.assertEqual(utility.datetime_to_pretty_str(utility.datetime_null()),
                        'Thursday 01 January 1970 00:00 (UTC)')

    def test_ISO8601_to_pretty_str(self):
        self.assertEqual(utility.ISO8601_to_pretty_str(None), 'Thursday 01 January 1970 00:00 (UTC)')
        self.assertEqual(utility.ISO8601_to_pretty_str('1970-01-01T00:00:00Z'), 'Thursday 01 January 1970 00:00 (UTC)')
        self.assertEqual(utility.ISO8601_to_pretty_str(None, 1), 'Thursday 01 January 1970 01:00')
        self.assertEqual(utility.ISO8601_to_pretty_str(None, 2), 'Thursday 01 January 1970 02:00')
        self.assertEqual(utility.ISO8601_to_pretty_str('1970-01-01T00:00:00Z', 1), 'Thursday 01 January 1970 01:00')
        self.assertEqual(utility.ISO8601_to_pretty_str('1970-01-01T00:00:00Z', 2), 'Thursday 01 January 1970 02:00')

    def test_bytes_to_pretty_str(self):
        self.assertEqual(utility.bytes_to_pretty_str("60000000001"), "60GB")
        self.assertEqual(utility.bytes_to_pretty_str("5000000001"), "5GB")
        self.assertEqual(utility.bytes_to_pretty_str("40000001"), "40MB")
        self.assertEqual(utility.bytes_to_pretty_str("3000001"), "3MB")
        self.assertEqual(utility.bytes_to_pretty_str("20001"), "20KB")
        self.assertEqual(utility.bytes_to_pretty_str("1001"), "1KB")

    def test_log(self):
        utility.log.info("info")
        utility.log.err("err")
        utility.log.debug("debug")
        utility.log.msg("msg")

    def test_caller_name(self):
        def abcdef():
            return utility.caller_name()

        self.assertEqual(abcdef(), 'globaleaks.tests.utils.test_utility.TestUtility.test_caller_name')

class TestLogging(unittest.TestCase):
    def setUp(self):
        fake_std_out = StringIO.StringIO()
        self._stdout, sys.stdout = sys.stdout, fake_std_out

    def tearDown(self):
        sys.stdout = self._stdout

    def test_log_emission(self):
        output_buff = StringIO.StringIO()

        observer = utility.GLLogObserver(output_buff)
        observer.start()

        # Manually emit logs
        e1 = {'time': 100000, 'message': 'x', 'system': 'ut'}
        observer.emit(e1)

        f = Failure(IOError('This is a mock failure'))
        e2 = {'time': 100001, 'message': 'x', 'system': 'ut', 'failure': f}
        observer.emit(e2)

        # Emit logs through twisted's interface. Import is required now b/c of stdout hack
        from twisted.python import log as twlog
        twlog.err("error-msg")
        twlog.err("info-msg")
        twlog.msg("msg-msg")
        observer.stop()

        s = output_buff.getvalue()
        # A bit of a mess, but this is the format we are expecting.
        gex = r".+ \[ut\] x\n"
        m = re.findall(gex, s)
        self.assertTrue(len(m) == 2)
        self.assertTrue(s.endswith("[-] msg-msg\n"))
