import sass

from evidencelocker.__main__ import app

@app.get("/assets/style/light.css")
def light_css():
	with open('evidencelocker/evidencelocker/assets/style/light.scss') as stylesheet:
		return Response(sass.compile(string=stylesheet.read(), mimetype="text/css"))