import pyqrcode
import png
from  pyqrcode import create

d = "https://biotutor-ai-dershin.streamlit.app"

url = pyqrcode.create(d)

url.svg("myqr.svg",scale=8)

url.png("myqr.png",scale=6)