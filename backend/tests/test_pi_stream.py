import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

from app.config import Settings
from app.llm.base import LLMMessage
from app.llm.ollama_client import OllamaClient
from app.llm.pi_client import PiClient


def test_pi_streams_provider_text_and_sends_output_limit():
    captured = {'requests': []}

    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            captured['body'] = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            captured['requests'].append(captured['body'])
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for delta in ['Grounded ', 'answer [1].']:
                event = {'id': 'test', 'object': 'chat.completion.chunk', 'created': 0,
                         'model': 'test-model', 'choices': [{'index': 0, 'delta': {'content': delta}, 'finish_reason': None}]}
                self.wfile.write(('data: ' + json.dumps(event) + '\n\n').encode())
                self.wfile.flush()
            self.wfile.write(b'data: {"id":"test","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n')
            self.wfile.flush()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Provider)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    settings = Settings(OLLAMA_BASE_URL=url, OLLAMA_MODEL='test-model', LLM_MAX_OUTPUT_TOKENS=96)
    client = PiClient('ollama', settings, OllamaClient(url, 'test-model'))
    deltas = []
    try:
        answer = client.generate_stream('Use only sources.', [LLMMessage(role='user', content='Question')], deltas.append)
        assert answer == 'Grounded answer [1].'
        assert ''.join(deltas) == answer
        assert captured['body']['max_tokens'] == 96
        assert captured['body']['temperature'] == 0.2
        assert len(captured['requests']) == 1  # No extra model call to compact the transcript prompt.
        assert captured['body']['stream'] is True
        assert not captured['body'].get('tools')
    finally:
        server.shutdown()
        server.server_close()
