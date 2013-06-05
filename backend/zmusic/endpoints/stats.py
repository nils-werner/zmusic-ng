from zmusic import app, db
from zmusic.database import Download
from zmusic.login import login_required, is_admin
from flask import jsonify, request, abort
import socket

def clean_ip():
	ip = request.remote_addr
	if (ip.find('::ffff:') == 0 and len(ip) > len('::ffff:')):
		ip = ip[len('::ffff:'):]
	return ip

@app.route('/stats')
@app.route('/stats/')
@login_required
def stats_all_ips():
	ips = []
	socket.setdefaulttimeout(2)

	if is_admin():
		iterations = [a.ip for a in db.session.query(Download.ip).group_by(Download.ip).order_by(db.desc(db.func.max(Download.time)))]
	else:
		iterations = [clean_ip()]

	for ip in iterations:
		try:
			host = socket.gethostbyaddr(ip)[0]
		except:
			host = None
		ips.append({ "ip": ip, "host": host })
	response = jsonify(downloaders=ips)
	response.cache_control.no_cache = True
	return response

@app.route('/stats/<ip>')
@login_required
def stats_for_ip(ip):
	if not is_admin() and ip != clean_ip():
		return abort(403)
	songlist = []
	for song in Download.query.filter((Download.ip == ip) & (Download.leader_id == None)).order_by(Download.leader_id).order_by(db.desc(Download.time)):
		if song.is_zip:
			zipsongs = [song.to_dict()]
			for zipsong in Download.query.filter(Download.leader_id == song.id).order_by(Download.time):
				zipsongs.append(zipsong.to_dict())
			songlist.append({ "zip": zipsongs })
		else:
			songlist.append({ "song": song.to_dict() })
	response = jsonify(downloads=songlist)
	response.cache_control.no_cache = True
	return response
