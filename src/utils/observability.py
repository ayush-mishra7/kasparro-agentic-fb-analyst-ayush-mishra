from utils.logging_utils import make_trace_id, start_span, end_span, SpanCtx

def start_trace(name, agent=None):
    trace_id = make_trace_id()
    span = start_span(name, trace_id=trace_id, agent=agent)
    return span
