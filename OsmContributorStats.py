#-*- coding: utf-8 -*-

'''
#!/usr/bin/python
'''
#========================================================================="
# OsmContributorStats.py
# Version 0.3.1
# Pierre Beland, 08-2014
# See https://github.com/pierzen/osm-contributor-stats/README.md
#========================================================================="

#__version__ = '0.3.1'

import ast, csv, os, sys, json, math
from pprint import pprint
from datetime import datetime
from datetime import timedelta
import gettext
class OsmContributorStats:

	def __init__(self, rep=None, lang="en", debug = False):
		self.rep=rep
		# debug
		self._debug = debug
		# translation : french and english available
		#LOCALE_PATHS = ('/home/mathx/crepes_bretonnes/locale/',)
		# tuto : http://fr.openclassrooms.com/informatique/cours/developpez-votre-site-web-avec-le-framework-django/sortez-vos-dictionnaires-place-a-la-traduction
		if lang in ["en","fr"] : self.lang=lang
		else : self.lang="en"
		module_dir= os.getcwd()
		_ = gettext.translation(self.lang,module_dir , fallback=True).ugettext
		# trad.textdomain("OsmContributorStats")
		#_ = trad.ugettext
		print _('List of Changesets excluded')
		#translation.activate(self.lang)
		print "lang=",self.lang

	def __del__(self):
		return None

	def verif_users(self,users):
		try:
		  users
		except NameError:
			team_from=1
			team_to=1
			users=[None]*2
			users[0]=[""]
			print "users do not exist,  create it :", users
		else:
			if users != None:
				print "users existe : ",users
			else:
				team_from=0
				team_to=0
				users=[None]*2
				users[0]=[""]
				print 'users=none non defini, valeur par defaut, vide ', users
		return users

	#=========================================================
	"""
	The following block determine changeset to flag for exclusion based on the surface of the BBOX. The objective is to eliminate from BOTS and Massive edites that covers part of the world objects that are outside of the Study zone. The critera is to flag the changests for which the surface is at least ten times larger then the bbox of the Study zone.
	"""

	def distance_on_unit_sphere(self, lat1, lon1, lat2, lon2):
		#source 2013-09-09 http://www.johndcook.com/python_lonitude_latitude.html public domain
		# Convert latitude and longitude to
		# spherical coordinates in radians.
		# to avoid math domain error, value modified if 180.0
		"""
		if (lon1>=180.0) :
			lon1=179.95
		if (lon1<=-180.0) :
			lon1=-179.95
		if (lon2>=180.0) :
			lon2=179.95
		if (lon2<=-180.0) :
			lon2=-179.95
		"""
		degrees_to_radians = math.pi/180.0
		# phi = 90 - latitude
		phi1 = (90.0 - float(lat1))*degrees_to_radians
		phi2 = (90.0 - float(lat2))*degrees_to_radians

		# theta = longitude
		theta1 = float(lon1)*degrees_to_radians
		theta2 = float(lon2)*degrees_to_radians

		# Compute spherical distance from spherical coordinates.

		# For two locations in spherical coordinates
		# (1, theta, phi) and (1, theta, phi)
		# cosine( arc length ) =
		#	sin phi sin phi' cos(theta-theta') + cos phi cos phi'
		# distance = rho * arc length

		cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
			   math.cos(phi1)*math.cos(phi2))
		if cos>0.9999 : arc=0.0
		else : arc = math.acos( cos )

		# Remember to multiply arc by the radius of the earth
		# in your favorite set of units to get length.
		return arc

	def calc_dims_bbox(self, lat1,lon1,lat2,lon2):
		radius = 6372.8 # earth's mean radium in km
		dist=radius*self.distance_on_unit_sphere(lat1,lon1,lat2,lon2)
		dist_lat=radius*self.distance_on_unit_sphere(lat1,lon1,lat2,lon1)
		dist_lon=radius*self.distance_on_unit_sphere(lat1,lon1,lat1,lon2)
		surface=dist_lat*dist_lon
		dims={};dims["dist"]=dist
		dims["dist_lat"]=dist_lat
		dims["dist_lon"]=dist_lon
		dims["surface"]=surface
		return dims

	def open_file(filename,filemode) :
		try:
			fp = open(filename,filemode)
		except IOError as e:
			if e.errno == errno.EACCES:
				return
			# Not a permission error.
			raise
		else:
			return fp
		return

	def Changesets_to_Exclude(self,nom_changeset_list,min_lon,max_lon,min_lat,max_lat,csv_dim) :
		os.chdir(self.rep)
		if self._debug: print "debug: rep=" + os.getcwd()
		if self._debug: print "debug: nom_changeset_list=" + str(nom_changeset_list)
		if self._debug: print os.listdir(self.rep)
		try:
			fi_changesets_list = open(nom_changeset_list, 'r')
		except:
			sys.exit ("\n ERROR OsmContributorStats, Changesets_Contributor_Statistics function.\n Directory " + self.rep+", Filename "+ nom_changeset_list + " not found.\n Note that parameters from_date, to_date and prefix should be the same as in API6_Collect_Changesets function.\n" )
		if ((min_lon-max_lon)<0.0001) and ((max_lat-min_lat)<0.0001):
			dims_bbox={"dist":1.0, "dist_lat":1.0,"dist_lon":1.0,"surface":1}
		else: dims_bbox=self.calc_dims_bbox(min_lat,min_lon,max_lat,max_lon)
		surface_bbox=dims_bbox["surface"]
		if (surface_bbox==0): surface_bbox=0.1
		nb=0
		exclusion=[]
		exclusion.append(9)
		for read_list in fi_changesets_list.readlines():
			changesets_list=ast.literal_eval(read_list)
			# one line contains many changeset lists
			""" changeset_list
			{17145613: {u'uid': 1692003, u'open': False,
			u'min_lat': u'-38.9458371',
			u'created_at': u'2013-07-29T22:01:24Z',
			u'max_lon': u'-3.697719',
			u'tag': {u'comment': u'Casa Neuquen Basavilbaso 1075', u'imagery_used': u'Bing', u'created_by': u'iD 1.0.1'},
			u'user': u'Kiter Simha', u'max_lat': u'40.4168397', u'min_lon': u'-74.4806297', u'closed_at': u'2013-07-29T22:01:27Z',
			u'id': 17145613}
			"""
			for obs in changesets_list:
				nb+=1
				lon1=changesets_list[obs]["min_lon"]
				lon2=changesets_list[obs]["max_lon"]
				lat1=changesets_list[obs]["min_lat"]
				lat2=changesets_list[obs]["max_lat"]
				exclu=0
				if (lon1==lon2) and (lat1==lat2):
					dims_changeset={"dist":1, "dist_lat":1, "dist_lon":1, "surface":1}
					ratio=0
				else:
					dims_changeset=self.calc_dims_bbox(lat1,lon1,lat2,lon2)
					ratio=dims_changeset["surface"]/surface_bbox
					if ratio >= 100 :
						exclusion.append(obs)
						exclu=1
				tag=changesets_list[obs]["tag"]
				if (nb==1): pprint(tag)
				comment=""
				created_by=""
				csv_dim_txt=changesets_list[obs]["user"].encode('utf-8')+"\t "+str(obs)+"\t "+str(exclu)
				csv_dim_txt+="\t "+str(lat1)+"\t "+str(lon1)+"\t "+str(lat2)+"\t "+str(lon2)+"\t "+str(surface_bbox)
				csv_dim_txt+="\t "+str(dims_changeset["surface"])+"\t "+ str(ratio)
				csv_dim_txt+="\t "+comment +"\t "+created_by +"\n"
				csv_dim.write(csv_dim_txt)
				csv_dim.flush()
		fi_changesets_list.close()
		if len(exclusion)>1 : exclusion.remove(9)
		#fi_changesets_objects.close()
		return exclusion

	#=========================================================


	def stats_init(self, ):
		zero={"changeset":0, "objects":0, "objects_c":0, "objects_m":0, "objects_d":0, "node_c":0, "way_c":0, "relation_c":0,"node_m":0, "way_m":0, "relation_m":0,"node_d":0, "way_d":0, "relation_d":0, "node_amenity":0, "node_shop":0, "node_craft":0, "node_office":0, "node_power":0, "node_place":0, "node_man_made":0, "node_history":0, "node_tourism":0, "node_leisure":0,"poi_total_nodes": 0, "way_highway":0, "way_waterway":0, "way_building":0, "way_landuse":0, "way_man_made":0}
		return zero

	def stats_sum_changeset_node(self, changeset, flag_excluded, stats, stats_excluded, id):
		#stats_excluded a enlever de liste de variables
		if(changeset["action"] == "create") :
			#print "create id=",id
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_c"] += 1
				if "tag" in changeset["data"]:
					if ("amenity" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_amenity"] += 1
					elif ("shop" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_shop"] += 1
					elif ("craft" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_craft"] += 1
					elif ("office" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_office"] += 1
					elif ("power" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_power"] += 1
					elif ("place" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_place"] += 1
					elif ("man_made" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_man_made"] += 1
					elif ("history" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_history"] += 1
					elif ("tourism" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_tourism"] += 1
					elif ("leisure" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_leisure"] += 1
		elif(changeset["action"] == "modify") :
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_m"] += 1
		elif(changeset["action"] == "delete") :
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_d"] += 1
		else:
			print "ERROR"
		stats[id]["stat"]["objects_c"]=stats[id]["stat"]["node_c"]
		stats[id]["stat"]["objects_m"]=stats[id]["stat"]["node_m"]
		stats[id]["stat"]["objects_d"]=stats[id]["stat"]["node_d"]
		stats[id]["stat"]["objects"]=stats[id]["stat"]["objects_c"]+stats[id]["stat"]["objects_m"]+stats[id]["stat"]["objects_d"]
		stats[id]["stat"]["poi_total_nodes"]= stats[id]["stat"]["node_amenity"] + stats[id]["stat"]["node_shop"]+ stats[id]["stat"]["node_craft"] + stats[id]["stat"]["node_office"]+ stats[id]["stat"]["node_power"] + stats[id]["stat"]["node_place"]+ stats[id]["stat"]["node_man_made"] + stats[id]["stat"]["node_history"]+ stats[id]["stat"]["node_tourism"] + stats[id]["stat"]["node_leisure"]
		return stats, stats_excluded


	def stats_sum_changeset_way_relation(self, changeset, flag_excluded, stats, stats_excluded, id):
		if(changeset["action"] == "create") :
			if changeset["type"] == "way":
				stats[id]["stat"]["way_c"] += 1
				if "tag" in changeset["data"]:
					if ("highway" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_highway"] += 1
					elif ("waterway" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_waterway"] += 1
					elif ("building" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_building"] += 1
					elif ("landuse" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_landuse"] += 1
					elif ("man_made" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_man_made"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_c"] += 1
		elif(changeset["action"] == "modify") :
			if changeset["type"] == "way":
				stats[id]["stat"]["way_m"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_m"] += 1
		elif(changeset["action"] == "delete") :
			if changeset["type"] == "way":
				stats[id]["stat"]["way_d"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_d"] += 1
		else:
			print "ERROR"
		stats[id]["stat"]["objects_c"]=stats[id]["stat"]["node_c"]+stats[id]["stat"]["way_c"]+stats[id]["stat"]["relation_c"]
		stats[id]["stat"]["objects_m"]=stats[id]["stat"]["node_m"]+stats[id]["stat"]["way_m"]+stats[id]["stat"]["relation_m"]
		stats[id]["stat"]["objects_d"]=stats[id]["stat"]["node_d"]+stats[id]["stat"]["way_d"]+stats[id]["stat"]["relation_d"]
		#stats[id]["stat"]["objects"]=stats[id]["stat"]["node_c"]+stats[id]["stat"]["node_m"]+stats[id]["stat"]["node_d"]+stats[id]["stat"]["way_c"]+stats[id]["stat"]["way_m"]+stats[id]["stat"]["way_d"]+stats[id]["stat"]["relation_c"]+stats[id]["stat"]["relation_m"]+stats[id]["stat"]["relation_d"]
		stats[id]["stat"]["objects"]=stats[id]["stat"]["objects_c"]+stats[id]["stat"]["objects_m"]+stats[id]["stat"]["objects_d"]
		#if (self._debug) : print "total objects ",str(id),str(stats[id]["stat"]["objects"])
		return stats, stats_excluded

	def stats_sum_changeset(self, changeset, flag_excluded, stats, stats_excluded, id):
		if(changeset["action"] == "create") :
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_c"] += 1
				if "tag" in changeset["data"]:
					if ("amenity" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_amenity"] += 1
					elif ("shop" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_shop"] += 1
					elif ("craft" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_craft"] += 1
					elif ("office" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_office"] += 1
					elif ("power" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_power"] += 1
					elif ("place" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_place"] += 1
					elif ("man_made" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_man_made"] += 1
					elif ("history" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_history"] += 1
					elif ("tourism" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_tourism"] += 1
					elif ("leisure" in changeset["data"]["tag"]) :
						stats[id]["stat"]["node_leisure"] += 1
			elif changeset["type"] == "way":
				stats[id]["stat"]["way_c"] += 1
				if "tag" in changeset["data"]:
					if ("highway" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_highway"] += 1
					elif ("waterway" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_waterway"] += 1
					elif ("building" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_building"] += 1
					elif ("landuse" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_landuse"] += 1
					elif ("man_made" in changeset["data"]["tag"]) :
						stats[id]["stat"]["way_man_made"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_c"] += 1
		elif(changeset["action"] == "modify") :
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_m"] += 1
			elif changeset["type"] == "way":
				stats[id]["stat"]["way_m"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_m"] += 1
		elif(changeset["action"] == "delete") :
			if changeset["type"] == "node" :
				stats[id]["stat"]["node_d"] += 1
			elif changeset["type"] == "way":
				stats[id]["stat"]["way_d"] += 1
			elif changeset["type"] == "relation":
				stats[id]["stat"]["relation_d"] += 1
		else:
			print "ERROR"
		stats[id]["stat"]["objects_c"]=stats[id]["stat"]["node_c"]+stats[id]["stat"]["way_c"]+stats[id]["stat"]["relation_c"]
		stats[id]["stat"]["objects_m"]=stats[id]["stat"]["node_m"]+stats[id]["stat"]["way_m"]+stats[id]["stat"]["relation_m"]
		stats[id]["stat"]["objects_d"]=stats[id]["stat"]["node_d"]+stats[id]["stat"]["way_d"]+stats[id]["stat"]["relation_d"]
		stats[id]["stat"]["objects"]=stats[id]["stat"]["objects_c"]+stats[id]["stat"]["objects_m"]+stats[id]["stat"]["objects_d"]
		stats[id]["stat"]["poi_total_nodes"]= stats[id]["stat"]["node_amenity"] + stats[id]["stat"]["node_shop"]+ stats[id]["stat"]["node_craft"] + stats[id]["stat"]["node_office"]+ stats[id]["stat"]["node_power"] + stats[id]["stat"]["node_place"]+ stats[id]["stat"]["node_man_made"] + stats[id]["stat"]["node_history"]+ stats[id]["stat"]["node_tourism"] + stats[id]["stat"]["node_leisure"]
		return stats, stats_excluded

	def max_datetime(self, changesets):
		vdate=[]
		maxdate='1'
		for id in changesets:
			if changesets[id]["created_at"]>maxdate:
				maxdate=changesets[id]["created_at"]
		t_date=datetime.strptime(maxdate,'%Y-%m-%dT%H:%M:%SZ')
		t_date2=t_date+timedelta(seconds=1)
		txt_maxdate = datetime.strftime(t_date2,'%Y-%m-%d %H:%M:%S')
		return txt_maxdate

	def min_datetime(self, changesets):
		vdate=[]
		mindate='1'
		for id in changesets:
			if changesets[id]["closed_at"]<mindate:
				mindate=changesets[id]["closed_at"]
		t_date=datetime.strptime(mindate,'%Y-%m-%dT%H:%M:%SZ')
		t_date2=t_date+timedelta(seconds=1)
		txt_mindate = datetime.strftime(t_date2,'%Y-%m-%d %H:%M:%S')
		return txt_mindate

	def appendChangesetsDict(self, changesets1,changesets2):
		# NOTE : changesets are updated by id. This avoids duplicates in case a changeset is open before and closed after the new start time.
		nb1=len(changesets1)
		nb2=len(changesets2)
		if (self._debug) :
			print "debug appendChangesetsDict ", nb1, nb2
		if nb1>0 and nb2>0 :
			for id in changesets2 :
				changesets1[id]=changesets2[id]
		else:
			if nb2 : changesets1=changesets2
		if (self._debug) :
			print "debug appendChangesetsDict changesets1 ", len(changesets1)
		return changesets1

	def getChangesets_max_min(self, username,min_lon, min_lat, max_lon, max_lat,
		date_from, date_to):
		from __main__ import osmApi
		if (self._debug): print "self.getChangesets("+str(username)+","+str(min_lon)+","+str(min_lat)+","+str(max_lon)+","+str(max_lat)+","+str(date_from)+","+str(date_to)+")"
		fini=0
		iter=0
		changesets={}
		while (fini==0) :
			iter+=1
			if (self._debug) : print username,iter,date_from, date_to
			s_changesets = osmApi.ChangesetsGet(min_lon, min_lat, max_lon, max_lat,
				username=username, closed_after=date_from,
				created_before=date_to)
			if (self._debug) : print "** debug getChangesets_max_min ** nb_changesets=",len(changesets), ", nb_s_changesets=",len(s_changesets)
			if iter==1 : changesets=s_changesets
			else : changesets=self.appendChangesetsDict(changesets,s_changesets)
			if (self._debug) : print "** debug getChangesets ** nb_changesets=",len(changesets)
			# protection indefinite loops
			if iter>=5 :
				print "\n**WARNING** ===============\nFUNCTION GETCHANGESET INTERRUPTED after 5 LOOPS\n==================\n"
				break
			if len(s_changesets)<100 :
				fini=1
				break
			if len(s_changesets)==0 :
				fini=1
				break
			date_from=self.max_datetime(s_changesets)
			if date_from==date_to :
				date_to=self.min_datetime(s_changesets)
				if (self._debug) : print username,iter,date_from, date_to, "** mindate **"
				if date_from!=date_to :
					s_changesets = osmApi.ChangesetsGet(min_lon, min_lat, max_lon, max_lat,
						username=username, closed_after=date_from,
						created_before=date_to)
				if (self._debug) : print "** debug getChangesets ** nb_changesets=",len(changesets), ", nb_s_changesets=",len(s_changesets)
				fini=1
		return changesets

	def getChangesets(self, username,min_lon, min_lat, max_lon, max_lat,
		date_from, date_to):
		from __main__ import osmApi
		# Time Segments command stack to extract changesets. Push segments and pop-up one by one. When 100 extracts returned, the specific Time segment is split in two segments and they are pushed to the stack.
		str_to_date=str(date_to)[0:10]+"Z00:00:00T"
		dt = datetime.strptime(str_to_date, "%Y-%m-%dZ%H:%M:%ST")
		#global changesets
		changesets=[]
		#1st step : 24h
		s_changesets=[]
		#if (username.lstrip()==" "): username=""
		if(self._debug) : print "\n", dt, " >> ChangesetsGet(username=(",username, "), date_from=", date_from, ", date_to=", date_to
		if (username.lstrip()==" "):
			s_changesets = osmApi.ChangesetsGet(min_lon, min_lat, max_lon, max_lat,
			closed_after=date_from,
			created_before=date_to)
		else :
			s_changesets = osmApi.ChangesetsGet(min_lon, min_lat, max_lon, max_lat,
			username=username, closed_after=date_from,
			created_before=date_to)
		if(self._debug): print "\n", dt, " >> iter=0  nb s_changesets=",len(s_changesets)
		if len(s_changesets)<100:
			changesets=s_changesets
			if (self._debug) : print dt, " === + nb s_changesets=",len(s_changesets), " = nb changesets=",len(changesets), " ==="
			# extract completed for the day
		else:
			# 2nd step : if more then 100 changesets for step1, then time slices to collect changesets
			time_segments=[]
			#	Time segments
			#0 : minute from beginning of day
			#1 : duration in minutes
			# Start strategy - day time segments 60 minutes
			time_segments.append([0,420])
			time_segments.append([420,60])
			time_segments.append([480,60])
			time_segments.append([540,60])
			time_segments.append([600,60])
			time_segments.append([660,60])
			time_segments.append([720,60])
			time_segments.append([780,60])
			time_segments.append([840,60])
			time_segments.append([900,60])
			time_segments.append([960,60])
			time_segments.append([1020,420])
			fini=0
			iter=0
			# protection infinite loop
			max_iter=200
			while (fini==0) :
				iter+=1
				if (self._debug): print "** debug ** time segments, iter=",iter,"\n",time_segments
				time_segment= time_segments.pop()
				if (self._debug): print "** debug ** time segment=", time_segment
				dt_from=dt+timedelta(minutes=time_segment[0])
				dt_to=dt+timedelta(minutes=(time_segment[0]+time_segment[1]))
				date_from=dt_from.strftime('%Y-%m-%dZ%H:%M:%ST')
				date_to=dt_to.strftime('%Y-%m-%dZ%H:%M:%ST')
				if (self._debug): print username,iter,date_from, date_to
				s_changesets=[]
				s_changesets = osmApi.ChangesetsGet(min_lon, min_lat, max_lon, max_lat,
					username=username, closed_after=date_from,
					created_before=date_to)
				if(self._debug): print "\n", dt, " >> iter ",iter, " nb s_changesets=",len(s_changesets)
				if len(s_changesets)<100:
					if iter==1 : changesets=s_changesets
					else : changesets=self.appendChangesetsDict(changesets,s_changesets)
					if (self._debug) : print "=== + nb s_changesets=",len(s_changesets), " = nb changesets=",len(changesets), " ==="
				# protection infinite loop
				if iter>=max_iter :
					print "\n Daily procedure interrupted, maximum iteration is ", max_iter, "\n"
					break
				if (len(s_changesets)>99) :
					# divide time segment in two portions
					half_time=time_segment[1]/2
					minute_1=time_segment[0]
					minute_2=minute_1+half_time
					if(self._debug): print ">> iter ", iter, " split in 2 time_segments (limit 100 changesets)"
					if(self._debug): print "   minute_1=", minute_1, " minute_2=", minute_2, " minutes=", half_time
					time_segment_1=[minute_1,half_time]
					time_segments.append(time_segment_1)
					if(self._debug): print ">> iter ", iter, " + n_time_segment 1 ", time_segment_1, "\n", time_segments
					time_segment_2=[minute_2,half_time]
					time_segments.append(time_segment_2)
					if(self._debug): print ">> iter ", iter, " + n_time_segment 2 ", time_segment_2, "\n", time_segments
				if len(time_segments)==0 :
					fini=1
					if(self._debug): print ">> TOTAL nb changesets=",len(changesets)
					break
		return changesets

	def getChangesetHist(self, cid,ekip,fi_changesets_objects):
		from __main__ import osmApi
		stat= {"changeset":0}
		for changesetData in osmApi.ChangesetDownload(cid):
			changesetData["ekip"]=ekip
			fi_changesets_objects.write(str(changesetData)+" \n")
			fi_changesets_objects.flush()
			changeset_json=json.dumps(changesetData,sort_keys=True)
		return stat

	def getChangesetStats(self, cid):
		from __main__ import osmApi
		stat= {"changeset":0,"node_c":0, "way_c":0, "relation_c":0,"node_m":0, "way_m":0, "relation_m":0,"node_d":0, "way_d":0, "relation_d":0, "node_amenity":0, "node_shop":0, "node_craft":0, "node_office":0, "node_power":0, "node_place":0, "node_man_made":0, "node_history":0, "node_tourism":0, "node_leisure":0, "way_highway":0, "way_waterway":0, "way_building":0, "way_landuse":0, "way_man_made":0, "flag_outside_zone":""}
		for changesetData in osmApi.ChangesetDownload(cid):
			fi_changesets_objects.write(str(changesetData)+" \n")
			fi_changesets_objects.flush()
			if(changesetData["action"] == "create") :
				if changesetData["type"] == "node" :
					stat["node_c"] += 1
					if "tag" in changesetData["data"]:
						if ("amenity" in changesetData["data"]["tag"]) :
							stat["node_amenity"] += 1
						elif ("shop" in changesetData["data"]["tag"]) :
							stat["node_shop"] += 1
						elif ("craft" in changesetData["data"]["tag"]) :
							stat["node_craft"] += 1
						elif ("office" in changesetData["data"]["tag"]) :
							stat["node_office"] += 1
						elif ("power" in changesetData["data"]["tag"]) :
							stat["node_power"] += 1
						elif ("place" in changesetData["data"]["tag"]) :
							stat["node_place"] += 1
						elif ("man_made" in changesetData["data"]["tag"]) :
							stat["node_man_made"] += 1
						elif ("history" in changesetData["data"]["tag"]) :
							stat["node_history"] += 1
						elif ("tourism" in changesetData["data"]["tag"]) :
							stat["node_tourism"] += 1
						elif ("leisure" in changesetData["data"]["tag"]) :
							stat["node_leisure"] += 1
				elif changesetData["type"] == "way":
					stat["way_c"] += 1
					if "tag" in changesetData["data"]:
						if ("highway" in changesetData["data"]["tag"]) :
							stat["way_highway"] += 1
						elif ("waterway" in changesetData["data"]["tag"]) :
							stat["way_waterway"] += 1
						elif ("building" in changesetData["data"]["tag"]) :
							stat["way_building"] += 1
						elif ("landuse" in changesetData["data"]["tag"]) :
							stat["way_landuse"] += 1
						elif ("man_made" in changesetData["data"]["tag"]) :
							stat["way_man_made"] += 1
				elif changesetData["type"] == "relation":
					stat["relation_c"] += 1
			elif(changesetData["action"] == "modify") :
				if changesetData["type"] == "node" :
					stat["node_m"] += 1
				elif changesetData["type"] == "way":
					stat["way_m"] += 1
				elif changesetData["type"] == "relation":
					stat["relation_m"] += 1
			elif(changesetData["action"] == "delete") :
				if changesetData["type"] == "node" :
					stat["node_d"] += 1
				elif changesetData["type"] == "way":
					stat["way_d"] += 1
				elif changesetData["type"] == "relation":
					stat["relation_d"] += 1
			else:
				print "ERROR"
		return stat

	def updateStat(self, dict1, dict2):
		return dict((n, dict2.get(n, 0)+ dict2.get(n, 0)) for n in set(dict1)|set(dict2))

	def daterange(self, start_date, end_date):
		if (self._debug) : print "daterange : " + str(range(int ((end_date - start_date).days +1)))
		for n in range(int ((end_date - start_date).days +1)):
			if (self._debug) : print "daterange : " + str(n)
			yield start_date + timedelta(n)
		return

	def daily_hist(self, username,min_lon, min_lat, max_lon,max_lat,single_date,
		t_from_date,t_to_date,fi_changesets_list,fi_changesets_objects,ekip,stats,stats_team) :
		if (self._debug) : print "daily statistics, single_date="+str(single_date)[0:10]
		date_from=str(t_from_date)[0:10]+"T00:00:00Z"
		date_to=str(t_from_date)[0:10]+"T23:59:59Z"
		if (self._debug) : print str(date_from)
		if (self._debug) : print str(date_to)
		if (username==" "):username=""
		if (self._debug) : print "username=(",username,")"
		changesets = self.getChangesets(username,min_lon, min_lat, max_lon,
			max_lat, date_from, date_to)
		nb_daily_changesets=len(changesets)
		if (self._debug) : print "Daily TOTAL nb_changesets=", nb_daily_changesets
		print str(date_from), str(date_to),len(changesets)
		if (nb_daily_changesets>0):
			fi_changesets_list.write(str(changesets)+" \n")
			fi_changesets_list.flush()
			for id in changesets:
				csstat= self.getChangesetHist(id,ekip,fi_changesets_objects)
				stats["changeset"] += 1
		return changesets, stats, stats_team, nb_daily_changesets

	def daily_statistics(self, username,min_lon, min_lat, max_lon,max_lat,single_date,
		t_from_date,t_to_date,csv,csv_team,csv_changeset,csv_dim,ekip,stats,stats_team) :
		if (self._debug) : print "daily statistics, single_date="+str(single_date)[0:10]
		date_from=str(t_from_date)[0:10]+"T00:00:00Z"
		date_to=str(t_from_date)[0:10]+"T23:59:59Z"
		if (self._debug) : print str(date_from)
		if (self._debug) : print str(date_to)
		if len(username)>0 :
			changesets = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T00:00:00Z",
				str(t_from_date)[0:10]+"T23:59:59Z")
		else:
			changesets = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T00:00:00Z",
				str(t_from_date)[0:10]+"T03:59:59Z")
			if (self._debug) : print "** debug daily_statistics ** nb_changesets=",len(changesets)
			changesets1 = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T04:00:00Z",
				str(t_from_date)[0:10]+"T07:59:59Z")
			changesets=self.appendChangesetsDict(changesets,changesets1)
			if (self._debug) : print "** debug daily_statistics ** nb_changesets=",len(changesets)
			changesets1 = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T08:00:00Z",
				str(t_from_date)[0:10]+"T11:59:59Z")
			changesets=self.appendChangesetsDict(changesets,changesets1)
			if (self._debug) : print "** debug daily_statistics ** nb_changesets=",len(changesets)
			changesets1 = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T12:00:00Z",
				str(t_from_date)[0:10]+"T15:59:59Z")
			changesets=self.appendChangesetsDict(changesets,changesets1)
			if (self._debug) : print "** debug daily_statistics ** nb_changesets=",len(changesets)
			changesets1 = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T16:00:00Z",
				str(t_from_date)[0:10]+"T17:59:59Z")
			changesets=self.appendChangesetsDict(changesets,changesets1)
			if (self._debug) : print "** debug daily_statistics ** nb_changesets=",len(changesets)
			changesets1 = self.getChangesets(username,min_lon, min_lat, max_lon, max_lat,
				str(t_from_date)[0:10]+"T20:00:00Z",
				str(t_from_date)[0:10]+"T23:59:59Z")
			changesets=self.appendChangesetsDict(changesets,changesets1)
		if (self._debug) : print "** debug daily_statistics ** nb_changesets=", len(changesets)
		nb_daily_changesets=len(changesets)
		if (nb_daily_changesets>0):
			fi_changesets_list.write(str(changesets)+" \n")
			fi_changesets_list.flush()
			if (self._debug) : print "** debug daily_statistics ** nb_daily_changesets="+ str(nb_daily_changesets)
			for id in changesets:
				csstat= self.getChangesetStats(id)
				stats["changeset"] += 1
				stats["node_c"] += csstat["node_c"]
				stats["way_c"]  += csstat["way_c"]
				stats["relation_c"] += csstat["relation_c"]
				stats["node_m"] += csstat["node_m"]
				stats["way_m"]  += csstat["way_m"]
				stats["relation_m"] += csstat["relation_m"]
				stats["node_d"] += csstat["node_d"]
				stats["way_d"]  += csstat["way_d"]
				stats["relation_d"] += csstat["relation_d"]
				stats["node_amenity"] += csstat["node_amenity"]
				stats["node_shop"] += csstat["node_shop"]
				stats["node_craft"] += csstat["node_craft"]
				stats["node_office"] += csstat["node_office"]
				stats["node_power"] += csstat["node_power"]
				stats["node_place"] += csstat["node_place"]
				stats["node_man_made"] += csstat["node_man_made"]
				stats["node_history"] += csstat["node_history"]
				stats["node_tourism"] += csstat["node_tourism"]
				stats["node_leisure"] += csstat["node_leisure"]
				stats["way_highway"] += csstat["way_highway"]
				stats["way_waterway"] += csstat["way_waterway"]
				stats["way_building"] += csstat["way_building"]
				stats["way_landuse"] += csstat["way_landuse"]
				stats["way_man_made"] += csstat["way_man_made"]
				# users
				day=datetime.strptime(single_date,'%Y-%m-%d')
		if (self._debug) : print str(ekip) +" *debug*, " +str(username) +", " + str(stats["changeset"]) + ", " + str(stats["node_c"]) + ", " + str(stats["way_c"]) + ", " + str(stats["relation_c"])+ ", " + str(stats["node_m"]) + ", " + str(stats["way_m"]) + ", " + str(stats["relation_m"])+ ", " + str(stats["node_d"]) + ", " + str(stats["way_d"]) + ", " + str(stats["relation_d"]) + ", " + str(stats["node_amenity"]) + ", " + str(stats["node_shop"]) + ", " + str(stats["node_craft"]) + ", " + str(stats["node_office"]) + ", " + str(stats["node_power"]) + ", " + str(stats["node_place"])  + ", " + str(stats["node_man_made"]) + ", " + str(stats["node_history"]) + ", " + str(stats["node_tourism"]) + ", " + str(stats["node_leisure"])
		return changesets, stats, stats_team, nb_daily_changesets

	def ekip_hist(self, user,min_lon, min_lat, max_lon,
		max_lat,from_date,to_date,fi_changesets_list,fi_changesets_objects,ekip,stats_team) :
		stats= {"changeset":0}
		nb_changesets=0
		nb_daily_changesets=0
		username=user.lstrip()
		str_from_date=str(from_date)[0:10]+" 00:00:00"
		str_to_date=str(to_date)[0:10]+" 00:00:00"
		if (self._debug) : print str(str_from_date)
		if (self._debug) : print str(str_to_date)
		t_from_date=datetime.strptime(str_from_date,'%Y-%m-%d %H:%M:%S')
		t_to_date=datetime.strptime(str_to_date,'%Y-%m-%d %H:%M:%S')
		if (self._debug) : print "t_from_date " + str(t_from_date)
		if (self._debug) : print "t_to_date " + str(t_to_date)
		time_from="T00:00:00Z"
		for single_date in self.daterange(t_from_date, t_to_date):
			if (self._debug): print "loop single_date = "+ str(single_date)
			self.daily_hist(username,min_lon, min_lat, max_lon,
				max_lat,single_date,single_date,single_date,fi_changesets_list,fi_changesets_objects,ekip,stats,stats_team)
			nb_changesets+=nb_daily_changesets
		stats_team["changeset"] += stats["changeset"]
		# end adding each day to the statistics
		print str(ekip) +", " +str(user) +", " + str(stats["changeset"])
		return  stats, stats_team, nb_changesets

	def summary_statistics(self, user,min_lon, min_lat, max_lon,
		max_lat,from_date,to_date,csv,csv_team,csv_changeset,csv_dim,ekip,stats_team) :
		stats= {"changeset":0,"node_c":0, "way_c":0, "relation_c":0,"node_m":0, "way_m":0, "relation_m":0,"node_d":0, "way_d":0, "relation_d":0, "node_amenity":0, "node_shop":0, "node_craft":0, "node_office":0, "node_power":0, "node_place":0, "node_man_made":0, "node_history":0, "node_tourism":0, "node_leisure":0, "way_highway":0, "way_waterway":0, "way_building":0, "way_landuse":0, "way_man_made":0, "flag_outside_zone":""}
		nb_changesets=0
		nb_daily_changesets=0
		username=user
		str_from_date=str(from_date)[0:10]+" 00:00:00"
		str_to_date=str(to_date)[0:10]+" 00:00:00"
		if (self._debug) : print str(str_from_date)
		if (self._debug) : print str(str_to_date)
		t_from_date=datetime.strptime(str_from_date,'%Y-%m-%d %H:%M:%S')
		t_to_date=datetime.strptime(str_to_date,'%Y-%m-%d %H:%M:%S')
		if (self._debug) : print "t_from_date " + str(t_from_date)
		if (self._debug) : print "t_to_date " + str(t_to_date)
		time_from="T00:00:00Z"
		for single_date in self.daterange(t_from_date, t_to_date):
			if (self._debug): print "loop single_date = "+ str(single_date)
			self.daily_statistics(username,min_lon, min_lat, max_lon,
				max_lat,single_date,single_date,single_date,csv,csv_team,csv_changeset,csv_dim,ekip,stats,stats_team)
		stats_team["changeset"] += stats["changeset"]
		stats_team["node_c"] += stats["node_c"]
		stats_team["way_c"]  += stats["way_c"]
		stats_team["relation_c"] += stats["relation_c"]
		stats_team["node_m"] += stats["node_m"]
		stats_team["way_m"]  += stats["way_m"]
		stats_team["relation_m"] += stats["relation_m"]
		stats_team["node_d"] += stats["node_d"]
		stats_team["way_d"]  += stats["way_d"]
		stats_team["relation_d"] += stats["relation_d"]
		stats_team["node_amenity"] += stats["node_amenity"]
		stats_team["node_shop"] += stats["node_shop"]
		stats_team["node_office"] += stats["node_office"]
		stats_team["node_power"] += stats["node_power"]
		stats_team["node_place"] += stats["node_place"]
		stats_team["node_man_made"] += stats["node_man_made"]
		stats_team["node_history"] += stats["node_history"]
		stats_team["node_tourism"] += stats["node_tourism"]
		stats_team["node_leisure"] += stats["node_leisure"]
		stats_team["way_highway"] += stats["way_highway"]
		stats_team["way_waterway"] += stats["way_waterway"]
		stats_team["way_building"] += stats["way_building"]
		stats_team["way_landuse"] += stats["way_landuse"]
		stats_team["way_man_made"] += stats["way_man_made"]

		# teams
		print str(ekip) +", " +str(user) +", " + str(stats["changeset"]) + ", " + str(stats["node_c"]) + ", " + str(stats["way_c"]) + ", " + str(stats["relation_c"])+ ", " + str(stats["node_m"]) + ", " + str(stats["way_m"]) + ", " + str(stats["relation_m"])+ ", " + str(stats["node_d"]) + ", " + str(stats["way_d"]) + ", " + str(stats["relation_d"]) + ", " + str(stats["node_amenity"]) + ", " + str(stats["node_shop"]) + ", " + str(stats["node_office"]) + ", " + str(stats["node_power"]) + ", " + str(stats["node_place"]) + ", " + str(stats["node_man_made"]) + ", " + str(stats["node_history"]) + ", " + str(stats["node_tourism"])+ ", " + str(stats["node_leisure"])+ ", " + str(stats["way_highway"])+ ", " + str(stats["way_waterway"])+ ", " + str(stats["way_building"])+ ", " + str(stats["way_landuse"])+ ", " + str(stats["way_man_made"])
		csv.write(str(ekip) +"\t " +str(user) +"\t " + str(stats["changeset"]) + "\t " + str(stats["node_c"]) + "\t " + str(stats["way_c"]) + "\t " + str(stats["relation_c"])+ "\t " + str(stats["node_m"]) + "\t " + str(stats["way_m"]) + "\t " + str(stats["relation_m"])+ "\t " + str(stats["node_d"]) + "\t " + str(stats["way_d"]) + "\t " + str(stats["relation_d"])
		+ "\t " + str(stats["node_amenity"]) + "\t " + str(stats["node_shop"]) + "\t " + str(stats["node_office"]) + "\t " + str(stats["node_power"]) + "\t " + str(stats["node_place"]) + "\t " + str(stats["node_man_made"]) + "\t " + str(stats["node_history"]) + "\t " + str(stats["node_tourism"])+ "\t " + str(stats["node_leisure"])+ "\t " + str(stats["way_highway"])+ "\t " + str(stats["way_waterway"])+ "\t " + str(stats["way_building"])+ "\t " + str(stats["way_landuse"])+ "\t " + str(stats["way_man_made"])  + "\n")
		csv.flush()
		return  stats, stats_team, nb_changesets

	def API6_Collect_Changesets(self,team_from,team_to,from_date,to_date,min_lon,max_lon,min_lat,max_lat,prefix, users=None) :
		global ekip
		self.verif_users(users)
		print "\n","="*100
		if (self._debug) : print "\ndebug=",self._debug
		ligne="=" * 100
		print "\n", ligne, "\nAPI6_Collect_Changesets(team_from=",team_from, ", team_to=", team_to, ", from_date=", from_date, ", to_date=",to_date
		print "\t\tmin_lon=", min_lon, ", max_lon=", max_lon, ", min_lat=", min_lat, ", max_lat=", max_lat, ", prefix=", prefix, ", users=xxx)"
		print "Output Directory : ",self.rep
		print "Output files prefix : " + prefix+from_date+"-"+to_date +"\n" + ligne
		try:
			os.chdir(self.rep)
		except:
			sys.exit ("\n ERROR OsmContributorStats module. Revise the rep parameter. DIRECTORY NOT FOUND :" + self.rep+"\n")
		#
		time_from="T00:00:00Z"
		time_to="T23:59:59Z"
		nom_changeset_list=prefix+from_date+"-"+to_date+"_changeset_hist_list.txt"
		nom_changeset_objects=prefix+from_date+"-"+to_date+"_changeset_hist_objects.txt"
		#
		print "="*100
		fi_changesets_list = open(nom_changeset_list, 'wb')
		fi_changesets_objects = open(nom_changeset_objects, 'wb')

		print "ekip, user, changeset"
		for ekip in range(team_from,team_to+1):
			stats_team= {"changeset":0}
			print "\n ekip " + str(ekip)
			for user in users[ekip]:
				try:
					self.ekip_hist(user,min_lon, min_lat, max_lon,
                        max_lat,from_date,to_date,fi_changesets_list,fi_changesets_objects,ekip,stats_team)
                    # end of team - print in summary file by team
				except:
					continue

			print str(ekip) +", " +str(from_date[1:10])+" - " + str(to_date[1:10])+", " + str(stats_team["changeset"])
		fi_changesets_list.close()
		fi_changesets_objects.close()
		print "API6_Collect_Changesets Completed."
		return None

	def is_numeric(self, var):
		try:
			float(var)
			return True
		except ValueError:
			return False

	def Changesets_Contributor_Statistics(self,team_from,team_to,from_date,to_date,min_lon,max_lon,min_lat,max_lat,prefix, users=None) :
		#global changesets
		global csv
		global csv_team
		global csv_changeset
		global ekip
		global fi_changesets_list
		global fi_changesets_objects
		if users != None:
			print "users existe : ",users
		else:
			team_from=0
			team_to=0
			users=[None]*2
			users[0]=[""]
			print 'users=none non defini, valeur par defaut, vide ', users
		print "\n","="*100
		if (self._debug): print "\ndebug=",self._debug
		ligne="=" * 100
		print "\n", ligne, "\nChangesets_Contributor_Statistics(team_from=",team_from, ", team_to=", team_to, ", from_date=", from_date, ", to_date=",to_date, ","
		print "\t\tmin_lon=", min_lon, ", max_lon=", max_lon, ", min_lat=", min_lat, ", max_lat=", max_lat, ", prefix=", prefix, ", users=xxx)"

		print "Output Directory : ",self.rep
		print "Output files prefix : " + prefix+from_date+"-"+to_date +"\n" + ligne
		os.chdir(self.rep)
		#
		time_from="T00:00:00Z"
		time_to="T23:59:00Z"
		nom_changeset_list=prefix+from_date+"-"+to_date+"_changeset_hist_list.txt"
		nom_changeset_objects=prefix+from_date+"-"+to_date+"_changeset_hist_objects.txt"
		nom_changeset_objects_json=prefix+from_date+"-"+to_date+"_changeset_hist_objects.json"
		nom_csv_dim=prefix+from_date+"-"+to_date+"_changeset_dim.csv"
		nom_date=prefix+from_date+"-"+to_date
		prefix_users=prefix+from_date+"-"+to_date+".csv"
		prefix_team=prefix+from_date+"-"+to_date+"-team.csv"
		prefix_changesets=prefix+from_date+"-"+to_date+"-changeset.csv"
		#
		csv = open(prefix_users, 'wb')
		csv_team = open(prefix_team, 'wb')
		csv_changeset = open(prefix_changesets, 'wb')
		csv_dim = open(nom_csv_dim, 'wb')
		csv_dim.write("user\t id\t exclu\t min_lat\t min_lon\t max_lat\t max_lon\t surface_bbox\t surface\t ratio\t comment\t editor\t created_by \n")
		csv_dim.flush()
		imp_col_changesets=  "flag \t day \t hour \t ekip \t osmuser_uid \t osmuser_name \t changeset \t changeset_id \t editor \t created_by \t comment \t objects \t objects_c \t objects_m \t objects_d \t node_c \t way_c \t relation_c \t node_m \t way_m \t relation_m \t node_d \t way_d \t relation_d \t poi_total_nodes \t node_amenity \t node_shop \t node_office \t node_power \t node_place \t node_man_made \t node_history \t node_tourism \t node_leisure \t way_highway \t way_waterway \t way_building \t way_landuse \t way_man_made \t min_lon \t min_lat \t max_lon \t max_lat"
		csv_changeset.write(imp_col_changesets+"\n")
		csv_changeset.flush()

		# 1. from list of changesets, determine changesets to flag for exclusion (ie. bot and massive edits, only nodes inside the Study zone are retained)
		# - criteria, their surface 10 times greater then the bbox
		exclusion=self.Changesets_to_Exclude(
		nom_changeset_list=nom_changeset_list,
		min_lon=min_lon,max_lon=max_lon,min_lat=min_lat,max_lat=max_lat,csv_dim=csv_dim)

		# 2. Calculate Statistics from  Changeset_objets - Exceptions for changesets flagged for Exclusion
		fi_changesets_objects= open(nom_changeset_objects, 'r')

		# total by person
		nb=0
		changesets=[]
		stats_changeset={}
		stats_excluded_changeset={}
		stats_user={}
		stats_excluded_user={}
		for read_data in fi_changesets_objects.readlines():
			nb+=1
			changeset=ast.literal_eval(read_data)
			changeset_id=changeset["data"]["changeset"]
			uid=changeset["data"]["uid"]
			user=str(changeset["data"]["user"].encode('utf-8'))
			if "ekip" in changeset: ekip=str(changeset["ekip"])
			else :
				if "team" in changeset: ekip=str(changeset["team"])
				else : ekip="0"
			flag_excluded=0
			if (changeset_id in exclusion) :
				flag_excluded=1
				if not stats_excluded_changeset.has_key(changeset_id):
					stats_excluded_changeset[changeset_id]={"ekip":ekip,"uid":uid, "user":user, "flag_outside_zone":flag_excluded,"stat":self.stats_init()}
				if not stats_excluded_user.has_key(changeset_id):
					stats_excluded_user[changeset_id]={"ekip":ekip,"uid":uid, "user":user, "flag_outside_zone":flag_excluded,"stat":self.stats_init()}
			if not stats_changeset.has_key(changeset_id):
				stats_changeset[changeset_id]={"ekip":ekip,"uid":uid, "user":user, "flag_outside_zone":flag_excluded,"stat":self.stats_init()}
			(stats_changeset, stats_excluded_changeset)=self.stats_sum_changeset(changeset,flag_excluded,stats_changeset,stats_excluded_changeset,changeset_id)
			if not stats_user.has_key(uid):
				stats_user[uid]={"ekip":ekip,"uid":uid, "user":user, "flag_outside_zone":"","stat":self.stats_init()}
			(stats_user, stats_excluded_user)=self.stats_sum_changeset(changeset,flag_excluded,stats_user,stats_excluded_user,uid)

		fi_changesets_objects.close()
		if (self._debug): print "\nINPUT : NB Objects=",nb
		nb=0
		tchangesets_list=[]
		changesets_list={}
		stats_user_list={}
		fi_changesets_list= open(nom_changeset_list, 'r')
		# nb changesets from changesets_list
		for read_list in fi_changesets_list.readlines():
			tchangesets_list=ast.literal_eval(read_list)
			# one line contains many changeset lists
			for changeset_id in tchangesets_list:
				nb+=1
				if not changesets_list.has_key(changeset_id) :
					changesets_list[changeset_id]=tchangesets_list[changeset_id]

				# stats_changeset
				if (self._debug and nb<3):
					print "\n Changeset changeset_id=",str(changeset_id)
					print changesets_list[changeset_id]

				# csv users
				uid=changesets_list[changeset_id]["uid"]
				if (self._debug and nb<3) : print "\nfi_changesets_list uid=",uid,"\n",changesets_list[changeset_id]
				user=changesets_list[changeset_id]["user"]
				if isinstance(user, unicode):
					user = user.encode('utf-8')
				if not stats_user_list.has_key(uid):
					stats_user_list[uid]={"uid":uid, "user":user,"changeset":0,"changeset_excluded":0}
				if (changeset_id in exclusion) :
					stats_user_list[uid]["changeset_excluded"]+=1
				else:
					stats_user_list[uid]["changeset"]+=1
		fi_changesets_list.close()
		print nb, " Changesets"," nb stats_user_list= ", len(stats_user_list)
		print "-"*100
		imp_col=  "ekip \t osmuser_uid\t osmuser_name\t changeset\t objects \t objects_c \t objects_m \t objects_d\t node_c\t way_c\t relation_c\t node_m\t way_m\t relation_m\t node_d\t way_d\t relation_d\t poi_total_nodes\t node_amenity\t node_shop\t node_office\t node_power\t node_place\t node_man_made\t node_history\t node_tourism\t node_leisure\t way_highway\t way_waterway\t way_building\t way_landuse\t way_man_made"
		print imp_col
		csv.write(imp_col+"\n")
		csv.write("\t \t"+nom_date+"\t\tBBOX : \t"+str(min_lon)+"\t"+ str(min_lat)+"\t"+str(max_lon)+"\t"+ str(max_lat)+"\n")
		csv.flush()
		csv_team.write(imp_col+"\n")
		csv_team.flush()
		stats_ekip={}
		users_ekip={}
		nbc=0
		for changeset_id in stats_changeset:
			nbc+=1
			changesets_l=changesets_list[changeset_id]
			if (self._debug and nb<3) :
				print "\n** changesets_list"
				print changesets_list[changeset_id]
				print "** stats_changeset"
				print stats_changeset[changeset_id]
			uid=stats_changeset[changeset_id]["uid"]
			# take account of accented characters
			# Lubeck L\xc3\xbcbeck probleme
			# Carsten G\xc3\xbcse
			user=str(stats_changeset[changeset_id]["user"])
			#Probleme user= Lubeck
			if uid==55462: user="Lubeck"
			#if (uid==55462) : user="Lubeck"
			#user=user.encode('utf-8')
			if isinstance(user, unicode):
				user = user.encode('utf-8')
			import re
			user= re.sub(r'[\xdf-\xfc]', ' ', user)
			if "closed_at" in changesets_list[changeset_id] :
				closed_at=changesets_list[changeset_id]["closed_at"]
			else : closed_at="99"
			if isinstance(closed_at, unicode):
				closed_at = closed_at.encode('utf-8')

			day_closed_at=str(closed_at)[1:10]
			hour_closed_at=str(closed_at)[11:13]
			if "comment" in changesets_l["tag"] :
				comment=changesets_l["tag"]["comment"]
				if isinstance(comment, unicode):
					comment = comment.encode('utf-8')
			else:
				comment=""
				comment= comment.replace(r'\xc3\xa9', 'é')
			# comment=="'Hausnummern Blauenstra\xc3\x9fe B\xc3\xbcchig'" :
			if (uid==35468 and changeset_id==3645581) :
				comment="House numbers Blauenstraaye Baychig"
			if "created_by" in changesets_l["tag"] :
				created_by=changesets_list[changeset_id]["tag"]["created_by"].encode('utf-8')
				if isinstance(created_by, unicode):
					created_by = created_by.encode('utf-8')
				#created_by= re.sub(r'[\x00-\x1f\x80-\xff]', ' ', created_by)
				tcreated_by=created_by.lower()
				if  (tcreated_by.count("josm",0,4)>0) :
					editor="1.JOSM"
				elif (tcreated_by.count("potlatch",0,8)>0) :
					editor="2.Potlatch"
				elif (tcreated_by.count("merkaartor",0,10)>0) :
					editor="3.Merkaartor"
				elif (tcreated_by.count("id",0,2)>0) :
					editor="4. ID"
				else : editor="5. Other"
			else:
				created_by=""
				editor="5. Other"
			flag_outside_zone=str(stats_changeset[changeset_id]["flag_outside_zone"])
			stats_c=stats_changeset[changeset_id]["stat"]
			if (self._debug and nb<3) :
				print stats_c
				print changesets_l
			users="1"
			imp= flag_outside_zone + " \t" + day_closed_at +' \t"' + hour_closed_at +  '"  \t' + str(ekip) +"\t" +str(uid) +"\t" + user +"\t" +str(users) + "\t" + str(changeset_id) + "\t"
			imp+= editor  + "\t" + created_by + "   \t"
			imp += comment + "   \t"
			imp += str(stats_c["objects"]) + " \t" +str(stats_c["objects_c"]) + " \t" +str(stats_c["objects_m"]) + " \t" +str(stats_c["objects_d"]) + " \t" + str(stats_c["node_c"]) + " \t" + str(stats_c["way_c"]) + " \t" + str(stats_c["relation_c"])+ " \t" + str(stats_c["node_m"]) + " \t" + str(stats_c["way_m"]) + " \t" + str(stats_c["relation_m"])+ " \t" + str(stats_c["node_d"]) + " \t" + str(stats_c["way_d"]) + " \t" + str(stats_c["relation_d"]) + " \t"
			imp += str(stats_c["poi_total_nodes"])
			imp += " \t" + str(stats_c["node_amenity"])
			imp += " \t" + str(stats_c["node_shop"]) + " \t" + str(stats_c["node_office"]) + " \t" + str(stats_c["node_power"]) + " \t" + str(stats_c["node_place"]) + " \t" + str(stats_c["node_man_made"]) + " \t" + str(stats_c["node_history"]) + " \t" + str(stats_c["node_tourism"])+ " \t" + str(stats_c["node_leisure"])+ " \t" + str(stats_c["way_highway"])+ " \t" + str(stats_c["way_waterway"])+ " \t" + str(stats_c["way_building"])+ " \t" + str(stats_c["way_landuse"])+ " \t" + str(stats_c["way_man_made"])+" \t"
			imp += str(changesets_l["min_lon"].encode('utf-8')) + " \t" + str(changesets_l["min_lat"].encode('utf-8')) + " \t" + str(changesets_l["max_lon"].encode('utf-8')) + " \t" + str(changesets_l["max_lat"].encode('utf-8')) + "\n"
			csv_changeset.write(imp)
			csv_changeset.flush()

		# stats by user
		for uid in stats_user:
			#nb+=1
			if (self._debug):  print "\n\nDebug uid=", uid
			imp= stats_user[uid]["ekip"].rjust(3," ") +"\t " + str(uid).rjust(10," ") +"\t " + stats_user[uid]["user"].ljust(20," ") +"\t " + str(stats_user[uid]["stat"]["changeset"]).rjust(5," ") +"\t " + str(stats_user[uid]["stat"]["objects"]).rjust(12," ") + "\t " + str(stats_user[uid]["stat"]["objects_c"]).rjust(12," ") + "\t " + str(stats_user[uid]["stat"]["objects_m"]).rjust(12," ") + "\t " + str(stats_user[uid]["stat"]["objects_d"]).rjust(12," ") + "\t " + str(stats_user[uid]["stat"]["node_c"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["way_c"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["relation_c"]).rjust(5," ")+ "\t " + str(stats_user[uid]["stat"]["node_m"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["way_m"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["relation_m"]).rjust(5," ")+ "\t " + str(stats_user[uid]["stat"]["node_d"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["way_d"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["relation_d"]).rjust(5," ") + "\t " + str(stats_user[uid]["stat"]["poi_total_nodes"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_amenity"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_shop"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_office"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_power"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_place"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_man_made"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_history"]).rjust(4," ") + "\t " + str(stats_user[uid]["stat"]["node_tourism"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["node_leisure"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["way_highway"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["way_waterway"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["way_building"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["way_landuse"]).rjust(4," ")+ "\t " + str(stats_user[uid]["stat"]["way_man_made"]).rjust(4," ")
			print imp
			csv.write(imp+"\n")
			csv.flush()
			ekip=str(stats_user[uid]["ekip"])
			#Users UID List by team
			if not users_ekip.has_key(ekip):
				users_ekip[ekip]=[]
			if not uid in users_ekip : users_ekip[ekip].append(uid)
			#Stats by team
			if not stats_ekip.has_key(ekip):
				stats_ekip[ekip]={"ekip":ekip,"stat":self.stats_init()}
			for key,value in stats_user[uid]["stat"].items():
				stats_ekip[str(ekip)]["stat"][key]+=value
		csv.write("\n\n"+imp_col+"\n")
		csv.flush()
		for ekip in stats_ekip:
			imp= str(ekip).rjust(3," ") + "\t " + " ".rjust(10," ") + "\t " + "Equipe".ljust(20," ") + "\t " + str(stats_ekip[ekip]["stat"]["changeset"]).rjust(5," ") +"\t " + str(stats_ekip[ekip]["stat"]["objects"]).rjust(12," ") + "\t " + str(stats_ekip[ekip]["stat"]["objects_c"]).rjust(12," ") + "\t " + str(stats_ekip[ekip]["stat"]["objects_m"]).rjust(12," ") + "\t " + str(stats_ekip[ekip]["stat"]["objects_d"]).rjust(12," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_c"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["way_c"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["relation_c"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_m"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["way_m"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["relation_m"]).rjust(5," ")+ "\t " + str(stats_ekip[ekip]["stat"]["node_d"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["way_d"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["relation_d"]).rjust(5," ") + "\t " + str(stats_ekip[ekip]["stat"]["poi_total_nodes"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_amenity"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_shop"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_office"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_power"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_place"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_man_made"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_history"]).rjust(4," ") + "\t " + str(stats_ekip[ekip]["stat"]["node_tourism"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["node_leisure"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["way_highway"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["way_waterway"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["way_building"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["way_landuse"]).rjust(4," ")+ "\t " + str(stats_ekip[ekip]["stat"]["way_man_made"]).rjust(4," ")
			print imp
			csv.write(imp+"\n")
			csv.flush()
			csv_team.write(imp+"\n")
			csv_team.flush()
		grand_total=self.stats_init()
		nbuser=0
		for ekip in stats_ekip:
			nbuser+=1
			for key,value in stats_ekip[ekip]["stat"].items():
				grand_total[key]+=value
		imp= " ".rjust(3," ") +"\t " +" ".rjust(10," ") +"\t " +"GRAND TOTAL".ljust(20," ") +"\t " + str(grand_total["changeset"]).rjust(5," ") +"\t " + str(grand_total["objects"]).rjust(12," ") + "\t " + str(grand_total["objects_c"]).rjust(12," ") + "\t " + str(grand_total["objects_m"]).rjust(12," ") + "\t " + str(grand_total["objects_d"]).rjust(12," ") + "\t " + str(grand_total["node_c"]).rjust(5," ") + "\t " + str(grand_total["way_c"]).rjust(5," ") + "\t " + str(grand_total["relation_c"]).rjust(5," ") + "\t " + str(grand_total["node_m"]).rjust(5," ") + "\t " + str(grand_total["way_m"]).rjust(5," ") + "\t " + str(grand_total["relation_m"]).rjust(5," ") + "\t " + str(grand_total["node_d"]).rjust(5," ") + "\t " + str(grand_total["way_d"]).rjust(5," ") + "\t " + str(grand_total["relation_d"]).rjust(5," ") + "\t " + str(grand_total["poi_total_nodes"]).rjust(4," ") + "\t " + str(grand_total["node_amenity"]).rjust(4," ") + "\t " + str(grand_total["node_shop"]).rjust(4," ") + "\t " + str(grand_total["node_office"]).rjust(4," ") + "\t " + str(grand_total["node_power"]).rjust(4," ") + "\t " + str(grand_total["node_place"]).rjust(4," ") + "\t " + str(grand_total["node_man_made"]).rjust(4," ") + "\t " + str(grand_total["node_history"]).rjust(4," ") + "\t " + str(grand_total["node_tourism"]).rjust(4," ")+ "\t " + str(grand_total["node_leisure"]).rjust(4," ")+ "\t " + str(grand_total["way_highway"]).rjust(4," ")+ "\t " + str(grand_total["way_waterway"]).rjust(4," ")+ "\t " + str(grand_total["way_building"]).rjust(4," ")+ "\t " + str(grand_total["way_landuse"]).rjust(4," ")+ "\t " + str(grand_total["way_man_made"]).rjust(4," ")
		print imp
		csv.write(imp+"\n")
		csv.flush()
		csv_team.write(imp+"\n")
		csv_team.flush()
		print "-"*100
		print "\n\nEDITS MOSTLY OUTSIDE STUDY ZONE\nChangesets excluded (The Changeset BBOX indicates that they extend largely outside the study zone)"
		csv.write("\n\n\t \tEDITS MOSTLY OUTSIDE STUDY ZONE\n\t \tCHANGESETS EXCLUDED\n")
		csv.flush()
		print "-"*100
		if len(stats_excluded_user)==0 :
			print "No changesets excluded"
			return
		imp_col=  "\nStats_excluded_user\nekip \t uid\t user\t changeset\t objects \t objects_c \t objects_m \t objects_d\t node_c\t way_c\t relation_c\t node_m\t way_m\t relation_m\t node_d\t way_d\t relation_d\t poi_total_nodes\t node_amenity\t node_shop\t node_office\t node_power\t node_place\t node_man_made\t node_history\t node_tourism\t node_leisure\t way_highway\t way_waterway\t way_building\t way_landuse\t way_man_made"
		print imp_col
		csv.write("\n\n"+imp_col+"\n")
		csv.flush()
		for uid in stats_excluded_user:
			nb+=1
			# ## ??? stats_excluded_user[uid]["stat"]["changeset"]=stats_user_list[uid]["changeset_excluded"]
			imp= stats_excluded_user[uid]["ekip"].rjust(3," ") +"\t " + str(uid).rjust(10," ") +"\t " + stats_excluded_user[uid]["user"].ljust(20," ") +"\t " + str(stats_excluded_user[uid]["stat"]["changeset"]).rjust(5," ") +"\t " + str(stats_excluded_user[uid]["stat"]["objects"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_c"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_m"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_d"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_c"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_m"]).rjust(12," ") + str(stats_excluded_user[uid]["stat"]["objects_d"]).rjust(12," ") + "\t " + str(stats_excluded_user[uid]["stat"]["node_c"]).rjust(5," ") + "\t " + str(stats_excluded_user[uid]["stat"]["way_c"]).rjust(5," ") + "\t " + str(stats_excluded_user[uid]["stat"]["relation_c"]).rjust(5," ")+ "\t " + str(stats_excluded_user[uid]["stat"]["node_m"]).rjust(5," ") + ", " + str(stats_excluded_user[uid]["stat"]["way_m"]).rjust(5," ") + ", " + str(stats_excluded_user[uid]["stat"]["relation_m"]).rjust(5," ")+ ", " + str(stats_excluded_user[uid]["stat"]["node_d"]).rjust(5," ") + ", " + str(stats_excluded_user[uid]["stat"]["way_d"]).rjust(5," ") + ", " + str(stats_excluded_user[uid]["stat"]["relation_d"]).rjust(5," ") + ", " + str(stats_excluded_user[uid]["stat"]["poi_total_nodes"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_amenity"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_shop"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_office"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_power"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_place"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_man_made"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_history"]).rjust(4," ") + ", " + str(stats_excluded_user[uid]["stat"]["node_tourism"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["node_leisure"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["way_highway"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["way_waterway"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["way_building"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["way_landuse"]).rjust(4," ")+ ", " + str(stats_excluded_user[uid]["stat"]["way_man_made"]).rjust(4," ")
			print imp
			csv.write(imp+"\n")
			csv.flush()
		grand_total=self.stats_init()
		nbuser=0
		for changeset_id in stats_excluded_user:
			nbuser+=1
			for key,value in stats_excluded_user[changeset_id]["stat"].items():
				grand_total[key]+=value
		imp= " ".rjust(3," ") +"\t " +" ".rjust(10," ") +"\t " +"GRAND TOTAL".ljust(20," ") +"\t " + str(grand_total["changeset"]).rjust(5," ") +"\t " + str(grand_total["objects"]).rjust(12," ") +"\t " + str(grand_total["objects_c"]).rjust(12," ") +"\t " + str(grand_total["objects_m"]).rjust(12," ") +"\t " + str(grand_total["objects_d"]).rjust(12," ") +"\t " + str(grand_total["objects_c"]).rjust(12," ") +"\t " + str(grand_total["objects_m"]).rjust(12," ") +"\t " + str(grand_total["objects_d"]).rjust(12," ") + "\t " + str(grand_total["node_c"]).rjust(5," ") + "\t " + str(grand_total["way_c"]).rjust(5," ") + "\t " + str(grand_total["relation_c"]).rjust(5," ") + "\t " + str(grand_total["node_m"]).rjust(5," ") + "\t " + str(grand_total["way_m"]).rjust(5," ") + "\t " + str(grand_total["relation_m"]).rjust(5," ") + "\t " + str(grand_total["node_d"]).rjust(5," ") + "\t " + str(grand_total["way_d"]).rjust(5," ") + "\t " + str(grand_total["relation_d"]).rjust(5," ") + "\t " + str(grand_total["poi_total_nodes"]).rjust(4," ") + "\t " + str(grand_total["node_amenity"]).rjust(4," ") + "\t " + str(grand_total["node_shop"]).rjust(4," ") + "\t " + str(grand_total["node_office"]).rjust(4," ") + "\t " + str(grand_total["node_power"]).rjust(4," ") + ", " + str(grand_total["node_place"]).rjust(4," ") + ", " + str(grand_total["node_man_made"]).rjust(4," ") + ", " + str(grand_total["node_history"]).rjust(4," ") + ", " + str(grand_total["node_tourism"]).rjust(4," ")+ ", " + str(grand_total["node_leisure"]).rjust(4," ")+ ", " + str(grand_total["way_highway"]).rjust(4," ")+ ", " + str(grand_total["way_waterway"]).rjust(4," ")+ ", " + str(grand_total["way_building"]).rjust(4," ")+ ", " + str(grand_total["way_landuse"]).rjust(4," ")+ ", " + str(grand_total["way_man_made"]).rjust(4," ")
		print imp
		csv.write(imp+"\n")
		csv.flush()
		csv_team.write(imp+"\n")
		csv_team.flush()
		print "-"*100
		print "\n\nEDITS MOSTLY OUTSIDE STUDY ZONE\nList of Changesets excluded"
		print "\n", exclusion
		csv.write("\n\n\t \tEDITS MOSTLY OUTSIDE STUDY ZONE\n\t \tList of CHANGESETS EXCLUDED\n")
		nb=0
		csv.write(", , ,")
		for obs_e in exclusion:
			nb+=1
			if ((int(nb/10)*10)==nb) : csv.write(str(obs_e) +"\n , , ,")
			else: csv.write(str(obs_e) +",")
			csv.flush()
		csv.write("\n")
		csv.flush()
		csv.close()
		csv_team.close()
		csv_changeset.close()
		csv_dim.close()
		return None

	def API6_Contributor_Statistics(self, users,team_from,team_to,from_date,to_date,prefix,min_lon,max_lon,min_lat,max_lat) :
		global csv
		global csv_team
		global ekip
		global fi_changesets_list
		global fi_changesets_objects
		#
		try:
		  users
		except NameError:
			team_from=1
			team_to=1
			users=[None]*2
			users[1]=[""]
			print "users do not exist,  create it :", users
		if (self._debug): print "\ndebug=",debug
		print "Directory :" + self.rep
		os.chdir(self.rep)
		print "from_date=" + str(from_date)
		print "to_date=" + str(to_date)
		print "bbox : min_lon=" + str(min_lon) + ", max_lon=" + str(max_lon) + ", min_lat=" + str(min_lat) + ", max_lat=" + str(max_lat)
		#
		time_from="T00:00:00Z"
		time_to="T23:59:00Z"
		nom_changeset_list=prefix+from_date+"-"+to_date+"_changeset_list.txt"
		nom_changeset_objects=prefix+from_date+"-"+to_date+"_changeset_objects.txt"
		prefix_team=prefix+from_date+"-"+to_date+"-team.csv"
		prefix_changesets=prefix+from_date+"-"+to_date+"-changeset.csv"
		prefix_users=prefix+from_date+"-"+to_date+".csv"
		#
		print "=========================================="
		fi_changesets_list = open(nom_changeset_list, 'wb')
		fi_changesets_objects = open(nom_changeset_objects, 'wb')
		csv = open(prefix_users, 'wb')
		print "ekip, user, changeset, objects, objects_c, objects_m, objects_d, node_c,way_c,relation_c, node_m,way_m,relation_m, node_d,way_d,relation_d ,node_amenity,node_shop,node_office,node_power,node_place,node_man_made,node_history,node_tourism,node_leisure,way_highway,way_waterway,way_building,way_landuse,way_man_made"
		csv.write("ekip, user, changeset, objects, objects_c, objects_m, objects_d, node_c,way_c,relation_c, node_m,way_m,relation_m, node_d,way_d,relation_d ,node_amenity,node_shop,node_office,node_power,node_place,node_man_made,node_history,node_tourism,node_leisure,way_highway,way_waterway,way_building,way_landuse,way_man_made \n")
		csv.flush()
		csv_changeset = open(prefix_changesets, 'wb')
		csv_team = open(prefix_team, 'wb')
		csv_team.write("ekip, user, changeset, objects, objects_c, objects_m, objects_d, node_c,way_c,relation_c, node_m,way_m,relation_m, node_d,way_d,relation_d ,node_amenity,node_shop,node_office,node_power,node_place,node_man_made,node_history,node_tourism,node_leisure,way_highway,way_waterway,way_building,way_landuse,way_man_made \n")
		csv_team.flush()
		for ekip in range(team_from,team_to+1):
			stats_team= {"changeset":0, "objects":0, "objects_c":0, "objects_m":0, "objects_d":0, "node_c":0, "way_c":0, "relation_c":0,"node_m":0, "way_m":0, "relation_m":0,"node_d":0, "way_d":0, "relation_d":0, "node_amenity":0, "node_shop":0, "node_craft":0, "node_office":0, "node_power":0, "node_place":0, "node_man_made":0, "node_history":0, "node_tourism":0, "node_leisure":0, "way_highway":0, "way_waterway":0, "way_building":0, "way_landuse":0, "way_man_made":0, "flag_outside_zone":""}
			print "\n ekip " + str(ekip)
			for user in users[ekip]:
				self.summary_statistics(user,min_lon, min_lat, max_lon,
					  max_lat,from_date,to_date,csv,csv_team,csv_changeset,ekip,stats_team)
				# end of team - print in summary file by team
			print str(ekip) +", " +str(from_date[1:10])+" - " + str(to_date[1:10])+", " + str(stats_team["changeset"])+", " + str(stats_team["objects"]) + ", " + str(stats_team["objects_c"]) + ", " + str(stats_team["objects_m"]) + ", " + str(stats_team["objects_d"]) + ", " + str(stats_team["node_c"]) + ", " + str(stats_team["way_c"]) + ", " + str(stats_team["relation_c"])+ ", " + str(stats_team["node_m"]) + ", " + str(stats_team["way_m"]) + ", " + str(stats_team["relation_m"])+ ", " + str(stats_team["node_d"]) + ", " + str(stats_team["way_d"]) + ", " + str(stats_team["relation_d"])	+ ", " + str(stats_team["node_amenity"]) + ", " + str(stats_team["node_shop"]) + ", " + str(stats_team["node_office"]) + ", " + str(stats_team["node_power"]) + ", " + str(stats_team["node_place"])	+ ", " + str(stats_team["node_man_made"]) + ", " + str(stats_team["node_history"]) + ", " + str(stats_team["node_tourism"])+ ", " + str(stats_team["node_leisure"])+ ", " + str(stats_team["way_highway"])+ ", " + str(stats_team["way_waterway"])+ ", " + str(stats_team["way_building"])+ ", " + str(stats_team["way_landuse"])+ ", " + str(stats_team["way_man_made"])
			csv_team.write(str(ekip) +", " + str(from_date[1:10])+" - " + str(to_date[1:10])+", " + str(stats_team["changeset"])+", " + str(stats_team["objects"]) + ", " + str(stats_team["objects_c"]) + ", " + str(stats_team["objects_m"]) + ", " + str(stats_team["objects_d"]) + ", " + str(stats_team["node_c"]) + ", " + str(stats_team["way_c"]) + ", " + str(stats_team["relation_c"])+ ", " + str(stats_team["node_m"]) + ", " + str(stats_team["way_m"]) + ", " + str(stats_team["relation_m"])+ ", " + str(stats_team["node_d"]) + ", " + str(stats_team["way_d"]) + ", " + str(stats_team["relation_d"])  + ", " + str(stats_team["node_amenity"]) + ", " + str(stats_team["node_shop"]) + ", " + str(stats_team["node_office"]) + ", " + str(stats_team["node_power"]) + ", " + str(stats_team["node_place"])	+ ", " + str(stats_team["node_man_made"]) + ", " + str(stats_team["node_history"]) + ", " + str(stats_team["node_tourism"])+ ", " + str(stats_team["node_leisure"])+ ", " + str(stats_team["way_highway"])+ ", " + str(stats_team["way_waterway"])+ ", " + str(stats_team["way_building"])+ ", " + str(stats_team["way_landuse"])+ ", " + str(stats_team["way_man_made"])  + "\n")
			csv_team.flush()
		fi_changesets_list.close()
		fi_changesets_objects.close()
		csv.close()
		csv_team.close()
		print "Done."
		return None
