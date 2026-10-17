"""Small adb UI helper. Does not fake screenshots or bypass the app's network path."""
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADB = str(Path.home() / 'Library/Android/sdk/platform-tools/adb')
OUT = ROOT / 'docs/evidence'

def adb(*args):
    return subprocess.check_output([ADB, *args])

def nodes():
    for attempt in range(3):
        time.sleep(.6)
        try:
            adb('shell', 'uiautomator', 'dump', '/sdcard/window.xml')
            root = ET.fromstring(adb('shell', 'cat', '/sdcard/window.xml'))
            if list(root): return root
        except (subprocess.CalledProcessError, ET.ParseError):
            time.sleep(.5)
    raise RuntimeError('Android UI hierarchy unavailable after retries')

def tap_node(node):
    a,b,c,d = map(int, re.findall(r'\d+', node.attrib['bounds']))
    adb('shell','input','tap',str((a+c)//2),str((b+d)//2))

def tap(text, exact=True):
    for _ in range(8):
        for node in nodes().iter('node'):
            value = node.attrib.get('text','')
            if (value == text if exact else text in value):
                tap_node(node)
                return
        time.sleep(.5)
    raise RuntimeError('UI text not found: '+text)

def fill(index, text):
    inputs = [n for n in nodes().iter('node') if n.attrib.get('class') == 'android.widget.EditText']
    tap_node(inputs[index])
    adb('shell','input','keycombination','113','29')
    adb('shell','input','keyevent','KEYCODE_DEL')
    adb('shell','input','text',text.replace(' ','%s'))
    time.sleep(.8)

def shot(name):
    time.sleep(1)
    (OUT/name).write_bytes(adb('exec-out','screencap','-p'))

def dump():
    print('\n'.join(n.attrib.get('text','')+' '+n.attrib.get('content-desc','')+' '+n.attrib.get('bounds','') for n in nodes().iter('node') if n.attrib.get('text') or n.attrib.get('content-desc')))
