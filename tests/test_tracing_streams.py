import time

import mock
import unittest

from flask import (Flask, Response, request, stream_with_context)
import opentracing
from opentracing.ext import tags
from opentracing.mocktracer import MockTracer
from flask_opentracing import FlaskTracing
from flaky import flaky


app = Flask(__name__)
test_app = app.test_client()


tracing_all = FlaskTracing(MockTracer(), True, app, ['url'])
tracing = FlaskTracing(MockTracer())
tracing_deferred = FlaskTracing(lambda: MockTracer(),
                                True, app, ['url'])


@app.route('/test/streams', methods=['GET'])
@tracing.trace()
def check_test_works():

    @stream_with_context
    def test():
        time.sleep(2)
        yield 'a'
        time.sleep(2)
        yield 'b'

    class MyResponse(Response):
        implicit_sequence_conversion = False
        automatically_set_content_length = False

    return MyResponse(test(), status=200)


class TestStreams(unittest.TestCase):
    def setUp(self):
        tracing_all._tracer.reset()
        tracing._tracer.reset()
        tracing_deferred._tracer.reset()

    def test_span_tags(self):
        response = test_app.get('/test/streams')
        assert len(tracing.tracer.finished_spans()) == 0
        assert response.text == 'ab'
        assert len(tracing.tracer.finished_spans()) == 1
