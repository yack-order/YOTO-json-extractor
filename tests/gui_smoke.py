"""Build the production GUI and exercise redacted JSON output under Xvfb."""
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import customtkinter as ctk

root = ctk.CTk()
root.withdraw()
try:
    with patch.object(ctk, 'CTk', return_value=root), patch.object(root, 'mainloop'):
        app = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'YOTO.py'))
    root.update_idletasks()
    assert app['download_button'].cget('text') == 'Extract (non Yoto Original) files'
    app['json_status_callback']('Only')
    with tempfile.TemporaryDirectory() as output:
        app['handle_json_data'].__globals__['save_directory'] = output
        data = {'props': {'pageProps': {'card': {
            'title': 'Synthetic smoke test', 'userId': 'yoto',
            'access_token': 'SYNTHETIC_GUI_SECRET',
            'shareLinkUrl': 'https://yoto.io/ABCDE?s=SYNTHETIC_CARD_SECRET',
        }}}}
        assert app['handle_json_data'](data, 'https://example.invalid', app['JSON_STATUS']['only']) == app['STATUS']['ok']
        files = list(Path(output).glob('*.json'))
        assert len(files) == 1
        saved = files[0].read_text()
        assert 'SYNTHETIC_GUI_SECRET' not in saved
        assert 'SYNTHETIC_CARD_SECRET' not in saved
        json.loads(saved)
    with patch.dict(os.environ, {'YOTO_CLIENT_ID': ''}):
        app['authenticate']()  # fail closed without starting a browser or listener
    root.update_idletasks()
    print('GUI construction, mode callback, redacted JSON export and missing-client login checks passed.')
finally:
    root.destroy()
