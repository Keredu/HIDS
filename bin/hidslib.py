import os
import subprocess
import pymysql
import matplotlib.pyplot as plt
plt.switch_backend('Agg')

def reset():
	os.system('rm -rf ../backups')
	os.system('rm -rf ../logs')
	os.system('rm -rf ../images')
	os.system('mysql -u root < deleteDB.sql')
	os.system('mysql -u root < iniDB.sql')

def names_paths():
	def names():
		f=open("config.txt","r")
		names=f.readlines()

		for n in names:
			i = names.index(n)
			names[i] = n.rstrip()
		f.close()
		return names

	def paths(names):
		for n in names:
			os.system("find / -name "+"'"+n+"*"+"'"+" >> paths.txt")
			os.system("find / -name "+"'"+n+"*"+"'"+" | wc -l >> wcl.txt")

		f=open("wcl.txt","r")
		arr=f.readlines()
		numbers = [0]*len(arr)
		for i in range(len(arr)):
        		numbers[i] = int(arr[i].rstrip())
		f.close()

		f = open("paths.txt","r")
		arr=f.readlines()
		paths= [[]]*len(numbers)
		z = 0
		for i in range(len(numbers)):
			paths[i] = arr[z:(z+numbers[i])]
			z+=numbers[i]
		for i in range(len(paths)):
			for j in range(len(paths[i])):
				s = paths[i][j]
				paths[i][j] = s.rstrip()
		f.close()
		os.system('rm paths.txt wcl.txt')

		return paths

	names = names();
	paths = paths(names);
	return names, paths

def hasher(path):
	s = subprocess.check_output("sha256sum "+ path, shell=True)
	return s[0:64].decode("utf-8").rstrip()

def insertDB(name, path, hash):
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	sql = "INSERT INTO Hashes (Name, Path, Hash) VALUES (%s, %s, %s)"
	val = (name, path, hash)
	cursor.execute(sql, val)
	db.commit()
	db.close()

def initialize(names, paths):
	os.system('mkdir -p ../backups')
	os.system('mkdir -p ../logs')
	os.system('mkdir -p ../images')
	os.system('touch ../logs/hids.log')
	mypaths = []
	for i in range(len(names)):
		for j in range(len(paths[i])):
			hash = hasher(paths[i][j])
			insertDB(names[i],paths[i][j],hash)
			mypaths.append(paths[i][j])
	createBackups(mypaths)

def selectHashDB(name, path):
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB" )
	cursor = db.cursor()
	cursor.execute('SELECT Hash FROM Hashes WHERE Name = "'+name+'" AND Path = "'+path+'"')
	data = cursor.fetchall()
	db.close()
	return (data[0][0])

def checkIntegrity():
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	cursor.execute('SELECT Name, Path FROM Hashes')
	tuples = cursor.fetchall()
	db.close()
	date = 1
	for t in tuples:
		hash = hasher(t[1])
		hashDB = selectHashDB(t[0],t[1])
		if (not (hash == hashDB)):
			if (date == 1):
				os.system('date >> ../logs/hids.log')
				date = 0
			updateModifiedDB(t[0],t[1])

def updateModifiedDB(name, path):
	os.system('echo "\tModification detected: '+path+'" >> ../logs/hids.log')
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	cursor.execute("UPDATE Hashes SET Modified ='X' WHERE Name='"+name+ "' AND Path='"+path+ "'")
	db.commit()
	db.close()

def kpi():
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursorName = db.cursor()
	cursorModified = db.cursor()
	cursorName.execute('SELECT COUNT(Name) FROM Hashes')
	names = cursorName.fetchall()
	cursorModified.execute('SELECT COUNT(Modified) FROM Hashes WHERE Modified = "X"')
	modifieds = cursorModified.fetchall()
	rate = 1 - modifieds[0][0]/names[0][0]
	ok = names[0][0] - modifieds[0][0]
	numFiles = names[0][0]
	return rate, ok, numFiles

def insertKPI():

	date = subprocess.check_output("date", shell=True)
	date = date.decode("utf-8").rstrip()
	date = date[8:10] + "/" + date[4:7] + "/" + date[-4:]+" | "+date[11:19]
	rate, ok, numFiles = kpi()
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	sql = "INSERT INTO KPI (Date, Rate, NumOk, NumFiles) VALUES (%s, %s, %s, %s)"
	val = (date, rate, ok, numFiles)
	cursor.execute(sql, val)
	db.commit()
	db.close()

def createBackups(paths):
	def subproc(path):
		return subprocess.check_output("dirname "+ path, shell=True).decode("utf-8").rstrip()

	os.system('mkdir -p ../backups')
	mypaths = set([subproc(p) for p in paths])
	for p in mypaths:
		os.system('mkdir -p ../backups'+p)
	for p in paths:
		os.system('cp '+p+' ../backups'+p)

def restore():
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	cursor.execute('SELECT Path FROM Hashes WHERE Modified = "X"')
	paths = cursor.fetchall()
	db.close()

	paths = [paths[i][0] for i in range(len(paths))]
	if len(paths) > 0:
		os.system('date >> ../logs/hids.log')
	for p in paths:
		os.system('cp ../backups'+p+' '+p)
		os.system('echo "\tRestore: '+p+'" >> ../logs/hids.log')

	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	cursor.execute("UPDATE Hashes SET Modified =''")
	db.commit()
	db.close()

def imageCreator():
	db = pymysql.connect("localhost","pacopepe","pacopepe","IntegrityDB")
	cursor = db.cursor()
	cursor.execute('SELECT Date,Rate FROM KPI')
	data = cursor.fetchall()
	db.close()

	LABELS = [data[i][0][0:11]+"\n"+data[i][0][14:] for i in range(len(data))]
	x = range(1,len(LABELS)+1)
	y = [data[i][1] for i in range(len(data))]
	name = subprocess.check_output("date", shell=True)
	name = name.decode("utf-8").rstrip()
	name = name[8:10] + "-" + name[4:7] + "-" + name[-4:]+"_"+name[11:19]+".png"
	plt.plot(x,y,marker='o')
	plt.xticks(x , LABELS)
	plt.ylim(0,1.07)
	plt.ylabel("KPI Rate")
	plt.savefig("../images/"+name)
